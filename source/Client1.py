import socket

HOST = "127.0.0.1"
SERVER_PORT = 65432
FORMAT = "utf8"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print("Client SIDE")
client.connect((HOST, SERVER_PORT))
print("Client address: ", client.getsockname())

username = input("Nhap ten: ")
client.sendall(username.encode(FORMAT))

password = input("Nhap mk: ")
client.sendall(password.encode(FORMAT))

input()