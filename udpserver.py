import socket
import threading
import os
import time
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

# KONFIGURIMET
IP = '127.0.0.1'
PORT = 9000
HTTP_PORT = 8080
MAX_CLIENTS = 4
BUFFER_SIZE = 4096
TIMEOUT = 300
SERVER_DIR = "server_files"

if not os.path.exists(SERVER_DIR):
    os.makedirs(SERVER_DIR)

# UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((IP, PORT))

# Statistika dhe monitorim
stats = {
    "active_connections": 0,
    "total_messages": 0,
    "clients_info": [],
    "active_addrs": {},   # {(ip, port): last_seen_timestamp}
    "messages": []        # ruan mesazhet/kërkesat për monitorim
}

admin_addr = None
lock = threading.Lock()

