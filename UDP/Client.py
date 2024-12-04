import socket
import time

# Tạo UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.settimeout(2)  # Timeout 2 giây
server_address = ('localhost', 12345)

sequence_number = 0  # Sequence number bắt đầu

messages = ["Hello Server!", "How are you?", "Goodbye!"]  # Dữ liệu gửi đi

for message in messages:
    while True:  # Thử gửi lại đến khi nhận được ACK
        try:
            # Gửi dữ liệu với sequence number
            data = f"{sequence_number}:{message}"
            print(f"Gửi: {data}")
            client_socket.sendto(data.encode(), server_address)

            # Chờ ACK từ server
            ack, _ = client_socket.recvfrom(1024)
            ack_sequence = int(ack.decode().split(":")[1])

            if ack_sequence == sequence_number:
                print(f"Nhận ACK: {ack}")
                sequence_number += 1  # Tăng sequence number cho gói tin tiếp theo
                break
            else:
                print(f"ACK sai thứ tự: {ack}")

        except socket.timeout:
            print("Timeout! Gửi lại gói tin...")

client_socket.close()
