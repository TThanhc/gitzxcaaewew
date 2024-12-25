def send_message(self, client_socket : socket, message):
        cnt = 1
        message = message.encode()
        checksum = self.calculate_checksum(message).encode()
        packet = b"|".join([checksum, message]) 
        while True:
            client_socket.sendto(packet, server_address)
            try:
                ack, _ = client_socket.recvfrom(PACKET_SIZE)
                if ack.decode() == "OK":
                    break
            except socket.timeout:
                cnt = cnt + 1
                if cnt == self.MAX_TRIES:
                    print("Can't send message to server\n")
                    break


def recv_message(self):
        cnt = 1
        while True:
            try:
                packet, client_address = self.server_socket.recvfrom(PACKET_SIZE)
                checksum, message = packet.split(b"|")
                checksum = checksum.decode()
                if self.calculate_checksum(message) == checksum:
                    response = "OK"
                    self.server_socket.sendto(response.encode(), client_address)
                    return message.decode()
                response = "NOK"
                self.server_socket.sendto(response.encode(), client_address)
            except socket.timeout:
                cnt = cnt + 1
                if cnt == self.MAX_TRIES:
                    print("Can not receive message from client\n")
                    break