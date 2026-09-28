import math
import psutil
import cpuinfo
import GPUtil

def get_pc_specs():
    # 1. RAM Detection
    ram_bytes = psutil.virtual_memory().total
    ram_gb = math.ceil(ram_bytes / (1024**3))
    
    # 2. CPU Detection
    cpu_name = cpuinfo.get_cpu_info()['brand_raw']
    
    # 3. GPU and VRAM Detection
    gpus = GPUtil.getGPUs()
    
    if gpus:
        gpu = gpus[0] 
        gpu_name = gpu.name
        vram_gb = math.ceil(gpu.memoryTotal / 1024)
    else:
        gpu_name = "No dedicated GPU found"
        vram_gb = 0

    return {
        "CPU": cpu_name,
        "RAM": ram_gb,
        "GPU": gpu_name,
        "VRAM": vram_gb
    }

if __name__ == "__main__":
    print("Scanning hardware...")
    specs = get_pc_specs()
    
    print("-" * 40)
    print("HARDWARE DETECTION RESULT:")
    print("-" * 40)
    print(f"CPU:  {specs['CPU']}")
    print(f"RAM:  {specs['RAM']} GB")
    print(f"GPU:  {specs['GPU']}")
    print(f"VRAM: {specs['VRAM']} GB")
    print("-" * 40)