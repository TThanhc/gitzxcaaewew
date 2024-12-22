import socket
# import time
import threading
import hashlib
import os

PACKET_SIZE = 1024
MAX_PACKET_SIZE = 65507
TIMEOUT = 1


class FileServer:
    def __init__(self, host, port, file_path):
        self.host = host
        self.port = port
        self.file_path = file_path
        self.file_size = os.path.getsize(file_path)
        self.chunk_size = self.file_size // 4
        self.TIMEOUT = 1  # Timeout 1 giây
        self.lock = threading.Lock()
        dir_path = r"UDP\test_file"
        self.MAX_TRIES = 10
        self.file_list = [
            f"{f} - {(os.path.getsize(os.path.join(dir_path, f)) / (1024 * 1024))} MB"
            for f in os.listdir(dir_path)
            if os.path.isfile(os.path.join(dir_path, f))
        ]
        self.progress = 0
        self.dic_ack = {}
        # khởi tạo server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.server_socket.bind((self.host, self.port))
        self.server_socket.settimeout(self.TIMEOUT)

    def check_exist_file(self, filename):
        for f in self.file_list:
            if filename in f:
                return True
        return False

    def send_file_list(self, client_address):
        file_list_str = "List of files:\n" + "\n".join(self.file_list)
        self.send_message(file_list_str, client_address)

    def calculate_checksum(self, data):
        return hashlib.md5(data.encode()).hexdigest()
    
    def packaging(self, data, sequence_number):
        # Tính checksum
        checksum = self.calculate_checksum(data)
        # Thêm các trường thông tin vào message --> packet
        packet = f"{sequence_number}|{checksum}|{data}"
        return packet

    def send_chunk(self, file_name, chunk_id):
        # Nhận tin nhắn khởi tạo kết nối
        client_address = self.recv_message()
        # gửi bytes
        sequence_number = 0
        try:
            # Đọc dữ liệu chunk từ file
            file_size = os.path.getsize(file_name)
            start = chunk_id * (file_size // self.chunk_size)  # Bắt đầu chunk
            end = start + (file_size // self.chunk_size)      # Kết thúc chunk
            if chunk_id == self.chunk_size - 1:  # Chunk cuối có thể chứa phần dư
                end = file_size

            with open(file_name, "rb") as f:
                f.seek(start)
                while start < end:
                    data = f.read(min(PACKET_SIZE, end - start))
                    # _____
                    print(data, "\n")
                    # _____
                    if not data:
                        break
                    # biến đếm số lần gửi lại (tối đa 100 lần)
                    cnt = 1
                    while True:
                        # đóng gói thành gói tin
                        packet = self.packaging(data, sequence_number)
                        # gửi đi
                        self.server_socket.sendto(
                            packet.encode(), client_address
                        )
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
                            # chờ nếu có địa chỉ của mình trong dic_ack
                            while True:
                                try:
                                    if client_address in self.dic_ack:
                                        ack = self.dic_ack.pop(client_address)
                                        if ack == sequence_number:
                                            sequence_number += 1
                                            break
                                except socket.timeout:
                                    break
                        except socket.timeout:
                            cnt = cnt + 1
                            if cnt == self.MAX_TRIES:
                                print("ERROR send data!!\n")
                                break
                    start += len(data)
        except Exception as e:
            print(f"Error sending chunk {chunk_id}: {e}")

    def update_progress(self, sent_bytes):
        with self.lock:
            self.progress += sent_bytes
            percent = (self.progress / self.file_size) * 100
            print(f"Progress: {percent:.2f}%", end="\r")
             
    def start_server(self):
        # Chờ PING_MSG từ client 
        print("Server ", self.server_socket.getsockname(), "is waiting for PING_MSG\n")
        client_address = self.recv_message()
        # gửi danh sách file
        if client_address is not None:
            self.send_file_list(client_address)
        # chạy server
        try:
            threads = []
            for chunk_id in range(4):
                thread = threading.Thread(
                    target=self.send_chunk, args=(self.file_path, chunk_id)
                )
                if thread is not None:
                    threads.append(thread)
                    thread.start()
                    
            for thread in threads:
                if thread is not None:
                    thread.join()
        except KeyboardInterrupt:
            print("\nShutting down server...")
              
    def recv_message(self):
        cnt = 1
        while True:
            try:
                message, client_address = self.server_socket.recvfrom(PACKET_SIZE)
                response = "OK"
                self.server_socket.sendto(response.encode(), client_address)
                print("Received PING_MSG from client ", client_address, "\n")
                return client_address
            except socket.timeout:
                cnt = cnt + 1
                if cnt == self.MAX_TRIES:
                    print("Can not receive PING_MSG from client\n")
                    break

    def send_message(self, message, client_address):
        cnt = 1
        while True:
            self.server_socket.sendto(message.encode(), client_address)
            try:
                ack, _ = self.server_socket.recvfrom(PACKET_SIZE)
                if ack.decode() == "OK":
                    print("Files list has been sent to client\n")
                    break
            except socket.timeout:
                cnt = cnt + 1
                if cnt == self.MAX_TRIES:
                    print("Can send Files list to client\n")
                    break
                

if __name__ == "__main__":
    server = FileServer("127.0.0.1", 61504, r"UDP\test_file\input.txt")
    server.start_server()
    server.server_socket.close()
