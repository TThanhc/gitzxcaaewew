import socket
from threading import Thread
from queue import Queue
import threading
import time
import signal
import os
import sys

HOST = "192.168.1.63"
PORT = 7632

class Client:

    def __init__(self, HOST, PORT):
        self.socket = [] * 5
        for i in range(5):
            self.socket.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            self.socket[i].connect((HOST, PORT))

        print("[NOTIFICATION] Client and server are connected.\n")

        signal.signal(signal.SIGINT, self.stop)

        self.need_file = Queue()
        self.running = True
        self.file_list = []
        self.folder_path = ""
        

        try:
            self.rcv_file_list()
            self.send_folder_path()

            input_thread = Thread(target = self.read_input_file, daemon = True)
            # self.read_input_file()
            send_request_thread = Thread(target = self.send_request, daemon = True)

            input_thread.start()
            send_request_thread.start()

            while self.running:
                input("")

            input_thread.join()
            send_request_thread.join()

        except KeyboardInterrupt:
            self.stop()
        except ConnectionAbortedError:
            self.stop()
        except (Exception, ConnectionAbortedError) as e:
            print(f"Error in main: {e}")
        # finally:
            # self.stop()

    def send_folder_path(self):
        try:
            server_msg = self.socket[4].recv(1024).decode()
            print("\033[1;31;40m" + "Server: " + server_msg + "\033[0m")
            msg = input("Client: ")
            self.socket[4].send(msg.encode())
            self.folder_path = msg
        except KeyboardInterrupt:
            self.stop()
        except ConnectionAbortedError:
            self.stop()
    
    def get_file_size(self, filename):
        return int(next((size for name, size in self.file_list if name == filename), None))

    def read_input_file(self):
        filename = "C:\\Users\\ADMIN\\Desktop\\gitzxcaaewew\\input.txt"
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
        except KeyboardInterrupt:
            self.stop()
        except ConnectionAbortedError:
            self.stop()

    def send_request(self):
        try:
            while self.running:
                if not self.need_file.empty():
                    filename = self.need_file.get()
                    msg = f"GET {filename}"
                    print(f"Client: {msg}")
                    self.socket[4].send(msg.encode())
                    
                    # response file exist or not
                    server_response = self.socket[4].recv(1024).decode()
                    print("\033[1;31;40m" + "Server: " + server_response + "\033[0m")
                    if "not exist" not in server_response:
                        file_size = self.get_file_size(filename)
                        rcv_file_thread = Thread(target = FileClient(filename, file_size, self, self.folder_path).rcv_file, daemon=True)
                        rcv_file_thread.start()
                        rcv_file_thread.join()

        except Exception as e:
            print(f"Error in send request: {e}")
        except KeyboardInterrupt:
            self.stop()
        except ConnectionAbortedError:
            self.stop()
        finally:
            self.stop()

    def rcv_file_list(self):
        try:
            server_msg = self.socket[4].recv(1024).decode()
            print("\033[1;31;40m" + "Server: " + server_msg + "\n\033[0m")
            
            for line in server_msg.splitlines():
                if line.startswith("List of files:"):
                    continue
                if " - " in line:
                    name, size = line.split(" - ")
                    self.file_list.append((name, float(size.replace("B", "").strip())))

        except Exception as e:
            print(f"Error in rcv_msg: {e}")
        except KeyboardInterrupt:
            self.stop()
        except ConnectionAbortedError:
            self.stop()

    def stop(self, *args, **kwargs):
        self.running = False
        print("\n[NOTIFICATION] Disconnected!\n")
        os._exit(0)
        print("Active threads:", threading.enumerate())

class FileClient:
    def __init__(self, filename, file_size, Client, folder_path):
        self.filename = filename
        self.socket = Client.socket
        self.output_file = folder_path + "/" + filename
        self.num_chunk = 4
        self.chunks_data = [None] * self.num_chunk
        self.chunks = []
        self.running = True
        
        for chunk_id in range(self.num_chunk):
            chunk_start = chunk_id * (file_size // self.num_chunk)

            if chunk_id < self.num_chunk - 1:
                chunk_end = (chunk_id + 1) * (file_size // self.num_chunk)
            else:
                chunk_end = file_size
            chunk_size = chunk_end - chunk_start
            self.chunks.append((chunk_start, chunk_end, chunk_size))

    def rcv_file(self):
        try:
            threads = []

            for chunk_id in range(self.num_chunk):
                thread = Thread(target = self.rcv_chunk, args = (chunk_id, ), daemon=True)
                threads.append(thread)
                thread.start()

            self.rcv_progress()
            for thread in threads:
                thread.join()

            self.merge_chunks()
            server_msg = self.socket[4].recv(1024).decode()
            print("\033[1;31;40m" + "Server: " + server_msg + "\033[0m")
        except Exception as e:
            print(f"Error in rcv_file: {e}")
        except KeyboardInterrupt:
            self.stop()
        except ConnectionAbortedError:
            self.stop()
        finally:
            self.running = False

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
            print(f"Error rcv chunk {chunk_id + 1}: {e}")
        except KeyboardInterrupt:
            self.stop()
        except ConnectionAbortedError:
            self.stop()

    def rcv_progress(self):
        try:
            while self.running:
                progress_msg = self.socket[4].recv(1024).decode()  
                print("\033[1;31;40m" + progress_msg + "\033[0m")

                if "successfully" in progress_msg: break

                # move cursor up
                sys.stdout.write("\033[4A\033[0G\033[J")
        except KeyboardInterrupt:
            self.stop()
        except ConnectionAbortedError:
            self.stop()

    def merge_chunks(self):
        with open(self.output_file, "wb") as f:
            for chunk in self.chunks_data:
                f.write(chunk)
        f.close()

    def stop(self, *args, **kwargs):
        self.running = False
        print("\n[NOTIFICATION] Disconnected!\n")
        os._exit(0)
    
if __name__ == "__main__":
    def handle_signal(signal, frame):
        Client.stop()

    signal.signal(signal.SIGINT, handle_signal)

    try:
        Client(HOST, PORT)
    except KeyboardInterrupt:
        Client.stop()