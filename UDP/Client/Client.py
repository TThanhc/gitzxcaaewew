from queue import Queue
import socket
import hashlib
#import os
from threading import Thread
import threading
import time

PACKET_SIZE = 1024 + 1024
# Cấu hình UDP socket
server_address = ('127.0.0.1', 61504)


class FileClient:
    def __init__(self):
        self.chunks_data = [None] * 4
        self.TIMEOUT = 0.2  # Timeout 1 giây
        self.lock = threading.Lock()
        self.progress = [0, 0, 0, 0]
        self.port = [61862, 61863, 61864, 61865]
        self.file_size = 0 
        self.file_name = 0
        self.output_file = "UDP\\receive-file\\"
        self.chunks = []
        self.num_chunk = 4
        self.MAX_TRIES = 1000
        self.chunk_size = 0
        self.need_file = Queue()
        self.list_file = ""

        Thread(target = self.read_input_file).start()
        # Thread(target = self.rcv_msg).start()

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
                    print(file)
                    self.need_file.put(file)

                    # if file == "": continue
                    # if file in self.list_file:  
                    #     self.need_file.put(file)
                f.close()
                time.sleep(1)
        except Exception as e:
            print(f"Error in send_request: {e}")
    
    def get_file_name(self):
        if not self.need_file.empty():
            return self.need_file.get()
        else: 
            return None
            
    def calculate_checksum(self, data):
        return hashlib.md5(data).hexdigest()

    def recv_chunk(self, chunk_id):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_sock:
                # client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65535)  # Tăng bộ đệm nhận lên 64KB
                client_sock.settimeout(self.TIMEOUT)
                # tin nhắn khởi tạo socket
                self.send_ping_message(client_sock, "23120088")
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
        self.file_name = self.output_file + self.file_name
        with open(self.file_name, "wb") as f:
            for chunk in self.chunks_data:
                if chunk is not None:
                    f.write(chunk)
                else:
                    print("Error write bytes\n")
                    return
        print(f"\nFile saved to {self.file_name}")

    def start_client(self):
        # tin nhắn khởi tạo
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
                client_socket.settimeout(self.TIMEOUT)
                # tin nhắn khởi tạo socket
                self.send_ping_message(client_socket, "23120088")
                # nhận danh sách file
                self.list_file = self.recv_message(client_socket)
                print(self.list_file)
                while True:
                    try:
                        # gửi file cần tải
                        self.file_name = self.get_file_name()
                        if self.file_name != None:
                            self.send_message(client_socket, self.file_name)
                            # Nhận file_size hay NOT
                            response = self.recv_message(client_socket)
                            if response != "NOT":
                                self.file_size = int(response)
                                self.chunk_size = self.file_size // self.num_chunk

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
                            else:
                                print(self.file_name, "does not exist in file list server!!\n")
                    except KeyboardInterrupt:
                        print("\nShutting down Client...")
                        break
        except Exception as e:
            print(f"Error: {e}")
        
    def send_ping_message(self, client_socket : socket, message):
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
                if cnt == self.MAX_TRIES:
                    print("Can not send PING_MSG to server\n")
                    break

    def send_message(self, client_socket : socket, message):
        cnt = 1
        message = message.encode()
        checksum = self.calculate_checksum(message).encode()
        packet = b"|".join([checksum, message]) 
        while True:
            client_socket.sendto(packet, server_address)
            try:
                ack, _ = client_socket.recvfrom(PACKET_SIZE)
                if ack.decode() == "OK":
                    break
            except socket.timeout:
                cnt = cnt + 1
                if cnt == self.MAX_TRIES:
                    print("Can't send message to server\n")
                    break
    
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
                cnt = cnt + 1
                if cnt == self.MAX_TRIES:
                    print("Can not receive message from server\n")
                    break
        

if __name__ == "__main__":
    client = FileClient()
    client.start_client()
 