import threading

# Shared variable
shared_data = 0
lock = threading.Lock()

def increment():
    global shared_data
    for _ in range(100000):
        with lock:
            shared_data += 1

def decrement():
    global shared_data
    for _ in range(100000):
        with lock:
            shared_data -= 1

# Create threads
thread1 = threading.Thread(target=increment)
thread2 = threading.Thread(target=decrement)

# Start threads
thread1.start()
thread2.start()

# Wait for threads to finish
thread1.join()
thread2.join()

print(f"Final value of shared_data: {shared_data}")


#-------------------------------------------------------

import socket
import threading
import json
import time

# Shared dictionary to track packet state
processed_packets = {}
lock = threading.Lock()  # To ensure thread-safe access

def listener_thread(port, packet_queue):
    """Listener thread to receive packets and add them to the queue."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("0.0.0.0", port))
    print(f"Server is listening on port {port}.")

    while True:
        data, addr = server_socket.recvfrom(1024)  # Receive data
        packet = json.loads(data.decode())
        print(f"Packet received from {addr}: {packet}")

        # Add packet to the processing queue
        packet_queue.put((packet, addr))


def worker_thread(worker_id, packet_queue):
    """Worker thread to process packets from the queue."""
    while True:
        # Get a packet from the queue
        packet, addr = packet_queue.get()
        client_id = packet["client_id"]
        seq_number = packet["seq_number"]

        # Use the lock to ensure thread-safe access to the dictionary
        with lock:
            # Check if the packet is already processed or out of order
            if client_id in processed_packets and seq_number <= processed_packets[client_id]:
                print(f"Worker {worker_id}: Ignoring duplicate or outdated packet {packet}.")
            else:
                # Update the processed sequence number and process the packet
                processed_packets[client_id] = seq_number
                print(f"Worker {worker_id}: Processing packet {packet} from {addr}.")
        
        # Notify the queue that the task is complete
        packet_queue.task_done()


# Main function to start the server
if __name__ == "__main__":
    # Shared queue for incoming packets
    packet_queue = queue.Queue()

    # Start the listener thread
    listener = threading.Thread(target=listener_thread, args=(12345, packet_queue))
    listener.daemon = True
    listener.start()

    # Start worker threads
    for i in range(4):
        worker = threading.Thread(target=worker_thread, args=(i, packet_queue))
        worker.daemon = True
        worker.start()

    print("Server is running... Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)  # Keep the main thread alive
    except KeyboardInterrupt:
        print("\nServer shutting down.")


#-------------------------------------------------------

import socket
import json
import threading
import time

def client_thread(client_id, port):
    """Send packets to the server."""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ("127.0.0.1", port)

    for seq_number in range(5):
        # Create a packet
        packet = {
            "client_id": client_id,
            "seq_number": seq_number,
            "data": f"Message {seq_number} from {client_id}"
        }

        # Send the packet
        client_socket.sendto(json.dumps(packet).encode(), server_address)
        print(f"{client_id} sent packet {seq_number}")
        time.sleep(1)  # Simulate delay between packets

# Start multiple clients
if __name__ == "__main__":
    for i in range(4):
        threading.Thread(target=client_thread, args=(f"client_{i}", 12345)).start()



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
