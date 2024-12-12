import socket
import struct
import time
import sys
import threading


CHUNK_SIZE = 1024
TIMEOUT = 1  # 1 second

def update_progress(chunks_progress):
    """
    Hiển thị tiến độ tải dữ liệu của 4 chunk trên 4 dòng cố định.
    """
    # In 4 dòng cố định ban đầu
    for i in range(len(chunks_progress)):
        print(f"Downloading File5.zip part {i + 1} ....  0%")

    while any(progress < 100 for progress in chunks_progress):
        for i, progress in enumerate(chunks_progress):
            # Di chuyển con trỏ về đầu dòng và cập nhật phần trăm
            print(f"\033[{i + 1}FDownloading File5.zip part {i + 1} ....  {progress}%", end='\r')
        time.sleep(0.1)

def simulate_chunk_download(chunk_id, chunks_progress):
    """
    Giả lập tải một chunk và cập nhật tiến độ vào danh sách chung.
    """
    for percentage in range(0, 101, 10):  # Tăng từ 0% đến 100%
        chunks_progress[chunk_id] = percentage
        time.sleep(0.5)  # Giả lập thời gian tải

def calculate_checksum(data):
    return sum(data) % 65536

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(('0.0.0.0', 12345))
    print("Server is running...")

    # File để gửi
    file_name = "large_file.zip"
    with open(file_name, 'rb') as f:
        file_data = f.read()

    client_addr = None
    sequence_number = 0

    while sequence_number * CHUNK_SIZE < len(file_data):
        # Lấy chunk dữ liệu
        chunk = file_data[sequence_number * CHUNK_SIZE:(sequence_number + 1) * CHUNK_SIZE]
        checksum = calculate_checksum(chunk)

        # Đóng gói dữ liệu
        packet = struct.pack('!I I', sequence_number, checksum) + chunk
        server.sendto(packet, client_addr)

        # Chờ ACK
        try:
            server.settimeout(TIMEOUT)
            ack_data, addr = server.recvfrom(1024)
            ack_sequence = struct.unpack('!I', ack_data)[0]

            if ack_sequence == sequence_number:
                print(f"Received ACK for sequence {sequence_number}")
                sequence_number += 1
        except socket.timeout:
            print(f"Timeout for sequence {sequence_number}, resending...")

if __name__ == "__main__":
    start_server()
