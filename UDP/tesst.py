import socket
from threading import Thread


clients = {}


def handle_client(addr, server_socket):
    while True:
        data, client_addr = server_socket.recvfrom(1024)
        if client_addr == addr:
            print(f"Data from {client_addr}: {data.decode()}")


# Tạo socket UDP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('0.0.0.0', 12345))


while True:
    data, addr = server_socket.recvfrom(1024)
    if addr not in clients:
        thread = Thread(target=handle_client, args=(addr, server_socket), daemon=True)
        clients[addr] = thread
        thread.start()
