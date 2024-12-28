from queue import Queue
import socket
import hashlib
from threading import Thread
import threading
import time
import sys
import os

PACKET_SIZE = 1024 + 1024
# Cấu hình UDP socket
server_address = ('127.0.0.1', 61504)


class FileClient:
    def __init__(self):
        self.num_chunk = 4
        self.chunks_data = [None] * self.num_chunk
        self.TIMEOUT = 0.2  # Timeout 1 giây
        self.lock = threading.Lock()
        self.chunk_progress = [0.0] * self.num_chunk
        self.done_chunk = [False] * self.num_chunk
        self.port = [61862, 61863, 61864, 61865]
        self.file_size = 0 
        self.file_name = 0
        self.output_file = "UDP\\receive-file\\"
        self.chunks = []
        self.MAX_TRIES = 1000
        self.chunk_size = 0
        self.need_file = Queue()
        self.list_file = ""

        Thread(target = self.read_input_file).start()

    def stop(self):
        print("\nShutting down Client...")
        os._exit(0)

    def read_input_file(self):
        file_input = "UDP\Client\input.txt"
        start = 0

        try:
            while True:
                try:
                    with open(file_input, "r") as f:
                        f.seek(start)
                        new_files = [line.strip() for line in f.readlines()]
                        start = f.tell()
                    
                    for file in new_files:
                        if file == "": continue
                        if file in new_files:  
                            self.need_file.put(file)
                    f.close()
                    time.sleep(5)
                except KeyboardInterrupt:
                    return
                except ConnectionResetError:
                    print(f"Server {server_address} is not alive.")
                    break
        except Exception as e:
            print(f"Error in send_request: {e}")
        # except KeyboardInterrupt:
        #     self.stop()
        # except ConnectionResetError:
        #     print(f"Server {server_address} is not alive.")
        #     self.stop


    def display_progress(self):
        try:
            while any(done == False for done in self.done_chunk):
                progress_msg = "\n".join([f"Downloading {self.file_name} part {chunk_id + 1}: {self.chunk_progress[chunk_id]:.2f}%" for chunk_id in range(self.num_chunk)])
                print("\033[1;31;40m" + progress_msg + "\033[0m")
                sys.stdout.flush()
                # move cursor up
                time.sleep(0.1)
                sys.stdout.write(f"\033[{self.num_chunk}A\033[0G\033[J")
        except Exception as e:
            print("ERROR display progress: ", {e})

    def get_file_name(self):
        if not self.need_file.empty():
            return self.need_file.get()
        else: 
            return None

    def rcv_progress(self, client_socket):
        while True:
            progress_msg = self.recv_message(client_socket)  
            print("\033[1;31;40m" + progress_msg + "\033[0m")

            if "successfully" in progress_msg: break

            # move cursor up
            sys.stdout.write("\033[4A\033[0G\033[J")
            
    def calculate_checksum(self, data):
        return hashlib.sha256(data).hexdigest()

    def recv_chunk(self, chunk_id):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_sock:
                client_sock.settimeout(self.TIMEOUT)
                # tin nhắn khởi tạo socket
                PING_MSG = str(chunk_id)
                self.send_ping_message(client_sock, PING_MSG)

                start = chunk_id * (self.file_size // int(self.num_chunk)) # Bắt đầu chunk    
                # Kết thúc chunk
                if chunk_id == self.num_chunk - 1:   # Chunk cuối có thể chứa phần dư
                    end = self.file_size
                else:
                    end = start + (self.file_size // int(self.num_chunk))  
                # tải chunk
                ack = 0
                total_chunk = end - start
                received_bytes = 0
                chunk_data = b""
                # biến đếm số lần gửi lại (tối đa 1000 lần)
                fl = True
                cnt = 1
                while True:
                    try:
                        # nhận gói tin
                        packet, _ = client_sock.recvfrom(PACKET_SIZE)
                        if packet.count(b"|") >= 3:
                            seq_s, checksum, id, data = packet.split(b"|", maxsplit=3)
                            seq_s = seq_s.decode()
                            checksum = checksum.decode()
                            id = int(id.decode())
                            if fl:
                                if chunk_id != id:
                                    chunk_id = id
                                    start = chunk_id * (self.file_size // int(self.num_chunk)) # Bắt đầu chunk    
                                    # Kết thúc chunk
                                    if chunk_id == self.num_chunk - 1:   # Chunk cuối có thể chứa phần dư
                                        end = self.file_size
                                    else:
                                        end = start + (self.file_size // int(self.num_chunk))  
                                    total_chunk = end - start
                                fl = False
                            # tin nhắn phản hồi
                            if self.calculate_checksum(data) == checksum:
                                if int(seq_s) == ack:
                                    # số bytes đã nhận
                                    received_bytes += len(data)
                                    # update progress
                                    with self.lock:
                                        self.chunk_progress[chunk_id] = (received_bytes / total_chunk) * 100
                                    # gửi ack lại
                                    response = f"{seq_s}"
                                    client_sock.sendto(response.encode(), server_address)
                                    # thêm các byte vào mảng lưu
                                    chunk_data += data
                                    # Dừng khi nhận đủ chunk
                                    if received_bytes >= total_chunk:
                                        break
                                    ack += 1
                                    continue
                        # gửi lại ack trc đó
                        response = f"{ack - 1}"
                        client_sock.sendto(response.encode(), server_address)
                    except KeyboardInterrupt:
                        break
                    except socket.timeout:
                        cnt = cnt + 1
                        if cnt >= self.MAX_TRIES:
                            print("Error receive data\n")
                            break
                    except ConnectionResetError:
                        print(f"Server disconnected.")
                        client_sock.close()
                        return
                self.done_chunk[chunk_id] = True
                self.chunks_data[chunk_id] = chunk_data
        except KeyboardInterrupt:
            return
        except Exception as e:
            print(f"Error downloading chunk {chunk_id}: {e}")

    def merge_chunks(self):
        self.file_name = self.output_file + self.file_name
        with open(self.file_name, "wb") as f:
            for chunk in self.chunks_data:
                if chunk is not None:
                    f.write(chunk)
                else:
                    print("Error write bytes\n")
                    return
        print(f"\nFile saved to {self.file_name}")

    def start_client(self):
        # tin nhắn khởi tạo
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
                client_socket.settimeout(self.TIMEOUT)
                # tin nhắn khởi tạo socket
                try:
                    fl = self.send_ping_message(client_socket, "23120088")
                    if not fl:
                        return
                    # nhận danh sách file
                    self.list_file = self.recv_message(client_socket)
                    if self.list_file is not None:
                        print(self.list_file)
                    while True:
                        try:
                            # gửi file cần tải
                            self.file_name = self.get_file_name()
                            if self.file_name != None:
                                self.send_message(client_socket, self.file_name)
                                # Nhận file_size hay NOT
                                response = self.recv_message(client_socket)
                                if response != "NOT":
                                    self.file_size = int(response)
                                    self.chunk_size = self.file_size // self.num_chunk                                
                                    # chạy client
                                    threads = []
                                    
                                    for chunk_id in range(self.num_chunk):
                                        thread = threading.Thread(target=self.recv_chunk, args=(chunk_id,))
                                        if thread is not None:
                                            threads.append(thread)
                                            thread.start()
                                    
                                    self.display_progress()

                                    for thread in threads:
                                        if thread is not None:
                                            thread.join()
                                            
                                    self.merge_chunks()
                                    self.chunks_data = [None] * self.num_chunk
                                    self.chunk_progress = [0.0] * self.num_chunk
                                    self.done_chunk = [False] * self.num_chunk
                                else:
                                    print(self.file_name, "does not exist in file list server!!\n")
                        except KeyboardInterrupt:
                            FIN = "EXIT"
                            self.send_message(client_socket, FIN)
                            break
                        except ConnectionResetError:
                            print(f"Server disconnected.")
                            break
                except KeyboardInterrupt:
                    return
        except ConnectionResetError:
            print(f"Server {server_address} is not alive.")
        
    def send_ping_message(self, client_socket : socket, message):
        cnt = 1
        while True:
            try:
                client_socket.sendto(message.encode(), server_address)
                ack, _ = client_socket.recvfrom(PACKET_SIZE)
                if ack.decode() == "OK":
                    return True
            except socket.timeout:
                cnt = cnt + 1
                if cnt >= self.MAX_TRIES:
                    print("Can not send PING_MSG to server\n")
                    break
            except ConnectionResetError:
                print(f"Server {server_address} is not alive.")
                return False
            except KeyboardInterrupt:
                return False

    def send_message(self, client_socket : socket, message):
        cnt = 1
        message = message.encode()
        checksum = self.calculate_checksum(message).encode()
        packet = b"|".join([checksum, message]) 
        while True:
            try:
                client_socket.sendto(packet, server_address)
                ack, _ = client_socket.recvfrom(PACKET_SIZE)
                if ack.decode() == "OK":
                    break
            except socket.timeout:
                cnt = cnt + 1
                if cnt >= self.MAX_TRIES:
                    print("Can't send message to server\n")
                    break
            except ConnectionResetError:
                print(f"Server {server_address} is not alive.")
                return False
            except KeyboardInterrupt:
                return False
    
    def recv_message(self, client_socket : socket):
        cnt = 1
        while True:
            try:
                packet, _ = client_socket.recvfrom(PACKET_SIZE)
                checksum, message = packet.split(b"|")
                checksum = checksum.decode()
                if self.calculate_checksum(message) == checksum:
                    response = "OK"
                    client_socket.sendto(response.encode(), server_address)
                    return message.decode()
                response = "NOK"
                client_socket.sendto(response.encode(), server_address)
            except socket.timeout:
                cnt = cnt + 1
                if cnt >= self.MAX_TRIES:
                    print("Can not receive message from server\n")
                    break
            except ConnectionResetError:
                print(f"Server {server_address} is not alive.")
                break
            except KeyboardInterrupt:
                return

if __name__ == "__main__":
    client = FileClient()
    client.start_client()
    client.stop()
    sys.exit(0)