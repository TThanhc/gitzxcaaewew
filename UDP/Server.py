import socket
# import time
import threading
import hashlib
import os

PACKET_SIZE = 1024 * 1024
MAX_PACKET_SIZE = 65507
server_address = ('127.0.0.1', 61504)
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
        self.progress = 0
        self.client = []
        self.dic_ack = {}
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as self.server_socket:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.settimeout(self.TIMEOUT)

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
                    if not data:
                        break
                    
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
                            if address == client_address:
                                if ack == sequence_number:
                                    break
                            else:
                                # Nhận ack không phải của mình lưu lại
                                self.dic_ack[address] = ack
                                # Nếu có địa chỉ của mình trong từ điển ack
                                if client_address in self.dic_ack:
                                    data = self.dic_ack.pop(client_address)
                                    if data == sequence_number:
                                        break
                        except socket.timeout:
                            continue
                    start += len(data)
        except Exception as e:
            print(f"Error sending chunk {chunk_id}: {e}")

    def update_progress(self, sent_bytes):
        with self.lock:
            self.progress += sent_bytes
            percent = (self.progress / self.file_size) * 100
            print(f"Progress: {percent:.2f}%", end="\r")
             
    def start_server(self):
        try:
            threads = []
            for chunk_id in range(4):
                thread = threading.Thread(
                    target=self.send_chunk, args=(self.file_pathpath, chunk_id)
                ).start()
                threads.append(thread)
                thread.join()
        except KeyboardInterrupt:
            print("\nShutting down server...")
              
    def recv_message(self):
        while True:
            try:
                message, client_address = self.server_socket.recvfrom(PACKET_SIZE)
                response = "OK"
                self.server_socket.sendto(response.encode(), client_address)
                return client_address
            except Exception as e:
                print(f"Error receiving message: {e}")
                

if __name__ == "__main__":
    server = FileServer("127.0.0.1", 61504, "input.txt")
    server.start_server()