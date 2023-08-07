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
    waiting_time_interval = 5 # in seconds
    separator = "____________________________________________________________________________________________________"

    def __init__(self, host, port):
        self.s = None
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(200)

    def vscale_to_zero(self):
        print(self.separator)
        verticalScale(1, 1, 1, 1)
        print("Vertical scale to zero")
        print(self.separator)

    def vscale_from_zero(self):
        print(self.separator)
        verticalScale(10, 10, 10, 10) #TODO: These values vary depending the min resources required by the app
        print("Vertical scale from zero")
        print(self.separator)

    def create_timer(self):
        return Timer(TIME,self.vscale_to_zero)

    def create_and_start_timer(self):
        self.t = self.create_timer()
        self.t.start()

    def main_loop(self):
        self.input_list.append(self.server)
        self.create_and_start_timer()
        while 1:
            time.sleep(delay)
            ss = select.select
            inputready, outputready, exceptready = ss(self.input_list, [], [])
            for self.s in inputready:
                if self.s == self.server:
                    self.t.cancel()
                    self.create_and_start_timer()
                    if verifyInZeroState():
                        self.t.cancel()
                        self.vscale_from_zero()
                        ctr = 0
                        while isContainerReady() == False:
                            ctr = ctr+1
                            print("Cycle of %s secs #: %s" % (self.waiting_time_interval, ctr))
                            time.sleep(self.waiting_time_interval) # Attempt to give some time to update container resources
                        self.create_and_start_timer()
                    self.on_accept()
                    break

                self.data = self.s.recv(buffer_size)
                if len(self.data) == 0:
                    self.on_close()
                    break
                else:
                    self.on_recv()

    def on_accept(self):
        forward = Forward().start(forward_to[0], forward_to[1])
        clientsock, clientaddr = self.server.accept()
        if forward:
            print(self.separator)
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
        print(self.separator)
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
    server = TheServer('0.0.0.0', 80) # Socket of the Proxy server
    try:
        server.main_loop()
    except KeyboardInterrupt:
        print("Ctrl C - Stopping server")
        sys.exit(1)
