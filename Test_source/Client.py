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
