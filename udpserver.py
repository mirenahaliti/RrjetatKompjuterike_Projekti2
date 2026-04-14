import socket
import threading
import os
import time
import json
from datetime import datetime

# 1. KONFIGURIMET (Pika 1 e detyrës)
IP = '192.168.0.24'
PORT = 12009
HTTP_PORT = 8080
MAX_CLIENTS = 10  # Pragu (Pika 2)
BUFFER_SIZE = 4096
SERVER_DIR = "server_files"

if not os.path.exists(SERVER_DIR):
    os.makedirs(SERVER_DIR)

# Struktura për monitorim (Pika 4 dhe 7)
stats = {
    "active_connections": 0,
    "total_messages": 0,
    "clients_info": [],
    "active_addrs": {}
}

admin_addr = None  # Për qasjen e plotë (Pika 6)


def get_file_info(filename):
    path = os.path.join(SERVER_DIR, filename)
    if os.path.exists(path):
        size = os.path.getsize(path)
        ctime = datetime.fromtimestamp(os.path.getctime(path)).strftime('%Y-%m-%d %H:%M:%S')
        return f"Size: {size} bytes, Created: {ctime}"
    return "Skedari nuk u gjet."
