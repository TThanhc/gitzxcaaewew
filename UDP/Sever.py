import socket
# import time
# import threading
import hashlib
import os

CHUNK_SIZE = 1024 * 1024
server_address = ('127.0.0.1', 61504)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(server_address)
TIMEOUT = 1
# sock.settimeout(2)  # Timeout 2 giây
sequence_number = 0
ack_number = 0
print("Server: ", sock.getsockname(), "is waiting for message!!!")


def calculate_checksum(data):
    return hashlib.md5(data.encode()).hexdigest()


def send_chunk(client_address, filename, chunk_id, total_chunks):
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Đọc dữ liệu chunk từ file
        file_size = os.path.getsize(filename)
        start = chunk_id * (file_size // total_chunks)  # Bắt đầu chunk
        end = start + (file_size // total_chunks)      # Kết thúc chunk
        if chunk_id == total_chunks - 1:  # Chunk cuối có thể chứa phần dư
            end = file_size

        with open(filename, "rb") as f:
            f.seek(start)
            while start < end:
                data = f.read(min(CHUNK_SIZE, end - start))
                if not data:
                    break
                # server_socket.sendto(data, client_address)
                start += len(data)

        print(f"Chunk {chunk_id} sent to Client")
        server_socket.close()
    except Exception as e:
        print(f"Error sending chunk {chunk_id}: {e}")


def send_bytes_rdt(data, client_address, server_socket):
    global sequence_number
    
    # Tính checksum
    checksum = calculate_checksum(data)
       
    # Thêm các trường thông tin vào message --> packet
    packet = f"{sequence_number}|{ack_number}|{checksum}|{data}"
    server_socket.sendto(packet.encode(), client_address)
    
    # Nhận gói tin phản hồi
    # Chờ ACK
    # try:
    #     server_socket.settimeout(TIMEOUT)
    #     ack_data, addr = server_socket.recvfrom(1024)

    #     if ack_sequence == sequence_number:
    #         print(f"Received ACK for sequence {sequence_number}")
    #         sequence_number += 1
    # except socket.timeout:
    #     print(f"Timeout for sequence {sequence_number}, resending...")
    
    response_packet, _ = server_socket.recvfrom(1024)
    seq_c, ack_c = response_packet.encode().split('|')
    while sequence_number == ack_c:
        server_socket.sendto(packet.encode(), client_address)
        response_packet, _ = server_socket.recvfrom(1024)
        response_packet = response_packet.decode()


def recv_message(sequence_number, ack_number, message):
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
    return packet, client_address


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
