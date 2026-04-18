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




def remove_inactive_clients():
    global admin_addr

    while True:
        time.sleep(5)
        current_time = time.time()

        with lock:
            inactive_clients = [
                addr for addr, last_seen in stats["active_addrs"].items()
                if current_time - last_seen > TIMEOUT
            ]

            for addr in inactive_clients:
                del stats["active_addrs"][addr]

                removed_role = None
                for client in stats["clients_info"][:]:
                    if client["ip"] == addr[0] and client["port"] == addr[1]:
                        removed_role = client["role"]
                        stats["clients_info"].remove(client)
                        break

                if removed_role == "ADMIN":
                    admin_addr = None
                    if stats["clients_info"]:
                        first_client = stats["clients_info"][0]
                        first_client["role"] = "ADMIN"
                        first_client["permissions"] = ["read", "write", "execute"]
                        admin_addr = (first_client["ip"], first_client["port"])

            stats["active_connections"] = len(stats["active_addrs"])


def log_message_for_stats(addr, message):
    with lock:
        stats["total_messages"] += 1
        stats["messages"].append({
            "ip": addr[0],
            "port": addr[1],
            "message": message,
            "time": now_str()
        })

        # për të mos u bërë shumë i madh
        if len(stats["messages"]) > 100:
            stats["messages"] = stats["messages"][-100:]


def list_files():
    files = os.listdir(SERVER_DIR)
    if not files:
        return "Nuk ka file ne server."
    return "\n".join(files)


def read_file(filename):
    filename = safe_filename(filename)
    if not filename:
        return "Emri i file-it nuk eshte valid."

    path = os.path.join(SERVER_DIR, filename)
    if not os.path.exists(path):
        return "Skedari nuk u gjet."

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return content if content else "[File bosh]"
    except Exception:
        return "Skedari nuk mund te lexohet si tekst."


def search_files(keyword):
    files = os.listdir(SERVER_DIR)
    matched = [f for f in files if keyword.lower() in f.lower()]
    if not matched:
        return "Nuk u gjet asnje file."
    return "\n".join(matched)