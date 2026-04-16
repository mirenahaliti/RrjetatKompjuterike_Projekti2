import socket
import threading
import os
import time
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

# KONFIGURIMET
IP = '192.168.0.24'   # ndryshoje sipas IP-se se serverit
PORT = 12009
HTTP_PORT = 8080
MAX_CLIENTS = 4
BUFFER_SIZE = 4096
SERVER_DIR = "server_files"
TIMEOUT = 60

if not os.path.exists(SERVER_DIR):
    os.makedirs(SERVER_DIR)

# Socket global
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((IP, PORT))

# Statistikat
stats = {
    "active_connections": 0,
    "total_messages": 0,
    "clients_info": [],
    "active_addrs": {}
}

admin_addr = None
lock = threading.Lock()


def get_file_info(filename):
    path = os.path.join(SERVER_DIR, filename)
    if os.path.exists(path):
        size = os.path.getsize(path)
        ctime = datetime.fromtimestamp(os.path.getctime(path)).strftime('%Y-%m-%d %H:%M:%S')
        return f"Size: {size} bytes, Created: {ctime}"
    return "Skedari nuk u gjet."


def is_admin(addr):
    return addr == admin_addr


def update_client_activity(addr):
    global admin_addr

    with lock:
        current_time = time.time()

        if addr not in stats["active_addrs"]:
            if len(stats["active_addrs"]) >= MAX_CLIENTS:
                return False, "Serveri eshte plot. Nuk lejohen me shume kliente."

            stats["active_addrs"][addr] = current_time
            stats["active_connections"] = len(stats["active_addrs"])

            role = "ADMIN" if admin_addr is None else "USER"
            if admin_addr is None:
                admin_addr = addr

            stats["clients_info"].append({
                "ip": addr[0],
                "port": addr[1],
                "role": role,
                "last_seen": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            stats["active_addrs"][addr] = current_time

            for client in stats["clients_info"]:
                if client["ip"] == addr[0] and client["port"] == addr[1]:
                    client["last_seen"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    break

    return True, "OK"


def remove_inactive_clients():
    global admin_addr

    while True:
        time.sleep(5)
        now = time.time()

        with lock:
            inactive = []
            for addr, last_time in stats["active_addrs"].items():
                if now - last_time > TIMEOUT:
                    inactive.append(addr)

            for addr in inactive:
                del stats["active_addrs"][addr]

                for client in stats["clients_info"][:]:
                    if client["ip"] == addr[0] and client["port"] == addr[1]:
                        removed_role = client["role"]
                        stats["clients_info"].remove(client)

                        if removed_role == "ADMIN":
                            admin_addr = None
                            if stats["clients_info"]:
                                first_client = stats["clients_info"][0]
                                first_client["role"] = "ADMIN"
                                admin_addr = (first_client["ip"], first_client["port"])
                        break

            stats["active_connections"] = len(stats["active_addrs"])


def list_files():
    files = os.listdir(SERVER_DIR)
    if not files:
        return "Nuk ka file ne server."
    return "\n".join(files)


def read_file(filename):
    path = os.path.join(SERVER_DIR, filename)
    if not os.path.exists(path):
        return "Skedari nuk u gjet."

    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "Skedari nuk mund te lexohet si tekst."


def search_files(keyword):
    files = os.listdir(SERVER_DIR)
    matched = [f for f in files if keyword.lower() in f.lower()]
    if not matched:
        return "Nuk u gjet asnje file."
    return "\n".join(matched)


def delete_file(filename):
    path = os.path.join(SERVER_DIR, filename)
    if not os.path.exists(path):
        return "Skedari nuk u gjet."

    os.remove(path)
    return f"Skedari '{filename}' u fshi me sukses."


def receive_upload(filename, addr):
    path = os.path.join(SERVER_DIR, os.path.basename(filename))

    with open(path, "wb") as f:
        while True:
            data, sender_addr = server.recvfrom(BUFFER_SIZE)

            # Siguri minimale: prano vetem nga i njejti klient
            if sender_addr != addr:
                continue

            if b"<END>" in data:
                f.write(data.replace(b"<END>", b""))
                break

            f.write(data)

    return f"Upload i file-it '{filename}' perfundoi me sukses."


def send_download(filename, addr):
    path = os.path.join(SERVER_DIR, filename)

    if not os.path.exists(path):
        server.sendto(b"ERROR: Skedari nuk u gjet.<END>", addr)
        return

    with open(path, "rb") as f:
        while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                break
            server.sendto(chunk, addr)

    server.sendto(b"<END>", addr)


class StatsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/stats":
            with lock:
                response = {
                    "active_connections": stats["active_connections"],
                    "total_messages": stats["total_messages"],
                    "clients_info": stats["clients_info"]
                }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=4).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return


def start_http_server():
    http_server = HTTPServer((IP, HTTP_PORT), StatsHandler)
    print(f"HTTP monitorimi u startua ne http://{IP}:{HTTP_PORT}/stats")
    http_server.serve_forever()


def handle_command(message, addr):
    global admin_addr

    parts = message.split()
    if not parts:
        return "Komande e pavlefshme."

    cmd = parts[0].lower()

    # KOMANDAT PER TE GJITHE
    if cmd == "/list":
        return list_files()

    elif cmd == "/read" and len(parts) > 1:
        return read_file(parts[1])

    elif cmd == "/search" and len(parts) > 1:
        return search_files(parts[1])

    elif cmd == "/download" and len(parts) > 1:
        send_download(parts[1], addr)
        return None

    # KOMANDAT VETEM PER ADMIN
    elif cmd == "/upload" and len(parts) > 1:
        if not is_admin(addr):
            return "ERROR: Vetem ADMIN mund te beje upload."

        server.sendto(b"READY", addr)
        result = receive_upload(parts[1], addr)
        return result

    elif cmd == "/delete" and len(parts) > 1:
        if not is_admin(addr):
            return "ERROR: Vetem ADMIN mund te fshije file."

        return delete_file(parts[1])

    elif cmd == "/info" and len(parts) > 1:
        if not is_admin(addr):
            return "ERROR: Vetem ADMIN mund te shohe info."

        return get_file_info(parts[1])

    else:
        return "Komande e panjohur ose format i gabuar."


def start_server():
    print(f"UDP Serveri u startua ne {IP}:{PORT}")
    print("Klienti i pare qe lidhet do te behet ADMIN.")

    threading.Thread(target=remove_inactive_clients, daemon=True).start()
    threading.Thread(target=start_http_server, daemon=True).start()

    while True:
        data, addr = server.recvfrom(BUFFER_SIZE)
        message = data.decode(errors="ignore").strip()

        allowed, msg = update_client_activity(addr)
        if not allowed:
            server.sendto(msg.encode(), addr)
            continue

        with lock:
            stats["total_messages"] += 1

        print(f"[{addr[0]}:{addr[1]}] -> {message}")

        response = handle_command(message, addr)

        if response is not None:
            server.sendto(response.encode(), addr)


if __name__ == "__main__":
    start_server()
