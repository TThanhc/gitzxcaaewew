import socket
import time
import threading
import hashlib
import os


def calculate_checksum(data):
    return hashlib.md5(data.encode()).hexdigest()


server_address = ('127.0.0.1', 61504)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(server_address)
# sock.settimeout(2)  # Timeout 2 giây

sequence_number = 0
ack_number = 0
print("Server: ", sock.getsockname(), "is waiting for message!!!")


def recv_message(sequence_number, ack_number):
    while True:
        # Nhận tin nhắn từ client
        packet, client_address = sock.recvfrom(1024)
        packet = packet.decode()
        # phân tách gói tin
        sequence_number_C, ack_number_C, checksum, message = packet.split('|')
        # tin nhắn phản hồi
        response = 0
        # kiểm tra checksum
        if calculate_checksum(message) == checksum:
            if int(sequence_number_C) == int(ack_number):
                print("Received: ", message, " from ", client_address)
                response = "OK"
                # tăng ack_number
                ack_number = int(ack_number) + len(message.encode())
                # Gửi gói tin phản hồi OK khi không có lỗi
                sock.sendto(response.encode(), client_address)
                break
        # Nếu gói tin bị lỗi gửi NOK
        response = "NOK"
        # Gửi gói tin phản hồi
        sock.sendto(response.encode(), client_address)
    return ack_number


def send_file(filename, server_ip, server_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (server_ip, server_port)
    
    with open(filename, 'rb') as f:
        chunk = f.read(1024)
        while chunk:
            sock.sendto(chunk, server_address)
            ack, _ = sock.recvfrom(1024)
            if ack.decode() != 'ACK':
                print("Failed to receive ACK, resending chunk")
                continue
            chunk = f.read(1024)
    
    sock.sendto(b'EOF', server_address)
    

ack_number = recv_message(sequence_number, ack_number)
ack_number = recv_message(sequence_number, ack_number)
ack_number = recv_message(sequence_number, ack_number)
ack_number = recv_message(sequence_number, ack_number)
ack_number = recv_message(sequence_number, ack_number)
"""
for chunk in data_chunks:
    while True:
        # Gắn sequence number và checksum
        checksum = calculate_checksum(chunk)
        packet = f"{sequence_number}|{checksum}|{chunk}"
        
        # Gửi gói tin
        print(f"Sending: {packet}")
        sock.sendto(packet.encode(), server_address)
        try:
            # Chờ ACK
            response, client_address = sock.recvfrom(1024)
            ack = response.decode()
            
            if ack == f"ACK{sequence_number}":
                print(f"Received: {ack}")
                # Chuyển sang sequence number tiếp theo
                sequence_number = 1 - sequence_number  
                break
            else:
                print(f"Received invalid ACK: {ack}, resending...")
        except socket.timeout:
            print("Timeout, resending...")
"""
sock.close()
