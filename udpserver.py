import socket
import threading
import os
import time
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

IP = '0.0.0.0'
PORT = 12060
HTTP_PORT = 9090
MAX_CLIENTS = 5
BUFFER_SIZE = 4096
TIMEOUT = 200
SERVER_DIR = "server_files"

if not os.path.exists(SERVER_DIR):
    os.makedirs(SERVER_DIR)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((IP, PORT))

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
        time.sleep(1)
        current_time = time.time()

        with lock:
            inactive_clients = [
                addr for addr, last_seen in stats["active_addrs"].items()
                if current_time - last_seen > TIMEOUT
            ]

            for addr in inactive_clients:
                print(f"Lidhja u mbyll automatikisht për {addr} (Inaktivitet).")
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

def get_file_info(filename):
    filename = safe_filename(filename)
    if not filename:
        return "Emri i file-it nuk eshte valid."

    path = os.path.join(SERVER_DIR, filename)
    if not os.path.exists(path):
        return "Skedari nuk u gjet."

    size = os.path.getsize(path)
    created = datetime.fromtimestamp(os.path.getctime(path)).strftime('%Y-%m-%d %H:%M:%S')
    modified = datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S')
    return f"Size: {size} bytes | Created: {created} | Modified: {modified}"


def delete_file(filename):
    filename = safe_filename(filename)
    if not filename:
        return "Emri i file-it nuk eshte valid."

    path = os.path.join(SERVER_DIR, filename)
    if not os.path.exists(path):
        return "Skedari nuk u gjet."

    os.remove(path)
    return f"Skedari '{filename}' u fshi me sukses."


def receive_upload(filename, addr):
    filename = safe_filename(filename)
    if not filename:
        return "Emri i file-it nuk eshte valid."

    path = os.path.join(SERVER_DIR, filename)

    with open(path, "wb") as f:
        while True:
            data, sender_addr = server_socket.recvfrom(BUFFER_SIZE)

            if sender_addr != addr:
                continue

            if b"<END>" in data:
                f.write(data.replace(b"<END>", b""))
                break

            f.write(data)

    return f"Upload i file-it '{filename}' perfundoi me sukses."


def send_download(filename, addr):
    filename = safe_filename(filename)
    if not filename:
        server_socket.sendto(b"ERROR: Emri i file-it nuk eshte valid.<END>", addr)
        return

    path = os.path.join(SERVER_DIR, filename)
    if not os.path.exists(path):
        server_socket.sendto(b"ERROR: Skedari nuk u gjet.<END>", addr)
        return

    with open(path, "rb") as f:
        while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                break
            server_socket.sendto(chunk, addr)

    server_socket.sendto(b"<END>", addr)


class StatsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/stats":
            with lock:

                response = {
                    "active_connections": stats["active_connections"],
                    "ip_addresses": [f"{c['ip']}:{c['port']}" for c in stats["clients_info"]],
                    "total_messages": stats["total_messages"],
                    "clients_info": stats["clients_info"],
                    "messages": stats["messages"]
                }


            response_data = json.dumps(response, indent=4).encode('utf-8')


            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_data)))


            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_header("Refresh", "2")

            self.end_headers()
            self.wfile.write(response_data)
        else:

            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 - Faqja nuk u gjet. Perdorni /stats")

    def log_message(self, format, *args):
        return


def start_http_server():
    http_server = HTTPServer((IP, HTTP_PORT), StatsHandler)
    print(f"Monitorimi: http://localhost:{HTTP_PORT}/stats")
    http_server.serve_forever()


def handle_command(message, addr):
    parts = message.split()
    if not parts:
        return "Komande e pavlefshme."

    cmd = parts[0].lower()

    user_allowed = ["/list", "/read", "/search"]


    if not is_admin(addr):
        if cmd not in user_allowed:
            return "ERROR: Ju keni vetem read permission."
        time.sleep(1)


    if cmd == "/list":
        return list_files()

    elif cmd == "/read" and len(parts) > 1:
        return read_file(parts[1])

    elif cmd == "/search" and len(parts) > 1:
        return search_files(parts[1])


    elif cmd == "/upload" and len(parts) > 1:
        server_socket.sendto(b"READY", addr)
        return receive_upload(parts[1], addr)

    elif cmd == "/download" and len(parts) > 1:
        send_download(parts[1], addr)
        return None

    elif cmd == "/delete" and len(parts) > 1:
        return delete_file(parts[1])

    elif cmd == "/info" and len(parts) > 1:
        return get_file_info(parts[1])


    elif not cmd.startswith("/"):
        return f"Mesazhi u pranua nga serveri: {message}"

    else:
        return "Komande e panjohur ose format i gabuar."


def start_server():
    print(f"UDP Serveri u startua ne {IP}:{PORT}")
    print("Klienti i pare qe lidhet do te behet ADMIN.")

    threading.Thread(target=remove_inactive_clients, daemon=True).start()
    threading.Thread(target=start_http_server, daemon=True).start()

    while True:
        data, addr = server_socket.recvfrom(BUFFER_SIZE)
        message = data.decode(errors="ignore").strip()

        allowed, info_msg = register_or_update_client(addr)
        if not allowed:
            server_socket.sendto(info_msg.encode(), addr)
            continue

        log_message_for_stats(addr, message)
        print(f"[{addr[0]}:{addr[1]}] -> {message}")

        response = handle_command(message, addr)

        if response is not None:
            server_socket.sendto(response.encode(), addr)


if __name__ == "__main__":
    start_server()