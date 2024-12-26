import sys
import time
import threading

def display_progress_fixed(chunk_progress, num_chunks):
    """
    Hiển thị tiến độ tải của các chunk trên 4 dòng cố định và cập nhật động.

    Args:
        chunk_progress (list): Danh sách phần trăm tiến độ của từng chunk.
        num_chunks (int): Số lượng chunk của file.
    """
    # In các dòng khởi tạo
    for chunk_id in range(num_chunks):
        sys.stdout.write(f"Chunk {chunk_id + 1}: {chunk_progress[chunk_id]}%\n")
    sys.stdout.flush()

    while not all(progress == 100 for progress in chunk_progress):
        # Di chuyển con trỏ lên `num_chunks` dòng
        sys.stdout.write(f"\033[{num_chunks}A")
        sys.stdout.flush()

        # Cập nhật phần trăm của từng chunk
        for chunk_id in range(num_chunks):
            sys.stdout.write(f"Chunk {chunk_id + 1}: {chunk_progress[chunk_id]}%\n")
        sys.stdout.flush()

        time.sleep(0.1)  # Chờ một chút trước lần cập nhật tiếp theo

    # In dòng hoàn thành
    sys.stdout.write(f"\033[{num_chunks}A")
    for chunk_id in range(num_chunks):
        sys.stdout.write(f"Chunk {chunk_id + 1}: 100%\n")
    sys.stdout.write("All chunks downloaded successfully!\n")
    sys.stdout.flush()

def simulate_chunk_download(chunk_id, chunk_progress):
    """
    Mô phỏng quá trình tải một chunk.
    """
    for i in range(101):
        time.sleep(0.05)  # Mô phỏng thời gian tải
        chunk_progress[chunk_id] = i

# Số lượng chunk tải song song
num_chunks = 4
chunk_progress = [0] * num_chunks

# Tạo và khởi chạy các thread mô phỏng tải
threads = []
for chunk_id in range(num_chunks):
    thread = threading.Thread(target=simulate_chunk_download, args=(chunk_id, chunk_progress))
    threads.append(thread)
    thread.start()

# Hiển thị tiến độ tải
display_progress_fixed(chunk_progress, num_chunks)

# Chờ các thread hoàn tất
for thread in threads:
    thread.join()
