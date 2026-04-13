import socket
import threading
import os
import time
import json
from datetime import datetime


IP = '192.168.0.24'
PORT = 12000
HTTP_PORT = 8080
MAX_CLIENTS = 5
BUFFER_SIZE = 4096
SERVER_DIR = "server_files"

if not os.path.exists(SERVER_DIR):
    os.makedirs(SERVER_DIR)




def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((IP, PORT))
    server.listen(MAX_CLIENTS)
    print(f"[*] Serveri ne portin {PORT}. Monitorimi: {HTTP_PORT}")
    threading.Thread(target=http_monitor_server, daemon=True).start()


if __name__ == "__main__":
    start_server()




