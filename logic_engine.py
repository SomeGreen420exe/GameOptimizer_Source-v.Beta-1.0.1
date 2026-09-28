import re

KNOWN_GPUS = {
    "HD 7850": 800, "GTX 660": 800, "GTX 750": 900, "GTX 760": 1200,
    "RX 460": 1600, "GTX 970": 2300, "GTX 1060": 2500, "RX 580": 2500,
    "GTX 1650": 2700, "GTX 1070": 3800, "GTX 1080": 5000, "RTX 2060": 5500,
    "RX 5700": 6000, "RTX 3060": 6500, "RTX 2070": 6800, "RX 6600": 7200,
    "RTX 3070": 8500, "RTX 4060": 9200, "RX 7700": 10000, "RTX 4070": 11800,
    "RX 7800": 12200, "RTX 5070": 15000
}

KNOWN_CPUS = {
    "i3-4130": 3600, "FX-6300": 3600, "i5-2500K": 4500, 
    "i5-8400": 6800, "Ryzen 5 1600": 6800, "i7-7700K": 8100, 
    "Ryzen 5 2600": 8100, "Ryzen 5 3600": 11000, "i7-9700K": 13500, 
    "Ryzen 7 3700X": 14400, "i5-12400": 18000, "Ryzen 5 5600X": 18900, 
    "i7-12700K": 24800, "Ryzen 7 8700F": 26000, "Ryzen 7 7800X3D": 27000
}

KNOWN_FEATURE_GAMES = {
    "dlss": [
        "cyberpunk", "witcher 3", "spider-man", "spiderman", "crimson desert", 
        "alan wake 2", "black myth", "red dead redemption 2", "god of war", 
        "horizon", "dying light 2", "starfield", "hogwarts legacy", 
        "flight simulator", "diablo iv", "call of duty", "battlefield"
    ],
    "fg": [
        "cyberpunk", "witcher 3", "spider-man", "spiderman", "crimson desert", 
        "alan wake 2", "black myth", "starfield", "hogwarts legacy", 
        "flight simulator", "diablo iv", "ghost of tsushima", "dragon's dogma 2",
        "dying light 2"
    ],
    "rt": [
        "cyberpunk", "witcher 3", "spider-man", "spiderman", "crimson desert", 
        "alan wake 2", "black myth", "dying light 2", "hogwarts legacy", 
        "control", "metro exodus", "doom eternal", "resident evil"
    ]
}

def parse_gpu_requirement(requirement_text):
    found_score = 0 
    text_lower = requirement_text.lower()
    
    for gpu, score in KNOWN_GPUS.items():
        if gpu.lower() in text_lower:
            if score > found_score:
                found_score = score
                
    if found_score == 0:
        if "rtx 4090" in text_lower: found_score = 35000
        elif "rtx 4080" in text_lower: found_score = 32000
        elif "rtx 3080" in text_lower: found_score = 15000
        elif "rtx 2080" in text_lower: found_score = 10000
        elif "gtx 1080" in text_lower: found_score = 5000
        
    return 2000 if found_score == 0 else found_score

def parse_cpu_requirement(requirement_text):
    found_score = 0
    text_lower = requirement_text.lower()
    
    for cpu, score in KNOWN_CPUS.items():
        if cpu.lower() in text_lower:
            if score > found_score:
                found_score = score
                
    if found_score == 0:
        if "i9" in text_lower or "ryzen 9" in text_lower: found_score = 24800
        elif "i7" in text_lower or "ryzen 7" in text_lower: found_score = 13500
        elif "i5" in text_lower or "ryzen 5" in text_lower: found_score = 6800
        elif "i3" in text_lower or "ryzen 3" in text_lower: found_score = 3600
        
    return 4000 if found_score == 0 else found_score

def parse_ram_requirement(requirement_text):
    match = re.search(r'(\d+)\s*GB', requirement_text, re.IGNORECASE)
    if match:
        gb_amount = int(match.group(1))
        return gb_amount * 140 
    return 1000

def get_equivalent_gpu(score):
    if score <= 0:
        return "Unknown"
    return min(KNOWN_GPUS.keys(), key=lambda k: abs(KNOWN_GPUS[k] - score))

def get_equivalent_cpu(score):
    if score <= 0:
        return "Unknown"
    return min(KNOWN_CPUS.keys(), key=lambda k: abs(KNOWN_CPUS[k] - score))

def get_equivalent_ram(score):
    if score <= 0:
        return "Unknown"
    gb = int(score / 140)
    return f"{gb} GB"

def calculate_exact_requirements(gpu_rec, cpu_rec, ram_rec, game_name=""):
    game_name_lower = game_name.lower()
    
    has_dlss = any(g in game_name_lower for g in KNOWN_FEATURE_GAMES["dlss"])
    has_fg = any(g in game_name_lower for g in KNOWN_FEATURE_GAMES["fg"])
    
    perf_gpu_mult = 0.65 if has_dlss else 0.75
    perf_cpu_mult = 0.80
    perf_ram_mult = 0.75
    
    ultra_gpu_mult = 1.45 if has_fg else 1.85
    ultra_cpu_mult = 1.15
    ultra_ram_mult = 1.25
    
    def round_score(val):
        return max(100, int(round(val / 100.0) * 100))
        
    perf_reqs = (round_score(gpu_rec * perf_gpu_mult), round_score(cpu_rec * perf_cpu_mult), round_score(ram_rec * perf_ram_mult))
    bal_reqs = (round_score(gpu_rec), round_score(cpu_rec), round_score(ram_rec))
    ultra_reqs = (round_score(gpu_rec * ultra_gpu_mult), round_score(cpu_rec * ultra_cpu_mult), round_score(ram_rec * ultra_ram_mult))
    
    return {
        "1. Performance": perf_reqs,
        "2. Balanced": bal_reqs,
        "3. Maximum Ultra": ultra_reqs
    }

def generate_three_tiers(performance_ratio, req_text, gpu_name, game_gpu_req=0, game_name=""):
    profiles = {}
    
    hw_has_rtx = "RTX" in gpu_name
    hw_has_framegen = "RTX 4" in gpu_name or "RTX 5" in gpu_name
    
    game_name_lower = game_name.lower()
    text_lower = req_text.lower()
    
    game_supports_dlss = any(g in game_name_lower for g in KNOWN_FEATURE_GAMES["dlss"])
    game_supports_fg = any(g in game_name_lower for g in KNOWN_FEATURE_GAMES["fg"])
    game_supports_rt = any(g in game_name_lower for g in KNOWN_FEATURE_GAMES["rt"])
    
    if not game_supports_dlss and ("dlss" in text_lower or "rtx" in text_lower):
        game_supports_dlss = True
    if not game_supports_fg and ("frame gen" in text_lower or "dlss 3" in text_lower or "fsr 3" in text_lower):
        game_supports_fg = True
    if not game_supports_rt and ("ray tracing" in text_lower or "raytracing" in text_lower):
        game_supports_rt = True
        
    if game_gpu_req >= 5000:
        game_is_modern = True
    elif game_gpu_req > 0 and game_gpu_req <= 3000:
        game_is_modern = False
    else:
        modern_keywords = ["directx 12", "version 12", "dx12", "ray tracing", "dlss", "rtx", "fsr"]
        game_is_modern = any(keyword in text_lower for keyword in modern_keywords)
        
    can_use_dlss = hw_has_rtx and game_supports_dlss
    can_use_rt = hw_has_rtx and game_supports_rt
    can_use_fg = hw_has_framegen and game_supports_fg
    
    # ---------------------------------------------------------
    # NEW DYNAMIC FPS CALCULATION ENGINE (Data-driven calibration)
    # ---------------------------------------------------------
    
    is_esports = any(g in game_name_lower for g in ["counter-strike", "cs 2", "cs2", "rocket league", "valorant", "league of legends", "dota 2"])
    
    if is_esports:
        # Esports curve: Uncapped non-linear scaling tailored for extremely high framerates
        # E.g., Ratio 5.8 -> ~266 Base FPS
        base_fps = 85.0 * (performance_ratio ** 0.65)
        
        perf_fps = base_fps * 1.05
        bal_fps  = base_fps * 0.85
        max_fps  = base_fps * 0.75
    else:
        # AAA curve: Standard scaling below 1.0, steady progression above 1.0
        if performance_ratio <= 1.0:
            base_fps = 60.0 * performance_ratio
        else:
            base_fps = 60.0 + 40.0 * (performance_ratio - 1.0)
            
        # Frame Generation provides roughly a 75% boost on modern cards
        fg_mult = 1.75 if can_use_fg else 1.0
        
        perf_fps = base_fps * 1.30 * fg_mult
        bal_fps  = base_fps * 1.00 * fg_mult
        max_fps  = base_fps * 0.75 * fg_mult

    def format_fps(fps, tier_desc):
        if fps < 15:
            return f"~{int(fps)} - {int(fps) + 5} FPS (UNPLAYABLE)"
        elif fps < 30:
            return f"~{int(fps)} - {int(fps) + 10} FPS (Very Poor / Stuttering)"
        elif fps < 60:
            return f"~{int(fps)} - {int(fps) + 10} FPS (Console-like)"
        elif fps < 150:
            return f"~{int(fps)} - {int(fps) + 15} FPS ({tier_desc})"
        else:
            # Broaden the variance window for very high framerates (e.g. 260 - 300 FPS)
            return f"~{int(fps)} - {int(fps) + 40} FPS ({tier_desc})"

    # ==========================================
    # GAME SPECIFIC TEMPLATES
    # ==========================================

    # 1. COUNTER-STRIKE 2 (Source 2 Engine)
    if "counter-strike" in game_name_lower or "cs 2" in game_name_lower or "cs2" in game_name_lower:
        profiles["1. PERFORMANCE (High FPS)"] = {
            "Target Resolution": "1080p (Native) or 4:3 Stretched",
            "Multisampling Anti-Aliasing Mode": "None" if performance_ratio < 0.8 else "2x MSAA",
            "Global Shadow Quality": "Low",
            "Dynamic Shadows": "Sun Only",
            "Texture Filtering Mode": "Bilinear",
            "Shader Quality": "Low",
            "Particle Detail": "Low",
            "High Dynamic Range (HDR)": "Performance",
            "FidelityFX Super Resolution (FSR)": "Performance" if performance_ratio < 0.7 else "Disabled (Highest Quality)",
            "Estimated FPS": format_fps(perf_fps, "Competitive Esports")
        }
        profiles["2. BALANCED (Visuals & FPS)"] = {
            "Target Resolution": "1440p (Native) or 1080p",
            "Multisampling Anti-Aliasing Mode": "4x MSAA" if performance_ratio >= 1.0 else "2x MSAA",
            "Global Shadow Quality": "Medium",
            "Dynamic Shadows": "All",
            "Texture Filtering Mode": "Trilinear",
            "Shader Quality": "High",
            "Particle Detail": "Medium",
            "High Dynamic Range (HDR)": "Quality",
            "FidelityFX Super Resolution (FSR)": "Disabled (Highest Quality)",
            "Estimated FPS": format_fps(bal_fps, "Ideal Balance")
        }
        profiles["3. MAXIMUM QUALITY (Ultra)"] = {
            "Target Resolution": "4K or 1440p",
            "Multisampling Anti-Aliasing Mode": "8x MSAA",
            "Global Shadow Quality": "High",
            "Dynamic Shadows": "All",
            "Texture Filtering Mode": "Anisotropic 16x",
            "Shader Quality": "High",
            "Particle Detail": "High",
            "High Dynamic Range (HDR)": "Quality",
            "FidelityFX Super Resolution (FSR)": "Disabled (Highest Quality)",
            "Estimated FPS": format_fps(max_fps, "Maximum Fidelity")
        }
        return profiles

    # 2. CRIMSON DESERT (Next-Gen Open World)
    elif "crimson desert" in game_name_lower:
        profiles["1. PERFORMANCE (High FPS)"] = {
            "Target Resolution": "1080p" if performance_ratio >= 0.7 else "720p",
            "Lighting Quality": "Low",
            "Effect Quality": "Low",
            "Water Quality": "Low",
            "Raytracing": "Disabled",
            "Anti-Aliasing": "DLSS (Performance)" if can_use_dlss else "FSR (Performance)",
            "Frame Generation": "Enabled" if can_use_fg else "Disabled",
            "Estimated FPS": format_fps(perf_fps, "Smooth Action")
        }
        profiles["2. BALANCED (Visuals & FPS)"] = {
            "Target Resolution": "1440p" if performance_ratio >= 1.2 else "1080p",
            "Lighting Quality": "Medium" if performance_ratio >= 1.0 else "Low",
            "Effect Quality": "Medium",
            "Water Quality": "Medium",
            "Raytracing": "Medium" if can_use_rt and performance_ratio >= 1.2 else "Disabled",
            "Anti-Aliasing": "DLSS (Balanced)" if can_use_dlss else "FSR (Quality)",
            "Frame Generation": "Enabled" if can_use_fg else "Disabled",
            "Estimated FPS": format_fps(bal_fps, "Ideal Balance")
        }
        profiles["3. MAXIMUM QUALITY (Ultra)"] = {
            "Target Resolution": "4K" if performance_ratio >= 1.8 else "1440p",
            "Lighting Quality": "Ultra",
            "Effect Quality": "Ultra",
            "Water Quality": "Ultra",
            "Raytracing": "Ultra" if can_use_rt else "Disabled",
            "Anti-Aliasing": "DLSS (Quality)" if can_use_dlss else "TAA (Maximum)",
            "Frame Generation": "Enabled" if can_use_fg else "Disabled",
            "Estimated FPS": format_fps(max_fps, "Cinematic Ultra")
        }
        return profiles
        
    # 3. ROCKET LEAGUE (Unreal Engine 3)
    elif "rocket league" in game_name_lower:
        profiles["1. PERFORMANCE (High FPS)"] = {
            "Target Resolution": "1080p",
            "Render Quality": "Performance",
            "Render Detail": "Performance",
            "Anti-Aliasing": "Off",
            "Texture Detail": "High Performance",
            "World Detail": "Performance",
            "High Quality Shaders": "Disabled",
            "Estimated FPS": format_fps(perf_fps, "Max Refresh Rate")
        }
        profiles["2. BALANCED (Visuals & FPS)"] = {
            "Target Resolution": "1440p" if performance_ratio >= 0.8 else "1080p",
            "Render Quality": "Quality",
            "Render Detail": "Custom",
            "Anti-Aliasing": "FXAA Low",
            "Texture Detail": "Quality",
            "World Detail": "Quality",
            "High Quality Shaders": "Enabled",
            "Estimated FPS": format_fps(bal_fps, "Smooth Aerials")
        }
        profiles["3. MAXIMUM QUALITY (Ultra)"] = {
            "Target Resolution": "4K" if performance_ratio >= 1.0 else "1440p",
            "Render Quality": "High Quality",
            "Render Detail": "High Quality",
            "Anti-Aliasing": "MLAA",
            "Texture Detail": "High Quality",
            "World Detail": "High Quality",
            "High Quality Shaders": "Enabled",
            "Estimated FPS": format_fps(max_fps, "Max Fidelity")
        }
        return profiles

    # ==========================================
    # FALLBACK: GENERIC MODERN GAME TEMPLATE
    # ==========================================
    
    profiles["1. PERFORMANCE (High FPS)"] = {
        "Target Resolution": "1080p (1920x1080)" if performance_ratio >= 0.7 else "720p or lower (FSR Ultra Perf)",
        "Global Preset": "Medium / Optimized" if performance_ratio >= 0.8 else "Absolute Lowest",
        "Texture Quality": "High" if performance_ratio >= 0.8 else "Lowest",
        "Shadow Quality": "Medium" if performance_ratio >= 0.8 else "Disabled / Lowest",
        "Volumetric Fog/Clouds": "Low" if performance_ratio >= 0.8 else "Disabled",
        "Anti-Aliasing": "DLSS (Performance Mode)" if can_use_dlss else ("TAA" if performance_ratio >= 0.6 else "Off"),
        "Ray Tracing": "Disabled",
        "Frame Generation": "Enabled" if can_use_fg else "Disabled",
        "Estimated FPS": format_fps(perf_fps, "Ultra Smooth")
    }
    
    profiles["2. BALANCED (Visuals & FPS)"] = {
        "Target Resolution": "1440p (2560x1440)" if performance_ratio >= 1.2 else ("1080p" if performance_ratio >= 0.8 else "720p"),
        "Global Preset": "High" if performance_ratio >= 1.0 else ("Medium" if performance_ratio >= 0.8 else "Low"),
        "Texture Quality": "High" if performance_ratio >= 1.0 else ("Medium" if performance_ratio >= 0.8 else "Low"),
        "Shadow Quality": "High" if performance_ratio >= 1.0 else ("Medium" if performance_ratio >= 0.8 else "Low"),
        "Volumetric Fog/Clouds": "Medium" if performance_ratio >= 1.0 else ("Low" if performance_ratio >= 0.8 else "Disabled"),
        "Anti-Aliasing": "DLSS (Balanced Mode)" if can_use_dlss else "TAA",
        "Ray Tracing": "Enabled (Medium)" if can_use_rt and performance_ratio >= 1.2 else "Not Supported / Off",
        "Frame Generation": "Off",
        "Estimated FPS": format_fps(bal_fps, "Ideal Balance")
    }
    
    profiles["3. MAXIMUM QUALITY (Ultra)"] = {
        "Target Resolution": "4K (3840x2160)" if performance_ratio >= 1.8 else ("1440p" if performance_ratio >= 1.2 else "1080p"),
        "Global Preset": "Ultra" if performance_ratio >= 1.0 else ("High" if performance_ratio >= 0.8 else "Medium"),
        "Texture Quality": "Ultra" if performance_ratio >= 1.0 else ("High" if performance_ratio >= 0.8 else "Medium"),
        "Shadow Quality": "Ultra" if performance_ratio >= 1.0 else ("High" if performance_ratio >= 0.8 else "Medium"),
        "Volumetric Fog/Clouds": "High" if performance_ratio >= 1.0 else ("Medium" if performance_ratio >= 0.8 else "Low"),
        "Anti-Aliasing": "DLSS (Quality Mode)" if can_use_dlss else "TAA (Maximum)",
        "Ray Tracing": "Enabled (High/Max)" if can_use_rt and performance_ratio >= 1.0 else "Not Supported / Off",
        "Frame Generation": "Enabled" if can_use_fg else "Disabled",
        "Estimated FPS": format_fps(max_fps, "Cinematic Ultra")
    }
    
    return profiles

def evaluate_hardware(user_gpu_score, user_cpu_score, user_ram_score, game_gpu_req, game_cpu_req, game_ram_req, req_text="", gpu_name="Unknown GPU", game_name=""):
    gpu_ratio = user_gpu_score / max(1, game_gpu_req)
    cpu_ratio = user_cpu_score / max(1, game_cpu_req)
    ram_ratio = user_ram_score / max(1, game_ram_req)
    
    performance_ratio = gpu_ratio
    
    if cpu_ratio < gpu_ratio * 0.75 and cpu_ratio < 1.0:
        bottleneck_penalty = (cpu_ratio / (gpu_ratio * 0.75)) ** 0.5
        performance_ratio *= max(0.65, bottleneck_penalty) 
        
    if ram_ratio < 0.8:
        performance_ratio *= 0.8
        
    three_tiers = generate_three_tiers(performance_ratio, req_text, gpu_name=gpu_name, game_gpu_req=game_gpu_req, game_name=game_name)
    return three_tiers