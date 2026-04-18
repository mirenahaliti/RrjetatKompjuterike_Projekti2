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