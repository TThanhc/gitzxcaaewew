import socket
# import time
import threading
import hashlib
import os

PACKET_SIZE = 1024 * 1024
MAX_PACKET_SIZE =  65507
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
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as self.server_socket:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.settimeout(TIMEOUT)


    def calculate_checksum(self, data):
        return hashlib.md5(data.encode()).hexdigest()
    

    def packaging(self, data, sequence_number):
        # Tính checksum
        checksum = self.calculate_checksum(data)
        # Thêm các trường thông tin vào message --> packet
        packet = f"{sequence_number}|{checksum}|{data}"
        return packet


    def send_chunk(self, file_name, chunk_id):
        # nhận tin nhắn khởi tạo socket
        _, client_address = self.server_socket.recvfrom(1024)
        # lưu địa chỉ của socket client
        self.client.append(client_address)
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
                        self.server_socket.sendto(packet.encode(), client_address)
                        # chờ nhận ack
                        try:
                            ack, _ = self.server_socket.recvfrom(1024)
                            ack = int(ack.decode())
                            if ack == sequence_number:
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
            for chunk_id in range(4):
                threading.Thread(
                    target=self.send_chunk, args=(self.file_name, chunk_id)
                ).start()
        except KeyboardInterrupt:
            print("\nShutting down server...")


    # def start_chunk_server(self, chunk_port, chunk_id):
    #     with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
    #         server_socket.bind((self.host, chunk_port))
    #         server_socket.settimeout(TIMEOUT)
    #         print(f"Server listening on port {chunk_port} for chunk {chunk_id}...")
    #         # tin nhắn khơi tạo
    #         message, client_address = server_socket.recvfrom(1024)
    #         chunk_start = chunk_id * self.chunk_size
    #         chunk_end = (
    #             (chunk_id + 1) * self.chunk_size if chunk_id < 3 else self.file_size
    #         )
    #         self.handle_client(client_address, chunk_start, chunk_end, chunk_id)
    

    # def recv_message(self, client_address):
    #     while True:
    #         try:
    #             # Nhận tin nhắn từ client
    #             packet, address = self.server_socket.recvfrom(1024)
    #             #if client_address == address:                    packet = packet.decode()
    #             # phân tách gói tin
    #             checksum, message = packet.split('|')
    #             # tin nhắn phản hồi
    #             response = 0
    #             # kiểm tra checksum
    #             if self.calculate_checksum(message) == checksum:   
    #                 #print("Received: ", message, " from ", client_address)
    #                 response = "OK"
    #                 # Gửi gói tin phản hồi OK khi không có lỗi
    #                 self.server_socket.sendto(response.encode(), address)
    #                 break

    #             # Nếu gói tin bị lỗi gửi NOK
    #             response = "NOK"
    #             # Gửi gói tin phản hồi
    #             self.server_socket.sendto(response.encode(), address)
    #         except socket.timeout:
    #             pass
    #         return True

if __name__ == "__main__":
    server = FileServer("127.0.0.1", 8000, "input.txt")
    server.start_server()