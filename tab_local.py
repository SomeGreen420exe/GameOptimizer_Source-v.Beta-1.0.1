import os
import threading
import json
import glob
import re
import customtkinter as ctk

try:
    import winreg
except ImportError:
    winreg = None

class LocalGamesTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.local_info_lbl = ctk.CTkLabel(self, text="Scan your PC for installed Steam and Epic Games titles.\nThis process is 100% local and safe. No data is sent to the internet.", text_color=("gray40", "gray70"))
        self.local_info_lbl.grid(row=0, column=0, pady=(15, 10))

        self.scan_local_btn = ctk.CTkButton(self, text="Scan for local games", height=40, font=ctk.CTkFont(weight="bold"), command=self.start_local_scan)
        self.scan_local_btn.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")

        self.local_games_scroll = ctk.CTkScrollableFrame(self, fg_color=("gray85", "gray17"))
        self.local_games_scroll.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.local_games_scroll.grid_columnconfigure(0, weight=1)

    def start_local_scan(self):
        self.scan_local_btn.configure(state="disabled", text="Scanning your drives...")
        for widget in self.local_games_scroll.winfo_children():
            widget.destroy()
        threading.Thread(target=self.scan_local_games_thread, daemon=True).start()

    def scan_local_games_thread(self):
        games = set()

        # 1. STEAM
        if winreg:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam") as key:
                    steam_path = winreg.QueryValueEx(key, "InstallPath")[0]

                library_vdf = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
                library_paths = [steam_path]

                if os.path.exists(library_vdf):
                    with open(library_vdf, "r", encoding="utf-8") as f:
                        content = f.read()
                        paths = re.findall(r'"path"\s+"([^"]+)"', content, re.IGNORECASE)
                        for p in paths:
                            clean_path = p.replace("\\\\", "\\")
                            if clean_path not in library_paths:
                                library_paths.append(clean_path)

                for lib in library_paths:
                    acf_path = os.path.join(lib, "steamapps", "*.acf")
                    for acf_file in glob.glob(acf_path):
                        try:
                            with open(acf_file, "r", encoding="utf-8") as f:
                                acf_content = f.read()
                                name_match = re.search(r'"name"\s+"([^"]+)"', acf_content, re.IGNORECASE)
                                if name_match:
                                    game_name = name_match.group(1)
                                    if all(x not in game_name for x in ["Steamworks", "Proton", "Redistributable"]):
                                        games.add(game_name)
                        except:
                            pass
            except Exception:
                pass

        # 2. EPIC GAMES
        try:
            epic_manifests_path = r"C:\ProgramData\Epic\EpicGamesLauncher\Data\Manifests"
            if os.path.exists(epic_manifests_path):
                for item_file in glob.glob(os.path.join(epic_manifests_path, "*.item")):
                    try:
                        with open(item_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            app_name = data.get("DisplayName", "")
                            if app_name:
                                games.add(app_name)
                    except:
                        pass
        except Exception:
            pass

        sorted_games = sorted(list(games))
        self.after(0, lambda: self.update_local_games_ui(sorted_games))

    def update_local_games_ui(self, games):
        self.scan_local_btn.configure(state="normal", text="Scan for local games")
        
        if not games:
            lbl = ctk.CTkLabel(self.local_games_scroll, text="No local Steam or Epic Games found.", text_color="gray")
            lbl.pack(pady=20)
            return

        for game_name in games:
            btn = ctk.CTkButton(
                self.local_games_scroll, 
                text=f"🎮  {game_name}", 
                anchor="w",
                fg_color=("gray92", "gray20"), 
                text_color=("black", "white"),
                hover_color=("gray85", "gray25"), 
                height=35,
                command=lambda name=game_name: self.launch_local_game(name)
            )
            btn.pack(fill="x", pady=3, padx=5)

    def launch_local_game(self, game_name):
        self.app.launch_search_for_game(game_name)