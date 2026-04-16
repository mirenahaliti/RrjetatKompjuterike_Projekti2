import socket
import os

SERVER_IP = '192.168.0.24'   # ndrysho sipas IP te serverit
SERVER_PORT = 12009
BUFFER_SIZE = 4096


def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print("Klienti u startua.")
    print("Shkruaj komanda si:")
    print("/list")
    print("/read emri.txt")
    print("/search fjala")
    print("/download emri.txt")
    print("/upload emri.txt")
    print("/delete emri.txt")
    print("/info emri.txt")
    print("Per dalje shkruaj: exit")
    print()

    while True:
        msg = input("Shkruaj komanden: ").strip()

        if not msg:
            continue

        if msg.lower() == "exit":
            break

        parts = msg.split()
        cmd = parts[0].lower()

        # UPLOAD
        if cmd == "/upload" and len(parts) > 1:
            filename = parts[1]

            if os.path.exists(filename):
                client.sendto(msg.encode(), (SERVER_IP, SERVER_PORT))
                resp, _ = client.recvfrom(BUFFER_SIZE)

                if resp == b"READY":
                    with open(filename, "rb") as f:
                        while True:
                            chunk = f.read(BUFFER_SIZE)
                            if not chunk:
                                break
                            client.sendto(chunk, (SERVER_IP, SERVER_PORT))

                    client.sendto(b"<END>", (SERVER_IP, SERVER_PORT))

                    resp, _ = client.recvfrom(BUFFER_SIZE)
                    print("SERVER:", resp.decode())
                else:
                    print("SERVER:", resp.decode())

            else:
                print("File nuk ekziston.")

        # DOWNLOAD
        elif cmd == "/download" and len(parts) > 1:
            filename = parts[1]
            client.sendto(msg.encode(), (SERVER_IP, SERVER_PORT))

            with open(f"marre_{filename}", "wb") as f:
                while True:
                    data, _ = client.recvfrom(BUFFER_SIZE)

                    if b"ERROR:" in data and b"<END>" in data:
                        print("SERVER:", data.replace(b"<END>", b"").decode())
                        f.close()
                        os.remove(f"marre_{filename}")
                        break

                    if b"<END>" in data:
                        f.write(data.replace(b"<END>", b""))
                        print("Download perfundoi.")
                        break

                    f.write(data)

        # KOMANDA TJERA
        else:
            client.sendto(msg.encode(), (SERVER_IP, SERVER_PORT))
            data, _ = client.recvfrom(BUFFER_SIZE)
            print("SERVER:", data.decode())

    client.close()


if __name__ == "__main__":
    start_client()