import socket
import select
import time
import sys
from verticalscale_operator import *
from threading import Timer

# Changing the buffer_size and delay, you can improve the speed and bandwidth.
# But when buffer get to high or delay go too down, you can broke things
buffer_size = 4096
delay = 0.0001
forward_to = ('localhost', getContainersPort()) # Find port number of the service !!!!!!!!!!
TIME = 30.0 # Timer to zero

class Forward:
    def __init__(self):
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, host, port):
        try:
            self.forward.connect((host, port))
            return self.forward
        except Exception as e:
            print(e)
            return False

class TheServer:
    input_list = []
    channel = {}

    def __init__(self, host, port):
        self.s = None
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(200)
        

    def to_zero(self):
        verticalScale(1, 1, 1, 1) # CHECK THE TO_0
        print("Vertical scale to zero")

    def create_timer(self):
        return Timer(TIME,self.to_zero)

    def main_loop(self):
        self.input_list.append(self.server)
        self.t = self.create_timer()
        self.t.start()
        while 1:
            time.sleep(delay)
            ss = select.select
            inputready, outputready, exceptready = ss(self.input_list, [], [])
            for self.s in inputready:
                if self.s == self.server:
                    self.t.cancel()
                    self.t = self.create_timer()
                    self.t.start()
                    #deletePod()
                    if verifyInZeroState():
                        verticalScale(10, 10, 10, 10)
                        print("Vertical scale from zero")
                        time.sleep(20) # Attempt to give some time to update container resources
                    self.on_accept()
                    break

                self.data = self.s.recv(buffer_size)
                if len(self.data) == 0:
                    print("Buffer LEN = 0")
                    self.on_close()
                    break
                else:
                    self.on_recv()

    def on_accept(self):
        print("HOLA")
        forward = Forward().start(forward_to[0], forward_to[1])
        print("CHAO")
        clientsock, clientaddr = self.server.accept()
        if forward:
            print(clientaddr, "has connected")
            self.input_list.append(clientsock)
            self.input_list.append(forward)
            self.channel[clientsock] = forward
            self.channel[forward] = clientsock
        else:
            print("Can't establish connection with remote server.", end=' ')
            print("Closing connection with client side", clientaddr)
            clientsock.close()

    def on_close(self):
        print(self.s.getpeername(), "has disconnected")
        # remove objects from input_list
        self.input_list.remove(self.s)
        self.input_list.remove(self.channel[self.s])
        out = self.channel[self.s]
        # close the connection with client
        self.channel[out].close()  # equivalent to do self.s.close()
        # close the connection with remote server
        self.channel[self.s].close()
        # delete both objects from channel dict
        del self.channel[out]
        del self.channel[self.s]

    def on_recv(self):
        data = self.data
        print(data)
        self.channel[self.s].send(data)
      
if __name__ == '__main__':
    server = TheServer('0.0.0.0', 80) # Socket of the Proxy server !!!!!!!!!!
    try:
        server.main_loop() # loop para vertical from 0, wait for request and forward (hace falta otro loop para vertical to 0) !!!!!!!!!!
    except KeyboardInterrupt:
        print("Ctrl C - Stopping server")
        sys.exit(1)
