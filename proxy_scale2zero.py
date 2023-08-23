import logging
import sys
import socket
import select
from threading import Timer
import time

from sla_operator import *
from verticalscale_operator import *

# Create and configure logger
logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO) #, datefmt='%m/%d/%Y %H:%M:%S %z')
logger = logging.getLogger("sidecar_proxy")

# Changing the buffer_size and delay, you can improve the speed and bandwidth.
# But when buffer get to high or delay go too down, you can broke things
BUFFERSIZE = 4096
DELAY = 0.0001
forward_to = ('127.0.0.1', getContainersPort()) # Find port number of the service !!!!!!!!!!
PROXY_PORT = 80
TIME_SHORT = 30.0 # Timer to zeroimport logging
TIME_LONG = 90.0
PROXY_ADDR = ('127.0.0.1', PROXY_PORT)


class ResourcesState():
    def __init__(self, cpu_req, cpu_lim, mem_req, mem_lim, resp_time):
        self.cpu_req = cpu_req
        self.cpu_lim = cpu_lim
        self.mem_req = mem_req
        self.mem_lim = mem_lim
        self.resp_time = resp_time


class Forward:
    def __init__(self):
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, host, port):
        try:
            self.forward.connect((host, port))
            return self.forward
        except Exception as e:
            logger.error(e)
            return False

class TheServer:
    """
    Sidecar proxy server with vertical scaling features. Besides performing forwarding proxy functions, it is an event-based 
    CPU core and memory allocation controller that performs scale TO and FROM zero.

    * Scale TO zero: When an app container has not received any request for a period of time, it scales down the resources of
    the app container, so it stays alive but consuming the bare minimum CPU allowed by K8s. This is the "zero" state.
    
    * Scale FROM zero: When an app container is in "zero" state and receives a request, it is scaled up to the resource values
    specified in the Deployment file so the app container can serve the request.

    Args:
        host: Address to which the server listens to
        port: Port to which the server listens to

    Returns:
        Instance of TheServer object
    """
    

    input_list = []
    channel = {}
    waiting_time_interval = 1 # in seconds
    separator = "____________________________________________________________________________________________________"

    def __init__(self, host, port):
        self.s = None
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(200)
        # Zero state definition (it must be fine tuned for every app)
        self.zero_state = ResourcesState(cpu_req="10m", cpu_lim="10m", mem_req="10Mi", mem_lim="10Mi", resp_time="1000000m")
        self.reqs_in_queue = 0
        self.users_in_sys = 0
        self.clients_req_pending_list = []

    def vscale_to_zero(self):
        logger.info(self.separator)
        logger.info("Vertical scale TO zero")
        verticalScale(self.zero_state.cpu_req, self.zero_state.cpu_lim, self.zero_state.mem_req, self.zero_state.mem_lim)
        #updateSLA(self.zero_state.cpu_req, self.zero_state.cpu_lim, self.zero_state.mem_req, self.zero_state.mem_lim, self.zero_state.resp_time)
        logger.info(self.separator)

    def vscale_from_zero(self):
        logger.info(self.separator)
        logger.info("Vertical scale FROM zero")
        [cpu_req, cpu_lim, mem_req, mem_lim] = getDefaultConfigContainer()
        #TODO: Pass default SLA as a dict
        verticalScale(cpu_req, cpu_lim, mem_req, mem_lim)
        #updateSLA(cpu_req, cpu_lim, mem_req, mem_lim, "100m")
        logger.info(self.separator)

    def create_timer(self,time):
        return Timer(time,self.vscale_to_zero)

    def create_and_start_timer(self,time):
        self.t = self.create_timer(time)
        #self.t.daemon = True # TODO: Possible way to handle ctrl+C interruption and close proxy w/o sending other request.
        self.t.start()

    def main_loop(self):
        """
        Flow logic of the proxy server. 
        Args: Self
        Returns: Nothing
        """
        # TODO: Introduce logic that makes use of metrics-server API for the TO zero
        self.input_list.append(self.server)
        self.create_and_start_timer(TIME_SHORT)
        while 1:
            time.sleep(DELAY)
            ss = select.select
            inputready, outputready, exceptready = ss(self.input_list, [], [])
            for self.s in inputready:
                if self.s == self.server:
                    # Perform vertical scaling and wait for container is ready before forwarding the request.
                    if isInZeroState(self.zero_state):
                        self.vscale_from_zero()
                        ctr = 0
                        # Wait some time till app container is ready
                        while ((isContainerReady() != True)):
                            ctr = ctr+1
                            logger.info("Cycle of %s secs #: %s" % (self.waiting_time_interval, ctr))
                            time.sleep(self.waiting_time_interval)
                    self.on_accept() # Attempt to forward the request to the app
                    break

                try:
                    self.data = self.s.recv(BUFFERSIZE)
                except Exception as e:
                    logger.error("Error caused by socket.recv(BUFFERSIZE)")
                    logger.error(e)
                    #break

                # Close connection when no more data is in buffer
                if len(self.data.decode()) == 0:
                    logger.info("NO MORE DATA IN BUFFER!")
                    self.on_close()
                    break
                else:
                    try:
                        self.on_recv()
                    except Exception as e:
                        logger.error("Error caused by socker.send(data)")
                        logger.error(e)
                        self.on_close()
                        break

    def on_accept(self):
        forward = Forward().start(forward_to[0], forward_to[1])
        clientsock, clientaddr = self.server.accept()
        if forward:
            logger.info(self.separator)
            logger.info((clientaddr, "has connected"))

            self.input_list.append(clientsock)
            self.input_list.append(forward)
            self.channel[clientsock] = forward
            self.channel[forward] = clientsock

            """ logger.info(f"self.s is: {self.s}")
            logger.info(f"clientsock is: {clientsock}")
            logger.info(f"forward is: {forward}")
            logger.info(f"channel is: {self.channel}")
            logger.info(f"input_list is: {self.input_list}") """
            
        else:
            logger.info("Can't establish connection with remote server.")
            logger.info(("Closing connection with client side", clientaddr))
            clientsock.close()

    def on_close(self):
        logger.info((self.s.getpeername(), "has disconnected"))
                
        """ logger.info(f"self.s is: {self.s}")
        logger.info(f"channel is: {self.channel}")
        logger.info(f"self.channel[self.s] is: {self.channel[self.s]}")
        logger.info(f"input_list is: {self.input_list}") """

        if self.s.getpeername() in self.clients_req_pending_list:
            logger.info("Client disconnected had pending requests")
            self.clients_req_pending_list.remove(self.s.getpeername())
            self.reqs_in_queue = self.reqs_in_queue - 1
            self.timer_controlled_by_reqs()

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
        logger.info(self.separator)

    def on_recv(self):
        data = self.data
        logger.info(data)

        """ # Restart LONG timer after receiving a request
        if (self.channel[self.s].getpeername() == forward_to):
            if self.t.is_alive(): self.t.cancel()
            self.create_and_start_timer(TIME_LONG) """

        """ logger.info(f"self.s: {self.s}")
        logger.info(f"self.channel[self.s] is: {self.channel[self.s]}")
        logger.info(f"channel is: {self.channel}") """

        # Connection destination remote address. If req then app's addr, if resp, then client addr
        conn_dst_remote = self.channel[self.s].getpeername()
        # Connection destination local address. If req then random port assigned to proxy, if resp, then PROXY_ADDR
        conn_dst_local =  self.channel[self.s].getsockname()
        conn_orig_local = self.s.getsockname()
        conn_orig_remote = self.s.getpeername()

        # TRANSITIONS
        # Socket obj: For laddr use mySocket.getsockname() and for raddr use mySocket.getpeername()
        # Proxy receiving request
        if ((conn_dst_remote == forward_to) and ("GET" in data.decode())):
            self.reqs_in_queue = self.reqs_in_queue + 1
            self.clients_req_pending_list.append(conn_orig_remote)
            #if self.t.is_alive(): self.t.cancel()
            #self.create_and_start_timer(TIME_LONG)
        # Proxy receiving response
        if ((conn_dst_local == PROXY_ADDR) and (conn_dst_remote in self.clients_req_pending_list)): #and (self.reqs_in_queue > 0)):
            self.reqs_in_queue = self.reqs_in_queue - 1
            self.clients_req_pending_list.remove(conn_dst_remote)

        self.timer_controlled_by_reqs()
        self.channel[self.s].send(data)

    def timer_controlled_by_reqs(self):
        # STATES
        if ((self.reqs_in_queue == 0) and (self.t.is_alive() == False)): self.create_and_start_timer(TIME_SHORT)
        if ((self.reqs_in_queue != 0) and self.t.is_alive()): self.t.cancel()
        logger.info(f"{self.reqs_in_queue} requests in queue...")
        logger.info(f"Clients with pending requests: {self.clients_req_pending_list}")
      
if __name__ == '__main__':
    server = TheServer('0.0.0.0', PROXY_PORT) # Socket of the Proxy server
    try:
        server.main_loop()
    except KeyboardInterrupt:
        logger.info("Ctrl C - Stopping server")
        sys.exit(1)