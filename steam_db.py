import requests

def get_dynamic_app_id(game_name):
    print(f"Searching Steam store for '{game_name}'...")
    
    # Steam Store Search API (Public, no API key required)
    url = "https://store.steampowered.com/api/storesearch/"
    params = {
        "term": game_name,
        "l": "english",
        "cc": "US"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        items = data.get("items", [])
        if not items:
            return None
            
        # The search returns a list of matches, we take the most relevant one (the first)
        best_match = items[0]
        found_id = best_match.get("id")
        found_name = best_match.get("name")
        
        print(f"Match found on Steam: '{found_name}'")
        return found_id
        
    except requests.exceptions.RequestException as error:
        print(f"Steam Search API Error: {error}")
        return None

if __name__ == "__main__":
    # Test it out with Cyberpunk 2077
    target_game = "Cyberpunk 2077"
    
    print("-" * 50)
    found_id = get_dynamic_app_id(target_game)
    
    if found_id:
        print(f"Success! AppID for '{target_game}': {found_id}")
    else:
        print(f"Game '{target_game}' could not be found.")
    print("-" * 50)