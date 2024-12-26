import socket
from threading import Thread
from queue import Queue
import threading
import time
import signal
import os
import sys

class Client:

    def __init__(self, HOST, PORT):
        # self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.socket.connect((HOST, PORT))
        self.socket = [] * 5
        for i in range(5):
            self.socket.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            self.socket[i].connect((HOST, PORT))

        print("\nClient and server are connected\n")

        self.need_file = Queue()
        self.running = True
        input_thread = Thread(target = self.read_input_file)
        send_request_thread = Thread(target = self.send_request)

        try:
            self.rcv_msg() # rcv_file_list
            input_thread.start()
            send_request_thread.start()
            input_thread.join()
            send_request_thread.join()
        except KeyboardInterrupt:
            self.stop()
        finally:
            self.stop()
        

    def read_input_file(self):
        filename = "TCP\input.txt"
        start = 0

        try:
            while self.running:
                with open(filename, "r") as f:
                    f.seek(start)
                    new_files = [line.strip() for line in f.readlines()]
                    start = f.tell()
                
                for file in new_files:
                    if file == "": continue
                    self.need_file.put(file)
                        
                f.close()
                time.sleep(5)
        except Exception as e:
            print(f"Error in send_request: {e}")
        finally:
            self.socket[4].close()

    def send_request(self):
        try:
            while self.running:
                if not self.need_file.empty():
                    filename = self.need_file.get()
                    msg = f"Download {filename}"
                    print(f"Client: {msg}")
                    self.socket[4].send(msg.encode())
                    
                    # response file exist or not
                    server_response = self.socket[4].recv(1024).decode()
                    print("\033[1;31;40m" + "Server: " + server_response + "\033[0m")
                    if "not exist" not in server_response:
                        self.rcv_file(filename)

        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.socket[4].close()

    def rcv_file(self, filename):
        server_msg = self.socket[4].recv(1024).decode()    # rcv_file_size
        print(server_msg)
        file_size = int(server_msg)
        FileClient(filename, file_size, self).rcv_file()

    def rcv_msg(self):
        try:
            server_msg = self.socket[4].recv(1024).decode()
            print("\033[1;31;40m" + "Server: " + server_msg + "\n\033[0m")
        except Exception as e:
            print(f"Error in rcv_msg: {e}")

    def stop(self):
        self.running = False
        # self.socket.sendall("DISCONNECT".encode())
        self.socket[4].close()
        print("Disconnected!")


class FileClient:
    def __init__(self, filename, file_size, Client):
        self.filename = filename
        self.socket = Client.socket

        if not os.path.exists("receive-file"):
            os.mkdir("receive-file")

        self.output_file = "receive-file/" + filename
        self.chunks_data = [None] * 4
        self.chunks = []
        self.num_chunk = 4

        for chunk_id in range(self.num_chunk):
            chunk_start = chunk_id * (file_size // 4)

            if chunk_id < 3:
                chunk_end = (chunk_id + 1) * (file_size // 4)
            else:
                chunk_end = file_size
            chunk_size = chunk_end - chunk_start
            self.chunks.append((chunk_start, chunk_end, chunk_size))

    def rcv_file(self):
        threads = []

        for chunk_id in range(4):
            thread = threading.Thread(target = self.rcv_chunk, args = (chunk_id, ))
            threads.append(thread)
            thread.start()

        self.rcv_progress()
        for thread in threads:
            thread.join()

        self.merge_chunks()
        server_msg = self.socket[4].recv(1024).decode()
        print("\033[1;31;40m" + "Server: " + server_msg + "\033[0m")

    def rcv_chunk(self, chunk_id):
        start, end, size = self.chunks[chunk_id]
        try:

            data = b""
            while start < end:
                packet = self.socket[chunk_id].recv(min(1024, end - start))
                if not packet: break
                data += packet
                start += len(packet)

            self.chunks_data[chunk_id] = data

        except Exception as e:
            print(f"Error downloading chunk {chunk_id + 1}: {e}")

    def rcv_progress(self):
        while True:
            progress_msg = self.socket[4].recv(1024).decode()  
            print("\033[1;31;40m" + progress_msg + "\033[0m")

            if "successfully" in progress_msg: break

            # move cursor up
            sys.stdout.write("\033[4A\033[0G\033[J")

    def merge_chunks(self):
        with open(self.output_file, "wb") as f:
            for chunk in self.chunks_data:
                f.write(chunk)
        f.close()
        print(f"\nFile saved to {self.output_file}")

    
if __name__ == "__main__":
    try:
        Client("10.131.4.140", 7632)
    except KeyboardInterrupt:
        print("\nExiting...")
        Client.stop()
        sys.exit(0)
