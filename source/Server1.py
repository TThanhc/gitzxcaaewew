import socket

HOST = "127.0.0.1"
SERVER_PORT = 65432
FORMAT = "utf8"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind((HOST, SERVER_PORT))
s.listen()

print("Server SIDE")
print("server: ", HOST, SERVER_PORT)
print("Waiting for Client")

conn, addr = s.accept()

print("Client address: ", addr)
print("conn: ", conn.getsockname())

username = conn.recv(1024).decode(FORMAT)
print("Username: ", username)

password = conn.recv(1024).decode(FORMAT)
print("Pass: ", password)

input()