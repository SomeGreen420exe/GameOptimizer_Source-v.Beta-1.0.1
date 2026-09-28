import time
import multiprocessing
import threading

def cpu_worker(ramp_duration, sustain_duration):
    start_time = time.time()
    total_duration = ramp_duration + sustain_duration
    score = 0
    
    # PURE 100% STRESS - No sleeping allowed. 
    # Forces the CPU's Floating Point Unit to work continuously.
    while True:
        current_time = time.time()
        elapsed = current_time - start_time
        
        if elapsed >= total_duration:
            break
            
        # Heavy mathematical loop (prevents Python from idling)
        temp = 0.0
        for i in range(1, 100000):
            temp += (i * 3.14159265359) ** 0.5
            
        # Only record score during the sustain phase, ignore the warm-up
        if elapsed >= ramp_duration:
            score += 1
            
    return score

def progress_monitor(duration, stop_event, task_name):
    start = time.time()
    while not stop_event.is_set():
        elapsed = time.time() - start
        pct = min(100, int((elapsed / duration) * 100))
        print(f"PROGRESS: {task_name} | PCT: {pct}", flush=True)
        if elapsed >= duration:
            break
        time.sleep(0.5)

def run_sustained_multicore_benchmark():
    start_time = time.time()
    
    # Detect all logical processors (e.g., 16 threads on Ryzen 7 8700F)
    cores = multiprocessing.cpu_count()
    
    # 5 seconds warm-up, 15 seconds hardcore benchmark
    ramp_duration = 5.0
    sustain_duration = 15.0
    total_duration = ramp_duration + sustain_duration
    
    stop_event = threading.Event()
    monitor = threading.Thread(target=progress_monitor, args=(total_duration, stop_event, "CPU Stress Test"))
    monitor.start()
    
    total_work = 0
    
    # Launch worker on absolutely every available thread
    with multiprocessing.Pool(cores) as pool:
        workload = [(ramp_duration, sustain_duration) for _ in range(cores)]
        results = pool.starmap(cpu_worker, workload)
        total_work += sum(results)
        
    stop_event.set()
    monitor.join()
            
    end_time = time.time()
    duration = end_time - start_time
    
    # Calculate final score based on operations completed per second
    work_per_sec = total_work / sustain_duration
    
    # Calibrated multiplier to place modern CPUs (like Ryzen 8700F) 
    # in the correct ~25000+ points bracket
    final_score = int(work_per_sec * 22) 
    
    if final_score < 2000:
        final_score = 2000
        
    return final_score, duration

if __name__ == "__main__":
    multiprocessing.freeze_support()
    score, time_taken = run_sustained_multicore_benchmark()
    print(f"Score: {score} pts in {time_taken:.2f}s")