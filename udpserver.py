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
