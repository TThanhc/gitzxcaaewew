import socket
import hashlib
import os
import threading
import time

PACKET_SIZE = 1024 * 1024
MAX_PACKET_SIZE =  65507
# Cấu hình UDP socket
server_address = ('127.0.0.1', 61504)


class FileClient:
    def __init__(self, output_file):
        self.output_file = output_file
        self.chunks_data = [None] * 4
        self.lock = threading.Lock()
        self.progress = 0


    def calculate_checksum(data):
        return hashlib.md5(data.encode()).hexdigest()


    def recv_chunk(self, chunk_id):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
                # tin nhắn khởi tạo socket
                ping_msg = "init"
                client_socket.sendto(ping_msg.encode(), server_address)
                print(f"Socket for received chunk {chunk_id}...")
                # tải chunk
                ack = 0
                received_bytes = 0
                while True:
                    try:
                        packet = client_socket.recvfrom(PACKET_SIZE)
                        seq_s, checksum, data = packet.split('|')
                        # tin nhắn phản hồi
                        if self.calculate_checksum(data) == checksum and seq_s == ack:
                            received_bytes += len(data)
                            client_socket.sendto(f"{seq_s}".encode(), server_address)
                            self.chunks_data[chunk_id] += data
                            ack += 1
                        else:
                            client_socket.sendto(f"{ack - 1}".encode(), server_address)
                    except:
                        pass
        except Exception as e:
            print(f"Error downloading chunk {chunk_id}: {e}")


    def update_progress(chunks_progress, file_name):
        # In 4 dòng cố định ban đầu
        for i in range(len(chunks_progress)):
            print(f"Downloading File", file_name, " part {i + 1} ....  0%")

        while any(progress < 100 for progress in chunks_progress):
            for i, progress in enumerate(chunks_progress):
                # Di chuyển con trỏ về đầu dòng và cập nhật phần trăm
                print(f"\033[{i + 1}FDownloading File5.zip part {i + 1} ....  {progress}%", end='\r')
            time.sleep(0.1)


    def merge_chunks(self):
        with open(self.output_file, "wb") as f:
            for chunk in self.chunks_data:
                f.write(chunk)
        print(f"\nFile saved to {self.output_file}")

    def start_client(self):
        threads = []
        for chunk_id in range(4):
            thread = threading.Thread(target=self.recv_chunk, args=(chunk_id))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.merge_chunks()

if __name__ == "__main__":
    client = FileClient("received_file.txt")
    client.start_client()


def send_message(client_sock : socket, message):
    client_sock.settimeout(1)
    ok = False
    while True:
        # Tính checksum
        checksum = calculate_checksum(message)
        # Thêm các trường thông tin vào message --> packet
        packet = f"{checksum}|{message}"
        client_sock.sendto(packet.encode(), server_address)
        try:
            # Nhận gói tin phản hồi
            response, _ = client_sock.recvfrom(1024)
            response = response.decode()
            # Dừng khi nhận đc OK
            if response == "OK":
                break
        except socket.timeout:
            pass


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