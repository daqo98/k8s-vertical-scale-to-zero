import logging
import sys
import socket
import select
import threading
import time

from VerSca20_operator import *

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.DEBUG)
logger = logging.getLogger("sidecar_proxy")

IP = "0.0.0.0"
PORT = 80
ADDR = (IP, PORT)
BUFFERSIZE = 4096
TIME_SHORT = 30.0
SEPARATOR = "____________________________________________________________________________________________________"
ZERO_CPU_REQ = "10m"
ZERO_CPU_LIM = "10m"
REQ_PENDING_LIST = []
REQ_QUEUE = 0
REQ_PER_CLIENT = {}
FORWARD_TO = ('127.0.0.1', getContainersPort("prime-numbers"))
CHANNEL = {}

class ResourcesState():
    def __init__(self, cpu_req, cpu_lim, **kwargs):
        self.cpu_req = cpu_req
        self.cpu_lim = cpu_lim

        for key, val in kwargs.items():
            if (key == "mem_req"): self.mem_req = val
            if (key == "mem_lim"): self.mem_lim = val
            if (key == "resp_time"): self.resp_time = val



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


def vscale_to_zero():
    logger.info(SEPARATOR)
    logger.info("Vertical scale TO zero")
    verticalScale(ZERO_CPU_REQ, ZERO_CPU_LIM)
    logger.info(SEPARATOR)

def vscale_from_zero():
    logger.info(SEPARATOR)
    logger.info("Vertical scale FROM zero")
    [cpu_req, cpu_lim, mem_req, mem_lim] = getDefaultConfigContainer()
    verticalScale(cpu_req, cpu_lim)
    logger.info(SEPARATOR)

def create_timer(time):
    return Timer(time,vscale_to_zero)

def create_and_start_timer(time):
    TIMER = create_timer(time)
    TIMER.start()

def timer_controlled_by_reqs():
    if ((REQ_QUEUE == 0) and (TIMER.is_alive() == False)): create_and_start_timer(TIME_SHORT)
    if ((REQ_QUEUE != 0) and TIMER.is_alive()): TIMER.cancel()
    logger.debug(f"{REQ_QUEUE} requests in queue...")
    logger.debug(f"Clients with pending requests: {REQ_PENDING_LIST}")


def handle_client(conn, addr):
    if isInZeroState(ResourcesState(cpu_req="10m", cpu_lim="10m")):
        vscale_from_zero()
    logger.info(f"Client {addr} connected.")
    connected = True
    while connected:
        data = conn.recv(BUFFERSIZE)
        if len(data.decode()) == 0:
            logger.debug("Empty buffer!")
            connected = False
            break
        else:
            logger.info(data)
            dest_addr = CHANNEL[conn].getpeername()
            dest_port = CHANNEL[conn].getsockname()
            origin_port = conn.getsockname()
            origin_addr = conn.getpeername()
            if ((dest_addr == FORWARD_TO) and ("GET" in data.decode())):
                REQ_QUEUE = REQ_QUEUE + 1
                if origin_addr not in REQ_PER_CLIENT:
                    REQ_PER_CLIENT[addr] = 1
                else:
                    REQ_PER_CLIENT[addr] += 1
                REQ_PENDING_LIST.append(addr)
            if ((dest_port == PROXY_ADDR) and (dest_addr in REQ_PENDING_LIST)):
                REQ_QUEUE = REQ_QUEUE - 1
                REQ_PER_CLIENT[dest_addr] = REQ_PER_CLIENT[dest_addr] - 1
                REQ_PENDING_LIST.remove(dest_addr)
            timer_controlled_by_reqs()
            CHANNEL[conn].send(data)
    if addr in REQ_PENDING_LIST:
        logger.info("Client disconnected had pending requests")
        REQ_QUEUE = REQ_QUEUE - REQ_PER_CLIENT[addr]
        REQ_PENDING_LIST.remove(addr)
        del REQ_PER_CLIENT[addr]
        timer_controlled_by_reqs()
    logger.info(f"{addr} has disconnected")
    conn.close()
    CHANNEL[conn].close()
    del CHANNEL[conn]
    del CHANNEL[CHANNEL[conn]]
    logger.info(SEPARATOR)

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()
    while True:
        forward = Forward().start(FORWARD_TO[0], FORWARD_TO[1])
        conn, addr = server.accept()
        if forward:
            logger.info(SEPARATOR)
            logger.info(f"{addr} has connected")
            CHANNEL[conn] = forward
            CHANNEL[forward] = conn
        else:
            logger.info("Can't establish connection with remote server.")
            logger.info(f"Closing connection with client side {addr}")
            conn.close()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        logger.info(f"Active Connections: {threading.active_count() - 1}")
    server.close() # PUEDE QUE HAYA QUE QUITARLO

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Ctrl C - Stopping server")
        sys.exit(1)
    
