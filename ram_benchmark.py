import time
import threading
import os
import ctypes

def progress_monitor(duration, stop_event, task_name):
    start = time.time()
    while not stop_event.is_set():
        elapsed = time.time() - start
        pct = min(100, int((elapsed / duration) * 100))
        print(f"PROGRESS: {task_name} | PCT: {pct}", flush=True)
        if elapsed >= duration:
            break
        time.sleep(0.5)

def get_available_memory_mb():
    try:
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return int(stat.ullAvailPhys / (1024 * 1024))
    except Exception:
        # Fallback if ctypes fails
        return 4096 

def run_advanced_ram_benchmark():
    start_time = time.time()
    memory_hog = []
    
    ramp_duration = 10.0
    sustain_duration = 15.0 
    total_duration = ramp_duration + sustain_duration
    
    stop_event = threading.Event()
    monitor = threading.Thread(target=progress_monitor, args=(total_duration, stop_event, "RAM Allocation & Bandwidth"))
    monitor.start()
    
    # Target 50% of currently available free RAM, safe limit up to 12GB
    avail_mb = get_available_memory_mb()
    target_mb = min(int(avail_mb * 0.5), 12288) 
    
    if target_mb < 1024:
        target_mb = 1024
        
    chunk_size_mb = 128
    chunk_size_bytes = chunk_size_mb * 1024 * 1024 
    max_chunks = target_mb // chunk_size_mb
    
    base_data = os.urandom(chunk_size_bytes)
    ramp_start = time.time()
    
    # Phase 1: Aggressive Memory Allocation
    while True:
        elapsed = time.time() - ramp_start
        if elapsed >= ramp_duration:
            break
            
        if len(memory_hog) < max_chunks:
            try:
                memory_hog.append(bytearray(base_data))
            except MemoryError:
                break
            
        time.sleep(0.05)
        
    # Phase 2: Memory Bandwidth (Strided Read/Write to defeat CPU Cache)
    sustain_start = time.time()
    operations_count = 0
    actual_chunks = len(memory_hog)
    
    if actual_chunks == 0:
        stop_event.set()
        monitor.join()
        return 1500, time.time() - start_time
    
    while True:
        elapsed = time.time() - sustain_start
        if elapsed >= sustain_duration:
            break
            
        for i in range(actual_chunks):
            if time.time() - sustain_start >= sustain_duration:
                break
            
            half = chunk_size_bytes // 2
            quarter = chunk_size_bytes // 4
            
            # Cross-block moving forces raw bandwidth usage
            memory_hog[i][:quarter] = memory_hog[i][half:half+quarter]
            memory_hog[i][-quarter:] = memory_hog[i][quarter:quarter*2]
            
            operations_count += 1
            
    # Cleanup memory aggressively
    del memory_hog
    base_data = None
    stop_event.set()
    monitor.join()
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Operations move half a chunk (64MB) per iteration
    total_mb_moved = operations_count * (chunk_size_mb // 2)
    mb_per_sec = total_mb_moved / sustain_duration
    
    # Heavy capacity scaling: big bonus for systems able to handle deep allocation
    final_score = int(mb_per_sec * 0.45) + (actual_chunks * 25)
    
    if final_score < 2500:
        final_score = 2500 + int(mb_per_sec * 0.1)
        
    return final_score, duration

if __name__ == "__main__":
    score, time_taken = run_advanced_ram_benchmark()
    print(f"RAM Score: {score} pts in {time_taken:.2f}s")