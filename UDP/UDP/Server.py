import socket
import threading
import hashlib
import os

PACKET_SIZE = 1500
DATA_SIZE = 1400
TIMEOUT = 1
HOST = "127.0.0.1"
PORT = 61504

class FileServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.file_path = "test_file\\"
        self.chunk_num = 4
        self.TIMEOUT = 0.2
        self.lock = threading.Lock()
        dir_path = r"test_file"
        self.MAX_TRIES = 100
        self.client = []    
        self.file_list = [
            f"{f} - {(os.path.getsize(os.path.join(dir_path, f)) / (1024 * 1024))} MB"
            for f in os.listdir(dir_path)
            if os.path.isfile(os.path.join(dir_path, f))
        ]
        self.dic_ack = {}
        self.dict_ping = {}
        # initialize server socket
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
            self.server_socket.bind((self.host, self.port))
            self.server_socket.settimeout(self.TIMEOUT)
        except Exception as e:
            print(f"Error: {e}")

    def check_exist_file(self, file_name):
        if '.' not in file_name:
            return False
        for f in self.file_list:
            if file_name in f:
                return True
        return False 

    def send_file_list(self, client_address):
        file_list_str = "List of files:\n" + "\n".join(self.file_list)
        self.send_message(file_list_str, client_address)

    def calculate_checksum(self, data):
        return hashlib.sha256(data).hexdigest()
    
    def packaging(self, data, sequence_number, chunk_id):
        # cacualte checksum
        checksum = self.calculate_checksum(data).encode()
        chunk_id = chunk_id.encode()
        seq_s = str(sequence_number).encode()
        # packaging message --> packet
        packet = b"|".join([seq_s, checksum, chunk_id, data])
        return packet

    def send_chunk(self, file_name, file_size, chunk_id):
        # receive PING_MSG
        client_address = self.recv_ping_message()
        if client_address is None:
            # print(f"\n\033[1;32;40m[NOTIFICATION] Server has received PING_MSG from client with address: {str(client_address)}\n\033[0m")
            return
        # send bytes
        sequence_number = 0
        try:
            # read chunk file
            start = chunk_id * (file_size // int(self.chunk_num)) # Bắt đầu chunk
            end = start + (file_size // int(self.chunk_num))      # Kết thúc chunk
            if chunk_id == self.chunk_num - 1:   # Chunk cuối có thể chứa phần dư
                end = file_size
            
            with open(file_name, "rb") as f:
                f.seek(start)
                while start < end:
                    data = f.read(min(DATA_SIZE, end - start))
                    
                    if not data:
                        break
                    # cnt = 1
                    while True:
                        # packaging
                        packet = self.packaging(data, sequence_number, str(chunk_id))
                        if packet == None or client_address == None:
                            return
                        try:
                            # send packet
                            self.server_socket.sendto(packet, client_address)
                            # wait for ack
                            ack, address = self.server_socket.recvfrom(PACKET_SIZE)
                            ack = ack.decode()
                            if ack.isdigit():
                                ack = int(ack)
                                # receive suitable ack
                                if address == client_address and ack == sequence_number:
                                    sequence_number += 1
                                    break
                                # not receive suitable ack store into dict_ack
                                self.dic_ack[address] = ack
        
                                if client_address in self.dic_ack:
                                    ack = self.dic_ack.pop(client_address)
                                    if ack == sequence_number:
                                        sequence_number += 1
                                        break      
                        except socket.timeout:
                            # cnt = cnt + 1
                            # if cnt >= self.MAX_TRIES:
                            #     break
                            continue
                        except ConnectionResetError:
                            return
                        except KeyboardInterrupt:
                            return
                    start += len(data)
        except KeyboardInterrupt:
            return

    def start_server(self):
        # receive PING_MSG from client
        print("Server ", self.server_socket.getsockname(), "is waiting for PING_MSG\n")
        try:
            client_address = self.recv_ping_message()
            if client_address is not None:
                print(f"\n\033[1;32;40m[NOTIFICATION] Server has received PING_MSG from client with address: {str(client_address)}\n\033[0m")
        except KeyboardInterrupt:
            return
        
        if client_address is not None:
            # send file_list
            self.send_file_list(client_address)
            print("Files list has been sent to client\n")
            # receive file need to be downloaded
            while True:
                try:
                    client_msg, address = self.recv_message()
                    # receive msg
                    if "GET" in client_msg:
                        file_name = client_msg[4:]
                    # client disconnect
                    if client_msg == "EXIT":
                        print(f"\n\033[1;32;40m[NOTIFICATION] Client {str(address)} disconnected.\n\033[0m")
                        break
                    # print msg
                    print("\033[1;31;40m" + "[FROM] " + str(address) + ": " + client_msg + "\033[0m")
                
                    if self.check_exist_file(file_name):
                        filename = file_name
                        file_name = self.file_path + file_name
                        file_size = os.path.getsize(file_name)
                        # send files_size to client
                        self.send_message(str(file_size), client_address)

                        # send file
                        print("Start downloading ", filename, "!")
                        try:
                            threads = []
                            for chunk_id in range(self.chunk_num):
                                thread = threading.Thread(
                                    target=self.send_chunk, args=(file_name, file_size, chunk_id)
                                )
                                if thread is not None:
                                    threads.append(thread)
                                    thread.start()
                                    
                            for thread in threads:
                                if thread is not None:
                                    thread.join()

                            # Gửi xong file
                            message = f"Download {filename} successfully"
                            print(message)
                        except KeyboardInterrupt:
                            return
                    else:
                        msg = f"File {file_name} is not exist!"
                        print(f"[TO] {str(address)}: {msg}")
                        message = "NOT"
                        self.send_message(message, client_address)
                except KeyboardInterrupt:
                    return
                except ConnectionResetError:
                    continue
        else:
            print("Client address is none\n")
              
    def recv_ping_message(self):
        cnt = 1
        while True:
            try:
                message, client_address = self.server_socket.recvfrom(PACKET_SIZE)
                if client_address in self.client:
                    continue
                self.client.append(client_address)
                message = message.decode()
                if message == "23120088":
                    response = "OK"
                    self.server_socket.sendto(response.encode(), client_address)
                    return client_address
                else:
                    response = "NOK"
                    self.server_socket.sendto(response.encode(), client_address)
            except socket.timeout:
                continue
            except ConnectionResetError:
                continue
            except KeyboardInterrupt:
                return None
    def recv_message(self):
        cnt = 1
        while True:
            try:
                packet, client_address = self.server_socket.recvfrom(PACKET_SIZE)
                if packet.count(b"|") >= 1:
                    checksum, message = packet.split(b"|")
                    checksum = checksum.decode()
                    if self.calculate_checksum(message) == checksum:
                        response = "OK"
                        self.server_socket.sendto(response.encode(), client_address)
                        return message.decode(), client_address
                    response = "NOK"
                    self.server_socket.sendto(response.encode(), client_address)
            except socket.timeout:
                # cnt = cnt + 1
                # if cnt >= self.MAX_TRIES:
                #     print("Can not receive message from client\n")
                #     return None
                continue
            except KeyboardInterrupt:
                print("\nShutting down server...")
                return None


    def send_message(self, message, client_address):
        cnt = 1
        message = message.encode()
        checksum = self.calculate_checksum(message).encode()
        packet = b"|".join([checksum, message]) 
        while True:
            self.server_socket.sendto(packet, client_address)
            try:
                ack, _ = self.server_socket.recvfrom(PACKET_SIZE)
                if ack.decode() == "OK":
                    break
            except socket.timeout:
                cnt = cnt + 1
                if cnt >= self.MAX_TRIES:
                    print("Can't send message to client\n")
                    break
            except KeyboardInterrupt:
                print("\nShutting down server...")
                return 
                
if __name__ == "__main__":
    server = FileServer(HOST, PORT)
    server.start_server()
    server.server_socket.close()
    print("\n\033[1;32;40m[NOTIFICATION] Exited the server!\n\033[0m")