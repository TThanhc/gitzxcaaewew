import socket
# import time
import threading
import hashlib
import os
import time
from threading import Thread
import sys
def get_file_size_from_string(file_list_str, file_name):
    # Tách chuỗi thành danh sách các dòng
    lines = file_list_str.splitlines()
    
    for line in lines:
        # Bỏ qua dòng tiêu đề "List of files:"
        if line.startswith("List of files:"):
            continue
        
        # Tách tên file và kích thước
        if " - " in line:
            name, size = line.split(" - ")
            if name.strip() == file_name:
                # Loại bỏ đơn vị MB và chuyển thành số
                size_in_mb = float(size.replace(" MB", "").strip())
                return size_in_mb
    
    return None  # Không tìm thấy file


dir_path = r"UDP\test_file"
file_list = [
            f"{f} - {(os.path.getsize(os.path.join(dir_path, f)) / (1024 * 1024))} MB"
            for f in os.listdir(dir_path)
            if os.path.isfile(os.path.join(dir_path, f))
        ]

file_list_str = "List of files:\n" + "\n".join(file_list)
print(file_list_str)

# Ví dụ sử dụng
file_name = "100MB.bin"
size = get_file_size_from_string(file_list_str, file_name)
if size is not None:
    print(f"The size of '{file_name}' is {size} MB.")
else:
    print(f"File '{file_name}' not found.")
