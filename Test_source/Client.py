import socket
import struct
import os

CHUNK_SIZE = 1024

def calculate_checksum(data):
    return sum(data) % 65536

def start_client():
    server_ip = '127.0.0.1'
    server_port = 12345
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # File lưu kết quả
    output_file = "downloaded_file.zip"
    with open(output_file, 'wb') as f:
        pass

    expected_sequence = 0

    while True:
        # Nhận gói tin
        data, addr = client.recvfrom(2048)
        sequence_number, checksum = struct.unpack('!I I', data[:8])
        chunk = data[8:]

        # Kiểm tra checksum
        if calculate_checksum(chunk) != checksum:
            print(f"Checksum mismatch for sequence {sequence_number}, discarding...")
            continue

        # Kiểm tra thứ tự gói tin
        if sequence_number != expected_sequence:
            print(f"Out-of-order packet: expected {expected_sequence}, got {sequence_number}")
            continue

        # Lưu chunk vào file
        with open(output_file, 'ab') as f:
            f.write(chunk)

        # Gửi ACK
        ack_packet = struct.pack('!I', sequence_number)
        client.sendto(ack_packet, addr)
        print(f"Sent ACK for sequence {sequence_number}")

        expected_sequence += 1

        # Kết thúc nếu hết file
        if len(chunk) < CHUNK_SIZE:
            print("Download complete")
            break

if __name__ == "__main__":
    start_client()


import socket

# Configurations
HOST = '127.0.0.1'
PORT = 12345
CHUNK_SIZE = 1024  # 1 KB
OUTPUT_DIR = "downloads"

def receive_file(client_socket, server_addr, file_name):
    try:
        # Yêu cầu file từ server
        client_socket.sendto(file_name.encode(), server_addr)

        # Nhận thông tin file
        data, _ = client_socket.recvfrom(1024)
        file_info = data.decode().split()
        file_name, file_size = file_info[0], int(file_info[1])

        print(f"Receiving file '{file_name}' ({file_size} bytes)")

        # Tạo file nhận
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        file_path = os.path.join(OUTPUT_DIR, file_name)
        with open(file_path, "wb") as f:
            expected_seq = 0
            received_size = 0

            while True:
                data, _ = client_socket.recvfrom(CHUNK_SIZE + 8)
                if data == b"END":
                    print("File transfer complete.")
                    break

                # Tách sequence number và dữ liệu
                seq_num = int(data[:8].decode())
                chunk = data[8:]

                if seq_num == expected_seq:
                    # Ghi dữ liệu vào file
                    f.write(chunk)
                    received_size += len(chunk)
                    print(f"Received chunk {seq_num} ({received_size}/{file_size} bytes)")

                    # Gửi ACK
                    client_socket.sendto(f"{seq_num}".encode(), server_addr)
                    expected_seq += 1
                else:
                    # Gửi lại ACK cho sequence trước đó
                    print(f"Out of order chunk. Expected {expected_seq}, got {seq_num}")
                    client_socket.sendto(f"{expected_seq - 1}".encode(), server_addr)

    except Exception as e:
        print(f"Error: {e}")

def main():
    # Tạo UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_addr = (HOST, PORT)

    # Danh sách file cần tải
    files_to_download = ["File1.zip", "File2.zip"]
    for file_name in files_to_download:
        receive_file(client_socket, server_addr, file_name)

    client_socket.close()

if __name__ == "__main__":
    main()
