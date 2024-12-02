import socket
import threading

HOST = "127.0.0.1"
SERVER_PORT = 65432
FORMAT = "utf8"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind((HOST, SERVER_PORT))
s.listen()


def handleClient(conn: socket, addr):
    print("Client ", nClients + 1, " address: ", addr, " | ", )
    print("conn: ", conn.getsockname())

    msg = None
    while (msg != "s"):
        msg = conn.recv(1024).decode(FORMAT)
        print("Client ", nClients + 1, " says: ", msg)
        if (msg == "s"):
            break
        conn.sendall(msg.encode(FORMAT))
                    
        msg = input("talk: ")
        conn.sendall(msg.encode(FORMAT))
            
        conn.recv(1024).decode(FORMAT)
    
    print("Client ", nClients + 1, " end!!")


print("Server SIDE")
print("server: ", HOST, SERVER_PORT)
print("Waiting for Client")

nClients = 0
while nClients < 3:
    try:
        conn, addr = s.accept()
        thr = threading.Thread(target=handleClient, args=(conn, addr))
        thr.daemon = False
        thr.start()
        nClients += 1
    except:
        print("error")
conn.close()