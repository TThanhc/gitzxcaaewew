import socket
import threading

HOST = "127.0.0.1"
SERVER_PORT = 65432
FORMAT = "utf8"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind((HOST, SERVER_PORT))
s.listen()
print("Server (", SERVER_PORT, ")is Waiting for Client")

def handleClient(conn: socket, addr):
    print("Client: ", conn.getsockname(), "is connecting to Sever (", SERVER_PORT, ")")
    msg = None
    while (msg != "s"):
        msg = conn.recv(1024).decode(FORMAT)
        print("Client says: ", msg)
        if (msg == "s"):
            break
        conn.sendall(msg.encode(FORMAT))
        msg = input("talk: ")
        conn.sendall(msg.encode(FORMAT))
        conn.recv(1024).decode(FORMAT)
    print("Quit")

try:
    conn, addr = s.accept()
    handleClient(conn, addr)    
except:
    print("error")
conn.close()