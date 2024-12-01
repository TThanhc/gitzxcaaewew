import socket

HOST = "127.0.0.1"
SERVER_PORT = 65432
FORMAT = "utf8"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    print("Client SIDE")
    client.connect((HOST, SERVER_PORT))
    print("Client address: ", client.getsockname())

    msg = None
    while (msg != "s"):
        msg = input("talk: ")
        client.sendall(msg.encode(FORMAT))
        if msg == "s":
           break 
        msg = client.recv(1024).decode(FORMAT)
        print("Server says: ", msg)
except:
    print("error")
client.close()