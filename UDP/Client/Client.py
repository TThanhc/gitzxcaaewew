from queue import Queue
import socket
import hashlib
from threading import Thread
import threading
import time
import sys
import os

PACKET_SIZE = 1024 + 1024
HOST = input("Enter server's IP: ")
PORT = input("Enter server's PORT: ")
server_address = (HOST, int(PORT))


class FileClient:
    def __init__(self):
        self.num_chunk = 4
        self.chunks_data = [None] * self.num_chunk
        self.TIMEOUT = 0.2
        self.lock = threading.Lock()
        self.chunk_progress = [0.0] * self.num_chunk
        self.done_chunk = [False] * self.num_chunk
        self.file_size = 0 
        self.file_name = 0
        self.file_input = input("Enter input_file's path: ")
        self.output_path = input("Enter folder path to save your file: ")
        self.chunks = []
        self.MAX_TRIES = 100
        self.chunk_size = 0
        self.need_file = Queue()
        self.list_file = ""

        Thread(target = self.read_input_file, daemon=True).start()

    def stop(self):
        print("\n\033[1;32;40m[NOTIFICATION] Disconnected!\n\033[0m")
        os._exit(0)

    def read_input_file(self):
        start = 0

        try:
            while True:
                try:
                    with open(self.file_input, "r") as f:
                        f.seek(start)
                        new_files = [line.strip() for line in f.readlines()]
                        start = f.tell()
                    
                    for file in new_files:
                        if file == "": continue
                        if file in new_files:  
                            self.need_file.put(file)
                    f.close()
                    time.sleep(5)
                except KeyboardInterrupt:
                    return
        except Exception as e:
            print(f"Error in send_request: {e}")

    def display_progress(self):
        try:
            msg = f"Server: Start downloading {self.file_name} !"
            print("\033[1;31;40m" + msg + "\033[0m")
            while any(done == False for done in self.done_chunk):
                progress_msg = "\n".join([f"Downloading {self.file_name} part {chunk_id + 1}: {self.chunk_progress[chunk_id]:.2f}%" for chunk_id in range(self.num_chunk)])
                print("\033[1;37;40m" + progress_msg + "\033[0m")
                sys.stdout.flush()
                # move cursor up
                sys.stdout.write(f"\033[{self.num_chunk}A\033[0G\033[J")

            progress_msg = "\n".join([f"Downloading {self.file_name} part {chunk_id + 1} successfully" for chunk_id in range(self.num_chunk)])
            print("\033[1;37;40m" + progress_msg + "\033[0m") 
            msg = f"Server: Downloading {self.file_name} successfully" 
            print("\033[1;31;40m" + msg + "\033[0m")      
        except Exception as e:
            print("ERROR display progress: ", {e})

    def get_file_name(self):
        if not self.need_file.empty():
            return self.need_file.get()
        else: 
            return None
            
    def calculate_checksum(self, data):
        return hashlib.sha256(data).hexdigest()

    def recv_chunk(self, chunk_id):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_sock:
                client_sock.settimeout(self.TIMEOUT)
                # send PING_MSG
                PING_MSG = "23120088"
                self.send_ping_message(client_sock, PING_MSG)
                # chunksize
                start = chunk_id * self.chunk_size
                if chunk_id == self.num_chunk - 1:   # Chunk cuối có thể chứa phần dư
                    end = self.file_size
                else:
                    end = start + self.chunk_size 
                # receive chunk
                ack = 0
                total_chunk = end - start
                received_bytes = 0
                chunk_data = b""
                fl = True
                while True:
                    try:
                        # receive packet
                        packet, _ = client_sock.recvfrom(PACKET_SIZE)
                        if packet.count(b"|") >= 3:
                            seq_s, checksum, id, data = packet.split(b"|", maxsplit=3)
                            seq_s = seq_s.decode()
                            checksum = checksum.decode()
                            id = int(id.decode())
                            if fl:
                                if chunk_id != id:
                                    chunk_id = id
                                    start = chunk_id * self.chunk_size
                                    if chunk_id == self.num_chunk - 1:
                                        end = self.file_size
                                    else:
                                        end = start + self.chunk_size  
                                    total_chunk = end - start
                                fl = False
                            # response msg
                            if self.calculate_checksum(data) == checksum:
                                if int(seq_s) == ack:
                                    received_bytes += len(data)
                                    # update progress
                                    with self.lock:
                                        self.chunk_progress[chunk_id] = (received_bytes / total_chunk) * 100
                                    # send ack back
                                    response = f"{seq_s}"
                                    client_sock.sendto(response.encode(), server_address)
                                    # store bytes
                                    chunk_data += data
                                    # stop when receive full chunk
                                    if received_bytes >= total_chunk:
                                        break
                                    ack += 1
                                    continue
                        # send last ack received
                        response = f"{ack - 1}"
                        client_sock.sendto(response.encode(), server_address)
                    except KeyboardInterrupt:
                        break
                    except socket.timeout:
                        continue
                self.done_chunk[chunk_id] = True
                self.chunks_data[chunk_id] = chunk_data
        except KeyboardInterrupt:
            return
        except Exception as e:
            print(f"Error downloading chunk {chunk_id}: {e}")

    def merge_chunks(self):
        self.file_name = self.output_path + '\\' + self.file_name
        with open(self.file_name, "wb") as f:
            for chunk in self.chunks_data:
                if chunk is not None:
                    f.write(chunk)
                else:
                    print("Error write bytes\n")
                    return
        print(f"\nFile saved to {self.file_name}")

    def start_client(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
                client_socket.settimeout(self.TIMEOUT)
                # PING_MSG
                try:
                    self.send_ping_message(client_socket, "23120088")
                    # nhận danh sách file
                    self.list_file = self.recv_message(client_socket)
                    if self.list_file is not None:
                        print("\033[1;31;40m" + "Server: " + self.list_file + "\n\033[0m")
                    
                    while True:
                        try:
                            # send file_name
                            self.file_name = self.get_file_name()
                            if self.file_name is not None:
                                msg = f"GET {self.file_name}"
                                print(f"Client: {msg}")
                                self.send_message(client_socket, msg)
                                # receive response (exist: file_size, not exist: NOT)
                                response = self.recv_message(client_socket)
                                if response != "NOT":
                                    self.file_size = int(response)
                                    self.chunk_size = self.file_size // int(self.num_chunk)                               
                                    # threading
                                    threads = []
                                    
                                    for chunk_id in range(self.num_chunk):
                                        thread = threading.Thread(target=self.recv_chunk, args=(chunk_id,))
                                        if thread is not None:
                                            threads.append(thread)
                                            thread.start()
                                    
                                    self.display_progress()

                                    for thread in threads:
                                        thread.join()
                                            
                                    self.merge_chunks()
                                    self.chunks_data = [None] * self.num_chunk
                                    self.chunk_progress = [0.0] * self.num_chunk
                                    self.done_chunk = [False] * self.num_chunk
                                else:
                                    server_msg = f"File {self.file_name} is not exist!"
                                    print("\033[1;31;40m" + "Server: " + server_msg + "\033[0m")
                        except KeyboardInterrupt:
                            # FIN = "EXIT"
                            # self.send_message(client_socket, FIN)
                            break
                        except ConnectionResetError:
                            print(f"Server disconnected.")
                            break
                except KeyboardInterrupt:
                    return
        except ConnectionResetError:
            print(f"Server {server_address} is not alive.")
        
    def send_ping_message(self, client_socket : socket, message):
        while True:
            try:
                client_socket.sendto(message.encode(), server_address)
                ack, _ = client_socket.recvfrom(PACKET_SIZE)
                if ack.decode() == "OK":
                    return
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                return

    def send_message(self, client_socket : socket, message):
        message = message.encode()
        checksum = self.calculate_checksum(message).encode()
        packet = b"|".join([checksum, message]) 
        while True:
            try:
                client_socket.sendto(packet, server_address)
                ack, _ = client_socket.recvfrom(PACKET_SIZE)
                if ack.decode() == "OK":
                    return
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                return
    
    def recv_message(self, client_socket : socket):
        cnt = 1
        while True:
            try:
                packet, _ = client_socket.recvfrom(PACKET_SIZE)
                checksum, message = packet.split(b"|")
                checksum = checksum.decode()
                if self.calculate_checksum(message) == checksum:
                    response = "OK"
                    client_socket.sendto(response.encode(), server_address)
                    return message.decode()
                response = "NOK"
                client_socket.sendto(response.encode(), server_address)
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                return None

if __name__ == "__main__":
    client = FileClient()
    client.start_client()
    client.stop()
    sys.exit(0)