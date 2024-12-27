import socket
import threading
import hashlib
import os
import time
from threading import Thread

PACKET_SIZE = 1024 + 1024
DATA_SIZE = 1024
TIMEOUT = 1


class FileServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.file_path = "test_file\\"
        self.chunk_num = 4
        self.TIMEOUT = 0.2  # Timeout 1 giây
        self.lock = threading.Lock()
        dir_path = r"test_file"
        self.MAX_TRIES = 1000
        self.client = []    
        self.file_list = [
            f"{f} - {(os.path.getsize(os.path.join(dir_path, f)) / (1024 * 1024))} MB"
            for f in os.listdir(dir_path)
            if os.path.isfile(os.path.join(dir_path, f))
        ]
        self.dic_ack = {}
        self.dict_ping = {}
        # khởi tạo server socket
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
            self.server_socket.bind((self.host, self.port))
            self.server_socket.settimeout(self.TIMEOUT)
        except Exception as e:
            print(f"Error: {e}")

    def check_exist_file(self, file_name):
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
        # Tính checksum
        checksum = self.calculate_checksum(data).encode()
        chunk_id = chunk_id.encode()
        seq_s = str(sequence_number).encode()
        # Thêm các trường thông tin vào message --> packet
        packet = b"|".join([seq_s, checksum, chunk_id, data])
        return packet

    def send_chunk(self, file_name, file_size, chunk_id):
        # Nhận tin nhắn khởi tạo kết nối
        client_address = self.recv_ping_message()
        if client_address is not None:
            print(f"{chunk_id}Received PING_MSG from client ", client_address, "\n")
        # gửi bytes
        sequence_number = 0
        try:
            # Đọc dữ liệu chunk từ file
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
                    # biến đếm số lần gửi lại (tối đa 1000 lần)
                    cnt = 1
                    while True:
                        # đóng gói thành gói tin
                        packet = self.packaging(data, sequence_number, str(chunk_id))
                        # gửi đi
                        self.server_socket.sendto(packet, client_address)
                        # chờ nhận ack
                        try:
                            ack, address = self.server_socket.recvfrom(PACKET_SIZE)
                            ack = int(ack.decode())
                            # Nhận đúng gói ack
                            if address == client_address and ack == sequence_number:
                                sequence_number += 1
                                break
                            # Nhận ack không phải của mình lưu lại
                            self.dic_ack[address] = ack
    
                            if client_address in self.dic_ack:
                                ack = self.dic_ack.pop(client_address)
                                if ack == sequence_number:
                                    sequence_number += 1
                                    break      
                        except socket.timeout:
                            cnt = cnt + 1
                            if cnt >= self.MAX_TRIES:
                                print("ERROR send data!!\n")
                                break
                        except ConnectionResetError:
                            return
                        except KeyboardInterrupt:
                            print("\nShutting down server...")
                    start += len(data)            
        except ConnectionResetError as e:
            return
             
    def start_server(self):
        # Chờ PING_MSG từ client 
        print("Server ", self.server_socket.getsockname(), "is waiting for PING_MSG\n")
        client_address = self.recv_ping_message()
        if client_address is not None:
            # gửi danh sách file
            self.send_file_list(client_address)
            print("Files list has been sent to client\n")
            # Nhận tên file
            while True:
                file_name = self.recv_message()
                print(file_name)
                if self.check_exist_file(file_name):
                    file_name = self.file_path + file_name
                    file_size = os.path.getsize(file_name)
                    # Gửi files_size cho client
                    self.send_message(str(file_size), client_address)

                    # Gửi file
                    print("Started to send file ", file_name, "!!!")
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
                        message = f"{file_name} has been sent successfully"
                        # self.send_message(message, client_address)
                        print(message)
                    except KeyboardInterrupt:
                        print("\nShutting down server...")
                else:
                    message = "NOT"
                    self.send_message(message, client_address)
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
                response = "OK"
                self.server_socket.sendto(response.encode(), client_address)
                return client_address
            except socket.timeout:
                cnt = cnt + 1
                if cnt >= self.MAX_TRIES:
                    print("Can not receive PING_MSG from client\n")
                    break
    
    def recv_message(self):
        cnt = 1
        while True:
            try:
                packet, client_address = self.server_socket.recvfrom(PACKET_SIZE)
                checksum, message = packet.split(b"|")
                checksum = checksum.decode()
                if self.calculate_checksum(message) == checksum:
                    response = "OK"
                    self.server_socket.sendto(response.encode(), client_address)
                    return message.decode()
                response = "NOK"
                self.server_socket.sendto(response.encode(), client_address)
            except socket.timeout:
                cnt = cnt + 1
                if cnt >= self.MAX_TRIES:
                    print("Can not receive message from client\n")
                    break


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
                

if __name__ == "__main__":
    server = FileServer("192.168.1.9", 61504)
    server.start_server()
    server.server_socket.close()
