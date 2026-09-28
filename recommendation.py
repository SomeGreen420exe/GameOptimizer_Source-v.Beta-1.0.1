import re

def parse_gpu_requirement(requirement_text):
    known_gpus = {
        "HD 7850": 2000, "GTX 660": 2000, "GTX 750": 2200, "GTX 760": 3000,
        "RX 460": 4000, "GTX 970": 5500, "GTX 1060": 6000, "RX 580": 6000,
        "GTX 1650": 6500, "GTX 1070": 9000, "GTX 1080": 12000, "RTX 2060": 13000,
        "RX 5700": 14000, "RTX 3060": 15000, "RTX 2070": 16000, "RX 6600": 17000,
        "RTX 3070": 20000, "RTX 4060": 22000, "RX 7700": 24000, "RTX 4070": 28000,
        "RX 7800": 29000, "RTX 5070": 35000
    }
    found_score = 0 
    for gpu, score in known_gpus.items():
        if gpu in requirement_text:
            if score > found_score:
                found_score = score
    return 5000 if found_score == 0 else found_score

def parse_cpu_requirement(requirement_text):
    known_cpus = {
        "i3-4130": 8000, "FX-6300": 8000, "i5-2500K": 10000, 
        "i5-8400": 15000, "Ryzen 5 1600": 15000, "i7-7700K": 18000, 
        "Ryzen 5 2600": 18000, "Ryzen 5 3600": 25000, "i7-9700K": 30000, 
        "Ryzen 7 3700X": 32000, "i5-12400": 40000, "Ryzen 5 5600X": 42000, 
        "i7-12700K": 55000, "Ryzen 7 8700F": 57000, "Ryzen 7 7800X3D": 60000
    }
    found_score = 0
    for cpu, score in known_cpus.items():
        if cpu in requirement_text:
            if score > found_score:
                found_score = score
    return 10000 if found_score == 0 else found_score

def parse_ram_requirement(requirement_text):
    match = re.search(r'(\d+)\s*GB', requirement_text, re.IGNORECASE)
    if match:
        gb_amount = int(match.group(1))
        return gb_amount * 250
    return 2000

def generate_detailed_settings(performance_ratio, req_text, gpu_name="RTX 5070"):
    settings = {}
    
    # 1. Hardware capabilities
    hw_has_rtx = "RTX" in gpu_name
    hw_has_framegen = "RTX 4" in gpu_name or "RTX 5" in gpu_name
    
    # 2. Game Engine capabilities (Strict detection)
    text_lower = req_text.lower()
    modern_keywords = ["directx 12", "version 12", "dx12", "ray tracing", "dlss", "rtx"]
    game_is_modern = any(keyword in text_lower for keyword in modern_keywords)
    
    # DEBUG PRINT: This will explicitly tell us what the script sees
    print(f"\n [ DEBUG ] Modern Engine Detected: {game_is_modern}")
    
    can_use_dlss = hw_has_rtx and game_is_modern
    can_use_rt = hw_has_rtx and game_is_modern
    can_use_fg = hw_has_framegen and game_is_modern
    
    if performance_ratio >= 2.0:
        settings["Target Resolution"] = "4K (3840x2160)" if can_use_dlss else "1440p (2560x1440)"
        settings["Global Preset"] = "Ultra"
        settings["Texture Quality"] = "Ultra"
        settings["Shadow Quality"] = "Ultra"
        settings["Volumetric Fog/Clouds"] = "High"
        settings["Anti-Aliasing"] = "DLSS (Quality Mode)" if can_use_dlss else "TAA (High)"
        settings["Ray Tracing"] = "Enabled (High/Max)" if can_use_rt else "Not Supported / Off"
        settings["Frame Generation"] = "Enabled" if can_use_fg else "Not Supported / Off"
        
    elif performance_ratio >= 1.2:
        settings["Target Resolution"] = "1440p (2560x1440)"
        settings["Global Preset"] = "High"
        settings["Texture Quality"] = "High"
        settings["Shadow Quality"] = "High"
        settings["Volumetric Fog/Clouds"] = "Medium"
        settings["Anti-Aliasing"] = "DLSS (Balanced Mode)" if can_use_dlss else "TAA (High)"
        settings["Ray Tracing"] = "Enabled (Medium)" if can_use_rt else "Not Supported / Off"
        settings["Frame Generation"] = "Off"
        
    elif performance_ratio >= 0.8:
        settings["Target Resolution"] = "1080p (1920x1080)"
        settings["Global Preset"] = "Medium"
        settings["Texture Quality"] = "Medium"
        settings["Shadow Quality"] = "Medium"
        settings["Volumetric Fog/Clouds"] = "Low"
        settings["Anti-Aliasing"] = "DLSS (Performance Mode)" if can_use_dlss else "FXAA / TAA"
        settings["Ray Tracing"] = "Disabled"
        settings["Frame Generation"] = "Off"
        
    else:
        settings["Target Resolution"] = "1080p (1920x1080)"
        settings["Global Preset"] = "Low / Performance"
        settings["Texture Quality"] = "Low"
        settings["Shadow Quality"] = "Low"
        settings["Volumetric Fog/Clouds"] = "Low"
        settings["Anti-Aliasing"] = "Off"
        settings["Ray Tracing"] = "Disabled"
        settings["Frame Generation"] = "Off"
        
    return settings

def evaluate_hardware(user_gpu_score, game_req_score, req_text=""):
    performance_ratio = user_gpu_score / game_req_score
    detailed_settings = generate_detailed_settings(performance_ratio, req_text)
    return detailed_settings