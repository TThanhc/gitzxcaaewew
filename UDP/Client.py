import socket
import hashlib
import os
import threading


def calculate_checksum(data):
    return hashlib.md5(data.encode()).hexdigest()


# Cấu hình UDP socket
server_address = ('127.0.0.1', 61504)
client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_sock.bind(('127.0.0.1', 12345))
sequence_number = 0
ack_number = 0


def send_message(sequence_number, ack_number, message):
    # Tính checksum
    checksum = calculate_checksum(message)
    # Thêm các trường thông tin vào message --> packet
    packet = f"{sequence_number}|{ack_number}|{checksum}|{message}"
    client_sock.sendto(packet.encode(), server_address)
    # Nhận gói tin phản hồi
    response, _ = client_sock.recvfrom(1024)
    response = response.decode()
    while response == "NOK":
        client_sock.sendto(packet.encode(), server_address)
        response, _ = client_sock.recvfrom(1024)
        response = response.decode()
    # tăng sequence number
    sequence_number = int(sequence_number) + len(message.encode())
    return sequence_number


data_chunks = ["Hello", "World", "This", "is", "RDT"]
#message = input("Enter message: ")
for data in data_chunks:
    sequence_number = send_message(sequence_number, ack_number, data)

"""
while True:
    try:
        # Nhận gói tin
        packet, client_address = sock.recvfrom(1024)
        packet = packet.decode()
        print(f"Received: {packet}")        
        # Phân tích gói tin
        sequence_number, checksum, data = packet.split('|')
        sequence_number = int(sequence_number)
        
        # Kiểm tra checksum
        if calculate_checksum(data) == checksum and 
        sequence_number == expected_sequence_number:
            print(f"Valid packet: {data}")
            # Gửi ACK
            ack = f"ACK{sequence_number}"
            sock.sendto(ack.encode(), client_address)
            # Chuyển sang số thứ tự tiếp theo
            expected_sequence_number = 1 - expected_sequence_number
        else:
            print("Invalid packet or sequence number!")
            # Gửi NACK
            nack = f"NACK{expected_sequence_number}"
            sock.sendto(nack.encode(), client_address)
    except KeyboardInterrupt:
        print("Receiver shutting down.")
        break
"""
client_sock.close()
