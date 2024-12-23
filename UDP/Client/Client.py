from queue import Queue
import socket
import hashlib
#import os
from threading import Thread
import threading
import time
import struct

PACKET_SIZE = 1024 + 1024
MAX_PACKET_SIZE = 65507
# Cấu hình UDP socket
server_address = ('127.0.0.1', 61504)


class FileClient:
    def __init__(self, filename, file_size):
        self.chunks_data = [None] * 4
        self.TIMEOUT = 1  # Timeout 1 giây
        self.lock = threading.Lock()
        self.progress = [0, 0, 0, 0]
        self.file_size = file_size
        self.filename = filename
        self.output_file = "UDP\\receive-file\\" + filename
        self.chunks = []
        self.num_chunk = 4
        self.MAX_TRIES = 1000
        self.chunk_size = self.file_size // self.num_chunk
        self.need_file = Queue()
        self.list_file = ""

        # Thread(target = self.read_input_file).start()
        # # Thread(target = self.rcv_msg).start()
        # Thread(target = self.send_request).start()
        
    def read_input_file(self):
        file_input = "UDP\Client\input.txt"
        start = 0

        try:
            while True:
                with open(file_input, "r") as f:
                    f.seek(start)
                    new_files = [line.strip() for line in f.readlines()]
                    start = f.tell()
                
                for file in new_files:
                    if file == "": continue
                    if file in self.list_file:  
                        self.need_file.put(file)
                        
                f.close()
                time.sleep(5)
        except Exception as e:
            print(f"Error in send_request: {e}")
    
    def send_request(self):
        try:
            while True:
                if not self.need_file.empty():
                    filename = self.need_file.get()
                    msg = "send " + filename
                    print(msg)
                    self.socket.send(msg.encode())
                    
                    server_response = self.socket.recv(1024).decode()
                    print("\033[1;31;40m" + "Server: " + server_response + "\033[0m")

                    if "not exist" not in server_response:
                        self.rcv_file(filename)
        except Exception as e:
            print(f"Error: {e}")
            
    def calculate_checksum(self, data):
        return hashlib.md5(data).hexdigest()

    def recv_chunk(self, chunk_id):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_sock:
                client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65535)  # Tăng bộ đệm nhận lên 64KB
                client_sock.settimeout(self.TIMEOUT)
                # tin nhắn khởi tạo socket
                self.send_message(client_sock, "23120088")
                # tải chunk
                ack = 0
                received_bytes = 0
                chunk_data = b""
                # biến đếm số lần gửi lại (tối đa 1000 lần)
                cnt = 1
                while True:
                    try:
                        # nhận gói tin
                        packet, _ = client_sock.recvfrom(PACKET_SIZE)
                        if packet.count(b"|") >= 2:
                            seq_s, checksum, data = packet.split(b'|', maxsplit=2)
                            seq_s = seq_s.decode()
                            checksum = checksum.decode()
                            # tin nhắn phản hồi
                            if self.calculate_checksum(data) == checksum:
                                if int(seq_s) == ack:
                                    received_bytes += len(data)
                                    # gửi ack lại
                                    response = f"{seq_s}"
                                    client_sock.sendto(response.encode(), server_address)
                                    # thêm các byte vào mảng lưu
                                    chunk_data += data
                                    # Dừng khi nhận đủ chunk
                                    if received_bytes >= self.chunk_size:
                                        break
                                    ack += 1
                                    continue
                        # gửi lại ack trc đó
                        response = f"{ack - 1}"
                        client_sock.sendto(response.encode(), server_address)
                    except socket.timeout:
                        cnt = cnt + 1
                        if cnt == self.MAX_TRIES:
                            print("Error receive data\n")
                            break

                self.chunks_data[chunk_id] = chunk_data
        except Exception as e:
            print(f"Error downloading chunk {chunk_id}: {e}")

    def merge_chunks(self):
        with open(self.output_file, "wb") as f:
            for chunk in self.chunks_data:
                if chunk is not None:
                    f.write(chunk)
                else:
                    print("Error write bytes\n")
                    return
        print(f"\nFile saved to {self.output_file}")

    def start_client(self):
        # tin nhắn khởi tạo
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
                client_socket.settimeout(self.TIMEOUT)
                # tin nhắn khởi tạo socket
                self.send_message(client_socket, "23120088")
                # nhận danh sách file
                self.recv_message(client_socket)
                
                # chạy client
                threads = []
                for chunk_id in range(self.num_chunk):
                    thread = threading.Thread(target=self.recv_chunk, args=(chunk_id,))
                    if thread is not None:
                        threads.append(thread)
                        thread.start()

                for thread in threads:
                    if thread is not None:
                        thread.join()

                self.merge_chunks()
        except Exception as e:
            print(f"Error: {e}")
        
    def send_message(self, client_socket : socket, message):
        cnt = 1
        while True:
            client_socket.sendto(message.encode(), server_address)
            try:
                ack, _ = client_socket.recvfrom(PACKET_SIZE)
                if ack.decode() == "OK":
                    # print(f"Socket for received chunk {chunk_id}...")
                    break
            except socket.timeout:
                cnt = cnt + 1
                if cnt == 100:
                    print("Can not send PING_MSG to server\n")
                    break
    
    def recv_message(self, client_socket : socket):
        cnt = 1
        while True:
            try:
                message, _ = client_socket.recvfrom(PACKET_SIZE)
                response = "OK"
                client_socket.sendto(response.encode(), server_address)
                self.list_file = message.decode()
                print(self.list_file)
                break
            except socket.timeout:
                cnt = cnt + 1
                if cnt == self.MAX_TRIES:
                    print("Can not receive list file from server\n")
                    break
        

if __name__ == "__main__":
    client = FileClient("received_file_2.txt", 10302528)
    client.start_client()
 

# def display_progress(file_size):
#     global progress
#     while True:
#         with progress_lock:
#             total_received = sum(progress)
#         percent = (total_received / file_size) * 100
#         print(f"\rDownload Progress: {percent:.2f}%", end="")

#         if total_received >= file_size:
#             print("\nDownload complete.")
#             break
#         time.sleep(0.5)