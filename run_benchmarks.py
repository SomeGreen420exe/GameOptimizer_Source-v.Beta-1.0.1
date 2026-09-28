import json
import time
import sys
import os

from cpu_benchmark import run_sustained_multicore_benchmark
from ram_benchmark import run_advanced_ram_benchmark
from disk_benchmark import run_storage_benchmark
from gpu_benchmark import run_real_gpu_benchmark

def run_gui_benchmarks():
    print("PROGRESS: Initializing benchmarks... | PCT: 0", flush=True)
    time.sleep(0.5)
    
    # Load existing cache to preserve scores of skipped benchmarks
    results = {"cpu_score": 0, "ram_score": 0, "disk_score": 0, "gpu_score": 0}
    if os.path.exists("benchmark_cache.json"):
        try:
            with open("benchmark_cache.json", "r") as f:
                data = json.load(f)
                results.update(data)
        except Exception:
            pass
            
    run_cpu = "--run-cpu" in sys.argv
    run_ram = "--run-ram" in sys.argv
    run_disk = "--run-disk" in sys.argv
    run_gpu = "--run-gpu" in sys.argv
    
    total_tasks = sum([run_cpu, run_ram, run_disk, run_gpu])
    
    if total_tasks == 0:
        print("PROGRESS: No benchmarks selected! | PCT: 100", flush=True)
        return
        
    completed = 0
    
    if run_cpu:
        print(f"PROGRESS: Testing CPU (Floating Point Math) | PCT: {int((completed/total_tasks)*100)}", flush=True)
        score, _ = run_sustained_multicore_benchmark()
        results["cpu_score"] = score
        completed += 1
        
    if run_ram:
        print(f"PROGRESS: Testing RAM (Allocation & Bandwidth) | PCT: {int((completed/total_tasks)*100)}", flush=True)
        score, _ = run_advanced_ram_benchmark()
        results["ram_score"] = score
        completed += 1
        
    if run_disk:
        print(f"PROGRESS: Testing Storage (Sequential R/W) | PCT: {int((completed/total_tasks)*100)}", flush=True)
        score, _ = run_storage_benchmark()
        results["disk_score"] = score
        completed += 1
        
    if run_gpu:
        print(f"PROGRESS: Testing GPU (3D Rendering) | PCT: {int((completed/total_tasks)*100)}", flush=True)
        try:
            results["gpu_score"], _ = run_real_gpu_benchmark()
        except Exception as e:
            print(f"GPU benchmark failed: {e}", file=sys.stderr, flush=True)
            raise SystemExit(2) from e
        completed += 1
    
    print("PROGRESS: Finalizing results... | PCT: 98", flush=True)
    
    with open("benchmark_cache.json", "w") as f:
        json.dump(results, f)
        
    print("PROGRESS: Done! | PCT: 100", flush=True)

if __name__ == "__main__":
    run_gui_benchmarks()