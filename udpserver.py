import socket
import threading
import os
import time
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
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
    "active_addrs": {},
    "messages": []
}
admin_addr = None
lock = threading.Lock()

def now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def safe_filename(filename):
    filename = os.path.basename(filename)
    if not filename or filename in [".", ".."]:
        return None
    return filename


def is_admin(addr):
    return addr == admin_addr


def get_permissions_for_role(role):
    if role == "ADMIN":
        return ["read", "write", "execute"]
    return ["read"]


def register_or_update_client(addr):
    global admin_addr

    with lock:
        current_time = time.time()

        if addr not in stats["active_addrs"]:
            if len(stats["active_addrs"]) >= MAX_CLIENTS:
                return False, "Serveri eshte plot. Lidhjet e reja po refuzohen."

            role = "ADMIN" if admin_addr is None else "USER"

            if admin_addr is None:
                admin_addr = addr

            stats["active_addrs"][addr] = current_time
            stats["active_connections"] = len(stats["active_addrs"])
            stats["clients_info"].append({
                "ip": addr[0],
                "port": addr[1],
                "role": role,
                "permissions": get_permissions_for_role(role),
                "last_seen": now_str()
            })
        else:
            stats["active_addrs"][addr] = current_time
            for client in stats["clients_info"]:
                if client["ip"] == addr[0] and client["port"] == addr[1]:
                    client["last_seen"] = now_str()
                    break

    return True, "OK"