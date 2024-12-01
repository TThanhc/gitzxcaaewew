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

try:
    conn, addr = s.accept()

    print("Client address: ", addr)
    print("conn: ", conn.getsockname())

    msg = None
    while (msg != "s"):
        msg = conn.recv(1024).decode(FORMAT)
        print("Client says: ", msg)
        msg = input("talk: ")
        conn.sendall(msg.encode(FORMAT))  
except:
    print("error") 
conn.close()