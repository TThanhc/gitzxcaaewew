"""
import socket

HOST = "127.0.0.1"
SERVER_PORT = 61504

UDP_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDP_server_socket.bind((HOST, SERVER_PORT))#
"""
import socket

# Tạo UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('localhost', 12345))

print("Server đang lắng nghe...")

expected_sequence = 0  # Sequence number mong đợi

while True:
    # Nhận dữ liệu từ client
    data, client_address = server_socket.recvfrom(1024)
    sequence, message = data.decode().split(":", 1)
    sequence = int(sequence)

    if sequence == expected_sequence:
        print(f"Nhận được gói tin hợp lệ: Sequence={sequence}, Message={message}")
        expected_sequence += 1
    else:
        print(f"Gói tin bị bỏ qua: Sequence={sequence} (Expected={expected_sequence})")

    # Gửi ACK cho client
    ack = f"ACK:{sequence}"
    server_socket.sendto(ack.encode(), client_address)
