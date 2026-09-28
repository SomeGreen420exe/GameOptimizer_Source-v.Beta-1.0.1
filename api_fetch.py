import requests
import re

# Insert your free API key from rawg.io here
RAWG_API_KEY = "cbfdbd6d4bba4fb4a9a50741dde81b53"

def fetch_game_requirements(game_name):
    """
    Fetches hardware requirements.
    1. PRIMARY: Tries Steam API first (fast and requires no auth).
    2. FALLBACK: Uses RAWG API for Epic exclusives or missing Steam games.
    """
    
    # ==========================================
    # 1. PRIMARY: STEAM API
    # ==========================================
    try:
        steam_search_url = f"https://steamcommunity.com/actions/SearchApps/{game_name}"
        steam_search_resp = requests.get(steam_search_url, timeout=4)
        
        if steam_search_resp.status_code == 200:
            search_data = steam_search_resp.json()
            if search_data and len(search_data) > 0:
                app_id = search_data[0].get("appid")
                
                if app_id:
                    details_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
                    details_resp = requests.get(details_url, timeout=4)
                    
                    if details_resp.status_code == 200:
                        app_details = details_resp.json().get(str(app_id), {}).get("data", {})
                        pc_reqs = app_details.get("pc_requirements", {})
                        
                        reqs = {"minimum": "", "recommended": ""}
                        if isinstance(pc_reqs, dict) and pc_reqs:
                            reqs["minimum"] = str(pc_reqs.get("minimum", ""))
                            reqs["recommended"] = str(pc_reqs.get("recommended", ""))
                            
                            # Clean HTML tags and return if Steam has the data
                            if reqs["minimum"] or reqs["recommended"]:
                                reqs["minimum"] = re.sub(r'<[^>]+>', ' ', reqs["minimum"])
                                reqs["recommended"] = re.sub(r'<[^>]+>', ' ', reqs["recommended"])
                                return reqs
    except Exception as e:
        print(f"Steam fetch failed: {e}")

    # ==========================================
    # 2. FALLBACK: RAWG API
    # ==========================================
    if RAWG_API_KEY and RAWG_API_KEY != "YOUR_API_KEY_HERE":
        try:
            rawg_search_url = f"https://api.rawg.io/api/games?key={RAWG_API_KEY}&search={game_name}&page_size=1"
            rawg_search_resp = requests.get(rawg_search_url, timeout=5)
            
            if rawg_search_resp.status_code == 200:
                rawg_search_data = rawg_search_resp.json()
                
                if rawg_search_data.get("results"):
                    game_slug = rawg_search_data["results"][0]["slug"]
                    details_url = f"https://api.rawg.io/api/games/{game_slug}?key={RAWG_API_KEY}"
                    details_resp = requests.get(details_url, timeout=5)
                    
                    if details_resp.status_code == 200:
                        details_data = details_resp.json()
                        requirements = {"minimum": "", "recommended": ""}
                        
                        platforms = details_data.get("platforms", [])
                        for plat in platforms:
                            platform_info = plat.get("platform", {})
                            if platform_info.get("name") == "PC":
                                reqs = plat.get("requirements", {})
                                if isinstance(reqs, dict) and reqs:
                                    requirements["minimum"] = str(reqs.get("minimum", ""))
                                    requirements["recommended"] = str(reqs.get("recommended", ""))
                                break
                                
                        # Generic fallback if no detailed text is present on RAWG
                        if not requirements["minimum"] and not requirements["recommended"]:
                            requirements["minimum"] = "Requires a 64-bit processor and operating system"
                            
                        return requirements
        except Exception as e:
            print(f"RAWG fallback fetch failed: {e}")

    return None