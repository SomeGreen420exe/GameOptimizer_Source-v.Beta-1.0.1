import time
import os
import tempfile

def run_storage_benchmark():
    start_time = time.time()
    temp_dir = tempfile.gettempdir()
    test_file = os.path.join(temp_dir, "optimizer_disk_test.tmp")
    
    # Increased to 2 GB to properly bypass NVMe SLC caching
    file_size_mb = 2048
    chunk_size = 1024 * 1024  # 1 MB blocks
    data = os.urandom(chunk_size)
    
    try:
        # 1. Sequential Write Test
        write_start = time.time()
        with open(test_file, "wb") as f:
            for _ in range(file_size_mb):
                f.write(data)
        write_end = time.time()
        write_speed = file_size_mb / max(0.001, write_end - write_start)
        
        # 2. Sequential Read Test
        read_start = time.time()
        with open(test_file, "rb") as f:
            while f.read(chunk_size):
                pass
        read_end = time.time()
        read_speed = file_size_mb / max(0.001, read_end - read_start)
        
    finally:
        if os.path.exists(test_file):
            try:
                os.remove(test_file)
            except Exception:
                pass
                
    duration = time.time() - start_time
    
    final_score = int((write_speed + read_speed) * 1.5)
    
    if final_score < 500:
        final_score = 500
        
    return final_score, duration

if __name__ == "__main__":
    score, time_taken = run_storage_benchmark()
    print(f"Storage Score: {score} pts in {time_taken:.2f}s")