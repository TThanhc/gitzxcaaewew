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



import socket
import os
import time

# Configurations
HOST = '127.0.0.1'
PORT = 12345
CHUNK_SIZE = 1024  # 1 KB
TIMEOUT = 2  # seconds
FILE_LIST = {
    "File1.zip": "test_files/File1.zip",
    "File2.zip": "test_files/File2.zip"
}

def send_file(server_socket, client_addr, file_name):
    try:
        file_path = FILE_LIST[file_name]
        file_size = os.path.getsize(file_path)

        # Gửi thông tin file tới client
        server_socket.sendto(f"{file_name} {file_size}".encode(), client_addr)
        print(f"Sending file '{file_name}' ({file_size} bytes) to {client_addr}")

        # Đọc file và gửi từng chunk
        seq_num = 0
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break

                # Gói tin gồm sequence number và dữ liệu
                packet = f"{seq_num:08d}".encode() + chunk
                while True:
                    server_socket.sendto(packet, client_addr)

                    # Chờ ACK từ client
                    try:
                        server_socket.settimeout(TIMEOUT)
                        ack, _ = server_socket.recvfrom(1024)
                        ack_seq = int(ack.decode())
                        if ack_seq == seq_num:
                            print(f"ACK received for seq {seq_num}")
                            break
                    except socket.timeout:
                        print(f"Resending packet {seq_num}")

                seq_num += 1

        # Gửi gói tin kết thúc
        server_socket.sendto(b"END", client_addr)
        print("File transfer complete.")
    except Exception as e:
        print(f"Error: {e}")

def main():
    # Tạo UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, PORT))
    print(f"Server listening on {HOST}:{PORT}")

    while True:
        print("Waiting for client...")
        data, client_addr = server_socket.recvfrom(1024)
        file_name = data.decode()

        if file_name in FILE_LIST:
            send_file(server_socket, client_addr, file_name)
        else:
            server_socket.sendto(b"ERROR: File not found", client_addr)

if __name__ == "__main__":
    main()
