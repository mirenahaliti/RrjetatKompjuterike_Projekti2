import socket
import os

SERVER_IP = '192.168.0.24'  # ndrysho sipas IP të serverit
SERVER_PORT = 12009
BUFFER_SIZE = 4096


def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        msg = input("Shkruaj komanden: ")

        if msg.lower() == "exit":
            break

        parts = msg.split()
        cmd = parts[0].lower()

        # UPLOAD
        if cmd == "/upload" and len(parts) > 1:
            if os.path.exists(parts[1]):
                client.sendto(msg.encode(), (SERVER_IP, SERVER_PORT))
                resp, _ = client.recvfrom(BUFFER_SIZE)

                if resp == b"READY":
                    with open(parts[1], "rb") as f:
                        while True:
                            chunk = f.read(BUFFER_SIZE)
                            if not chunk:
                                break
                            client.sendto(chunk, (SERVER_IP, SERVER_PORT))
                    client.sendto(b"<END>", (SERVER_IP, SERVER_PORT))

                    resp, _ = client.recvfrom(BUFFER_SIZE)
                    print(resp.decode())
            else:
                print("File nuk ekziston")

        # DOWNLOAD
        elif cmd == "/download" and len(parts) > 1:
            client.sendto(msg.encode(), (SERVER_IP, SERVER_PORT))
            with open(f"marre_{parts[1]}", "wb") as f:
                while True:
                    data, _ = client.recvfrom(BUFFER_SIZE)
                    if b"<END>" in data:
                        f.write(data.replace(b"<END>", b""))
                        break
                    f.write(data)
            print("Download perfundoi")

        else:
            client.sendto(msg.encode(), (SERVER_IP, SERVER_PORT))
            data, _ = client.recvfrom(BUFFER_SIZE)
            print("SERVER:", data.decode())


if __name__ == "__main__":
    start_client()