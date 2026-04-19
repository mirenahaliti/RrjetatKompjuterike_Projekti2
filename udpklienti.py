import socket
import os
import time
import threading
SERVER_IP = '172.16.109.215'
SERVER_PORT = 12030
BUFFER_SIZE = 4096

last_activity_time = time.time()
def check_timeout():
    global last_activity_time
    while True:
        time.sleep(1)
        if time.time() - last_activity_time > 200:
            print("\nLidhja me serverin ka skaduar.")
            print("Shkruani diçka për t'u ri-lidhur automatikisht: ", end="", flush=True)
            last_activity_time = time.time()

def start_client():
    global last_activity_time
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(200)

    threading.Thread(target=check_timeout, daemon=True).start()

    print("Klienti u startua.")
    print("Komandat:")
    print("/list")
    print("/read emri.txt")
    print("/search fjala")
    print("/upload emri.txt")
    print("/download emri.txt")
    print("/delete emri.txt")
    print("/info emri.txt")
    print("Mund te dergosh edhe tekst normal si mesazh.")
    print("Per dalje shkruaj: exit")
    print()
    while True:
        try:
            msg = input("Shkruaj komanden ose mesazhin: ").strip()

            if not msg:
                continue
            if msg.lower() == "exit":
                break

            parts = msg.split()
            cmd = parts[0].lower()

            # UPLOAD
            if cmd == "/upload" and len(parts) > 1:
                filename = parts[1]
                if not os.path.exists(filename):
                    print("File nuk ekziston ne kompjuterin tend.")
                    continue

                client_socket.sendto(msg.encode(), (SERVER_IP, SERVER_PORT))
                resp, _ = client_socket.recvfrom(BUFFER_SIZE)

                if resp == b"READY":
                    with open(filename, "rb") as f:
                        while True:
                            chunk = f.read(BUFFER_SIZE)
                            if not chunk:
                                break
                            client_socket.sendto(chunk, (SERVER_IP, SERVER_PORT))

                    client_socket.sendto(b"<END>", (SERVER_IP, SERVER_PORT))
                    final_resp, _ = client_socket.recvfrom(BUFFER_SIZE)
                    print("SERVER:", final_resp.decode())
                else:
                    print("SERVER:", resp.decode())

            # DOWNLOAD
            elif cmd == "/download" and len(parts) > 1:
                filename = parts[1]
                client_socket.sendto(msg.encode(), (SERVER_IP, SERVER_PORT))

                with open(f"marre_{filename}", "wb") as f:
                    while True:
                        data, _ = client_socket.recvfrom(BUFFER_SIZE)
                        if b"ERROR:" in data and b"<END>" in data:
                            print("SERVER:", data.replace(b"<END>", b"").decode())
                            f.close()
                            os.remove(f"marre_{filename}")
                            break
                        if b"<END>" in data:
                            f.write(data.replace(b"<END>", b""))
                            print(f"Download perfundoi. File u ruajt si marre_{filename}")
                            break
                        f.write(data)


            else:
                client_socket.sendto(msg.encode(), (SERVER_IP, SERVER_PORT))
                data, _ = client_socket.recvfrom(BUFFER_SIZE)
                print("SERVER:", data.decode())


        except socket.timeout:
            print("\nLidhja me serverin ka skaduar ose serveri është i mbyllur.")
            print("Provoni të dërgoni një mesazh përsëri për t'u ri-lidhur automatikisht.\n")
        except Exception as e:
            print(f"Ndodhi një gabim: {e}")

    client_socket.close()


if __name__ == "__main__":
    start_client()
