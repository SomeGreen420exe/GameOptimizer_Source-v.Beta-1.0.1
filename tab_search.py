import threading
import requests
import io
import re
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from PIL import Image

from ui_widgets import ToolTip
from api_fetch import fetch_game_requirements, RAWG_API_KEY
from logic_engine import (
    parse_gpu_requirement, parse_cpu_requirement, parse_ram_requirement, 
    evaluate_hardware, get_equivalent_gpu, get_equivalent_cpu, get_equivalent_ram,
    calculate_exact_requirements
)

from image_exporter import export_results_to_image

class SearchOptimizeTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        
        self.last_tested_game = ""
        self.last_estimated_fps = ""
        self.last_logo_data = None
        self.last_profiles = None
        self.current_game_reqs = None
        self.search_timer = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self.create_widgets()

    def create_widgets(self):
        self.search_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        self.search_frame.grid_columnconfigure(0, weight=1)

        self.game_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Enter game name (e.g. Cyberpunk 2077)...", height=40)
        self.game_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ToolTip(self.game_entry, "Type a game name to fetch live requirements from Steam/RAWG and predict performance.")
        
        self.game_entry.bind("<Return>", lambda event: self.optimize_game())
        self.game_entry.bind("<KeyRelease>", self.on_key_release)
        self.game_entry.bind("<FocusOut>", self.delayed_hide_suggestions)

        self.search_btn = ctk.CTkButton(self.search_frame, text="Optimize", width=120, height=40, command=self.optimize_game)
        self.search_btn.grid(row=0, column=1, sticky="e")
        ToolTip(self.search_btn, "Fetch requirements and calculate custom settings profiles.")

        self.game_header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.game_header_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        
        self.game_image_label = ctk.CTkLabel(self.game_header_frame, text="", width=120, height=45, fg_color=("gray85", "gray15"), corner_radius=4)
        self.game_image_label.pack(side="left", padx=(0, 15))
        ToolTip(self.game_image_label, "Official game capsule artwork.")
        
        self.game_title_label = ctk.CTkLabel(self.game_header_frame, text="Ready to optimize...", font=ctk.CTkFont(size=22, weight="bold"))
        self.game_title_label.pack(side="left")
        ToolTip(self.game_title_label, "Currently active game title being analyzed.")
        
        self.game_source_badge = ctk.CTkLabel(self.game_header_frame, text="", fg_color="transparent", corner_radius=6, font=ctk.CTkFont(size=11, weight="bold"))
        self.game_source_badge.pack(side="left", padx=(15, 0))

        self.suggestion_frame = ctk.CTkFrame(
            self, 
            fg_color=("gray95", "#121212"), 
            corner_radius=4, 
            border_width=1, 
            border_color=("gray75", "#333333")
        )

        self.info_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray20"))
        self.info_frame.grid(row=2, column=0, sticky="ew", pady=(0, 5))
        self.info_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.req_gpu_label = ctk.CTkLabel(self.info_frame, text="Req GPU: --", font=ctk.CTkFont(size=13, weight="bold"), fg_color="transparent")
        self.req_gpu_label.grid(row=0, column=0, padx=10, pady=10)
        ToolTip(self.req_gpu_label, "The exact GPU score required to run this game comfortably at 1080p Balanced settings.")

        self.req_cpu_label = ctk.CTkLabel(self.info_frame, text="Req CPU: --", font=ctk.CTkFont(size=13, weight="bold"), fg_color="transparent")
        self.req_cpu_label.grid(row=0, column=1, padx=10, pady=10)
        ToolTip(self.req_cpu_label, "The exact CPU score required to prevent bottlenecking in this game.")

        self.req_ram_label = ctk.CTkLabel(self.info_frame, text="Req RAM: --", font=ctk.CTkFont(size=13, weight="bold"), fg_color="transparent")
        self.req_ram_label.grid(row=0, column=2, padx=10, pady=10)
        ToolTip(self.req_ram_label, "The exact RAM score (capacity) needed for a smooth experience without virtual memory paging.")
        
        self.bottleneck_label = ctk.CTkLabel(self, text="", text_color="orange", font=ctk.CTkFont(size=12, weight="bold"))
        self.bottleneck_label.grid(row=3, column=0, pady=(0, 5))

        self.profiles_tabview = ctk.CTkTabview(self, command=self.on_tab_change)
        self.profiles_tabview.grid(row=4, column=0, sticky="nsew")

        self.tab_perf = self.profiles_tabview.add("1. Performance")
        self.tab_bal = self.profiles_tabview.add("2. Balanced")
        self.tab_max = self.profiles_tabview.add("3. Maximum Ultra")

        self.setup_tier_tab(self.tab_perf, "Performance profile awaiting game selection...")
        self.setup_tier_tab(self.tab_bal, "Balanced profile awaiting game selection...")
        self.setup_tier_tab(self.tab_max, "Maximum profile awaiting game selection...")
        
        self.share_btn = ctk.CTkButton(self, text="📸 Export as Image Matrix", width=200, fg_color="#27ae60", hover_color="#2ecc71", text_color="white", command=self.save_as_image)
        self.share_btn.grid(row=5, column=0, pady=(10, 0), sticky="e")
        ToolTip(self.share_btn, "Generates a complete side-by-side settings matrix for all profiles as an image.")

    def save_as_image(self):
        try:
            if not self.last_tested_game or not self.last_profiles:
                messagebox.showinfo("Info", "Please optimize a game first before generating an image report.", parent=self.app)
                return
                
            safe_name = "".join(c for c in self.last_tested_game if c.isalnum() or c in " -_").strip()
            default_filename = f"{safe_name}_Full_Matrix.png" if safe_name else "Optimization_Matrix.png"
                
            filepath = filedialog.asksaveasfilename(
                parent=self.app,
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png")],
                title="Save Matrix Report As...",
                initialfile=default_filename
            )
            
            if not filepath:
                return 
                
            scores = {
                'cpu': self.app.cpu_score,
                'gpu': self.app.gpu_score,
                'ram': self.app.ram_score
            }
                
            export_results_to_image(
                filepath=filepath,
                app_specs=self.app.actual_specs,
                scores=scores,
                game_name=self.last_tested_game,
                logo_data=self.last_logo_data,
                profiles_data=self.last_profiles
            )
            messagebox.showinfo("Success", f"Optimization Matrix successfully generated and saved to:\n{filepath}", parent=self.app)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate image matrix:\n{str(e)}", parent=self.app)

    def update_game_header(self, title, img_data, source=None):
        self.game_title_label.configure(text=title)
        if img_data:
            try:
                image = Image.open(io.BytesIO(img_data))
                ctk_img = ctk.CTkImage(light_image=image, dark_image=image, size=(120, 45))
                self.game_image_label.configure(image=ctk_img, text="")
            except Exception:
                self.game_image_label.configure(image=None, text="No Image")
        else:
            self.game_image_label.configure(image=None, text="No Image")

        if source == "Steam":
            self.game_source_badge.configure(text="  STEAM  ", fg_color=("#d1d5db", "#1b2838"), text_color=("#111827", "#c7d5e0"))
        elif source == "RAWG":
            self.game_source_badge.configure(text="  RAWG  ", fg_color=("#d1d5db", "#212121"), text_color=("#111827", "#ffffff"))
        else:
            self.game_source_badge.configure(text="", fg_color="transparent")

    def on_key_release(self, event):
        if event.keysym in ['Up', 'Down', 'Return', 'Escape', 'Tab']:
            return
        if self.search_timer:
            self.after_cancel(self.search_timer)
        self.search_timer = self.after(350, self.trigger_suggestion_fetch)

    def trigger_suggestion_fetch(self):
        query = self.game_entry.get().strip()
        if len(query) < 3:
            self.suggestion_frame.place_forget()
            return
        threading.Thread(target=self.fetch_suggestions_thread, args=(query,), daemon=True).start()

    def fetch_suggestions_thread(self, query):
        results = []
        
        try:
            url = f"https://steamcommunity.com/actions/SearchApps/{query}"
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                data = resp.json()[:5] 
                for item in data:
                    name = item.get("name")
                    logo_url = item.get("logo")
                    img_data = None
                    if logo_url:
                        try:
                            img_resp = requests.get(logo_url, timeout=2)
                            if img_resp.status_code == 200:
                                img_data = img_resp.content
                        except:
                            pass
                    results.append((name, img_data, "Steam"))
        except Exception:
            pass

        if not results and RAWG_API_KEY and RAWG_API_KEY != "YOUR_API_KEY_HERE":
            try:
                rawg_url = f"https://api.rawg.io/api/games?key={RAWG_API_KEY}&search={query}&page_size=5"
                resp = requests.get(rawg_url, timeout=4)
                if resp.status_code == 200:
                    data = resp.json().get("results", [])
                    for item in data:
                        name = item.get("name")
                        logo_url = item.get("background_image")
                        img_data = None
                        if logo_url:
                            try:
                                img_resp = requests.get(logo_url, timeout=2)
                                if img_resp.status_code == 200:
                                    img_data = img_resp.content
                            except:
                                pass
                        results.append((name, img_data, "RAWG"))
            except Exception:
                pass
                
        self.after(0, lambda: self.update_suggestions_ui(results))

    def update_suggestions_ui(self, results):
        for widget in self.suggestion_frame.winfo_children():
            widget.destroy()
            
        if not results:
            self.suggestion_frame.place_forget()
            return
            
        entry_width = self.game_entry.winfo_width()
        
        def bind_events(widget, enter_fn, leave_fn, click_fn):
            widget.bind("<Enter>", enter_fn)
            widget.bind("<Leave>", leave_fn)
            widget.bind("<Button-1>", click_fn)

        for name, img_data, source in results:
            def create_row_closure(n, img, src):
                row = ctk.CTkFrame(self.suggestion_frame, fg_color="transparent", corner_radius=0, height=45, width=entry_width - 2)
                row.pack_propagate(False)
                row.pack(fill="x", padx=1, pady=0)
                
                def on_enter(e): row.configure(fg_color=("gray85", "#2a2a2a"))
                def on_leave(e): row.configure(fg_color="transparent")
                def on_click(e): self.select_suggestion(n)
                
                bind_events(row, on_enter, on_leave, on_click)
                
                if img:
                    try:
                        image = Image.open(io.BytesIO(img))
                        ctk_img = ctk.CTkImage(light_image=image, dark_image=image, size=(92, 34))
                        lbl_img = ctk.CTkLabel(row, text="", image=ctk_img)
                        lbl_img.pack(side="left", padx=(5, 10), pady=5)
                        bind_events(lbl_img, on_enter, on_leave, on_click)
                    except Exception:
                        pass
                
                lbl_name = ctk.CTkLabel(row, text=n, font=ctk.CTkFont(size=13, weight="bold"), text_color=("black", "white"))
                lbl_name.pack(side="left", fill="y", padx=(5, 0))
                bind_events(lbl_name, on_enter, on_leave, on_click)
                
                if src == "Steam":
                    bg_color = ("#d1d5db", "#1b2838")
                    txt_color = ("#111827", "#c7d5e0")
                    logo_text = "  STEAM  "
                else:
                    bg_color = ("#d1d5db", "#212121")
                    txt_color = ("#111827", "#ffffff")
                    logo_text = "  RAWG  "
                    
                lbl_source = ctk.CTkLabel(row, text=logo_text, fg_color=bg_color, text_color=txt_color, corner_radius=6, font=ctk.CTkFont(size=10, weight="bold"))
                lbl_source.pack(side="right", padx=10, pady=10)
                bind_events(lbl_source, on_enter, on_leave, on_click)
                
            create_row_closure(name, img_data, source)
            
        self.update_idletasks()
        
        x = self.search_frame.winfo_x() + self.game_entry.winfo_x()
        y = self.search_frame.winfo_y() + self.game_entry.winfo_y() + self.game_entry.winfo_height()
        
        self.suggestion_frame.configure(width=entry_width)
        self.suggestion_frame.place(x=x, y=y)
        self.suggestion_frame.lift()

    def select_suggestion(self, name):
        self.game_entry.delete(0, 'end')
        self.game_entry.insert(0, name)
        self.suggestion_frame.place_forget()
        self.optimize_game() 

    def delayed_hide_suggestions(self, event=None):
        self.after(200, self.suggestion_frame.place_forget)

    def setup_tier_tab(self, tab, initial_msg):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color=("gray85", "gray17"))
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll_frame.grid_columnconfigure(0, weight=1)

        setattr(tab, "scroll_frame", scroll_frame)

        lbl = ctk.CTkLabel(scroll_frame, text=initial_msg, font=ctk.CTkFont(size=13, slant="italic"), text_color=("gray50", "gray60"), fg_color="transparent")
        lbl.grid(row=0, column=0, pady=20)
        setattr(tab, "initial_label", lbl)

    def on_tab_change(self):
        if not self.current_game_reqs:
            return
            
        selected_tab = self.profiles_tabview.get()
        reqs = self.current_game_reqs.get(selected_tab)
        
        if reqs:
            gpu_r, cpu_r, ram_r = reqs
            equiv_gpu = get_equivalent_gpu(gpu_r)
            equiv_cpu = get_equivalent_cpu(cpu_r)
            equiv_ram = get_equivalent_ram(ram_r)
            
            self.req_gpu_label.configure(text=f"Req GPU: {int(gpu_r)} pts\n(~ {equiv_gpu})")
            self.req_cpu_label.configure(text=f"Req CPU: {int(cpu_r)} pts\n(~ {equiv_cpu})")
            self.req_ram_label.configure(text=f"Req RAM: {int(ram_r)} pts\n(~ {equiv_ram})")
            
            gpu_ratio = self.app.gpu_score / max(1, gpu_r)
            cpu_ratio = self.app.cpu_score / max(1, cpu_r)
            ram_ratio = self.app.ram_score / max(1, ram_r)
            
            warning = ""
            if cpu_ratio < gpu_ratio * 0.75 and cpu_ratio < 1.0:
                warning = "⚠️ CPU Bottleneck Detected: Your GPU is being held back by your CPU."
            elif ram_ratio < 0.8:
                warning = "⚠️ Low RAM Detected: You may experience severe stuttering."
                
            self.bottleneck_label.configure(text=warning)

    def refresh_optimization(self, *args):
        if self.last_tested_game and self.current_game_reqs:
            self.app.status_label.configure(text="Status: Applying new settings...", text_color="orange")
            threading.Thread(target=self.optimize_game_task, args=(self.last_tested_game,), daemon=True).start()

    def optimize_game(self):
        game_name = self.game_entry.get().strip()
        if not game_name:
            messagebox.showwarning("Warning", "Please enter a game name.")
            return

        self.app.status_label.configure(text="Status: Fetching API data...", text_color="orange")
        self.app.progress_bar.set(0.5)
        self.search_btn.configure(state="disabled")
        threading.Thread(target=self.optimize_game_task, args=(game_name,), daemon=True).start()

    def optimize_game_task(self, game_name):
        logo_data = None
        display_name = game_name
        found_on_steam = False
        data_source = None
        
        try:
            search_url = f"https://steamcommunity.com/actions/SearchApps/{game_name}"
            search_resp = requests.get(search_url, timeout=4)
            if search_resp.status_code == 200 and search_resp.json():
                top_result = search_resp.json()[0]
                display_name = top_result.get("name", game_name)
                logo_url = top_result.get("logo")
                if logo_url:
                    img_resp = requests.get(logo_url, timeout=3)
                    if img_resp.status_code == 200:
                        logo_data = img_resp.content
                found_on_steam = True
                data_source = "Steam"
        except Exception:
            pass

        if not found_on_steam and RAWG_API_KEY and RAWG_API_KEY != "YOUR_API_KEY_HERE":
            try:
                rawg_url = f"https://api.rawg.io/api/games?key={RAWG_API_KEY}&search={game_name}&page_size=1"
                resp = requests.get(rawg_url, timeout=4)
                if resp.status_code == 200:
                    res_data = resp.json().get("results", [])
                    if res_data:
                        display_name = res_data[0].get("name", game_name)
                        logo_url = res_data[0].get("background_image")
                        if logo_url:
                            img_resp = requests.get(logo_url, timeout=3)
                            if img_resp.status_code == 200:
                                logo_data = img_resp.content
                        data_source = "RAWG"
            except Exception:
                pass

        self.last_tested_game = display_name
        self.last_logo_data = logo_data
        self.after(0, lambda: self.update_game_header(display_name, logo_data, data_source))

        try:
            requirements = fetch_game_requirements(display_name)
            
            if not requirements:
                err_text = f"Could not fetch requirement data for '{display_name}'."
                self.after(0, lambda: messagebox.showerror("Error", err_text, parent=self.app))
                self.after(0, lambda: self.app.status_label.configure(text="Status: Ready", text_color="green"))
                self.after(0, lambda: self.finalize_optimization_ui())
                return

            req_min_text = requirements.get("minimum", "")
            req_rec_text = requirements.get("recommended", "")
            if not req_rec_text or "Graphics:" not in req_rec_text:
                req_rec_text = req_min_text

            gpu_min = parse_gpu_requirement(req_min_text)
            cpu_min = parse_cpu_requirement(req_min_text)
            ram_min = parse_ram_requirement(req_min_text)
            
            gpu_rec = parse_gpu_requirement(req_rec_text)
            cpu_rec = parse_cpu_requirement(req_rec_text)
            ram_rec = parse_ram_requirement(req_rec_text)

            if gpu_rec <= 2000 and gpu_min > 2000: gpu_rec = int(gpu_min * 1.5)
            if cpu_rec <= 4000 and cpu_min > 4000: cpu_rec = int(cpu_min * 1.3)
            if ram_rec <= 1000 and ram_min > 1000: ram_rec = int(ram_min * 1.5)

            gpu_rec = max(gpu_min, gpu_rec)
            cpu_rec = max(cpu_min, cpu_rec)
            ram_rec = max(ram_min, ram_rec)

            reqs_dict = calculate_exact_requirements(gpu_rec, cpu_rec, ram_rec, display_name)

            actual_gpu_name = self.app.actual_specs.get("GPU", "Unknown GPU")
            eval_gpu_name = actual_gpu_name
            
            if not self.app.setting_enable_fg.get():
                eval_gpu_name = eval_gpu_name.replace("RTX 4", "GTX 4").replace("RTX 5", "GTX 5")
            if not self.app.setting_enable_rt.get():
                eval_gpu_name = eval_gpu_name.replace("RTX", "GTX").replace("RX 7", "RX 5").replace("RX 6", "RX 5")
            
            profiles = evaluate_hardware(
                self.app.gpu_score, self.app.cpu_score, self.app.ram_score,
                gpu_rec, cpu_rec, ram_rec,
                req_rec_text, eval_gpu_name, display_name
            )
            
            fps_format_pref = self.app.setting_fps_format.get()
            is_avg_mode = "Average" in fps_format_pref
            is_min_mode = "Minimum" in fps_format_pref
            
            if is_avg_mode or is_min_mode:
                for profile_name in profiles:
                    fps_str = profiles[profile_name].get("Estimated FPS", "")
                    if "FPS" in fps_str and "-" in fps_str:
                        try:
                            prefix_part, desc_part = fps_str.split("FPS")
                            nums = [int(s) for s in prefix_part.replace("~", "").replace(">", "").split() if s.isdigit()]
                            if len(nums) >= 2:
                                num1, num2 = nums[0], nums[1]
                                avg = int((num1 + num2) / 2)
                                if is_avg_mode:
                                    profiles[profile_name]["Estimated FPS"] = f"~{avg} FPS{desc_part}"
                                elif is_min_mode:
                                    profiles[profile_name]["Estimated FPS"] = f"> {num1} FPS{desc_part}"
                        except Exception as e:
                            pass

            self.after(0, lambda: self.update_results_ui(reqs_dict, profiles))
        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda: messagebox.showerror("Error", f"Optimization failed: {err_msg}", parent=self.app))
            self.after(0, lambda: self.app.status_label.configure(text="Status: Ready", text_color="green"))
        finally:
            self.after(0, lambda: self.finalize_optimization_ui())

    def finalize_optimization_ui(self):
        self.search_btn.configure(state="normal")
        self.app.progress_bar.set(0.0)

    def update_results_ui(self, reqs_dict, profiles):
        self.current_game_reqs = reqs_dict
        self.last_profiles = profiles
        self.on_tab_change()

        tier_keys = list(profiles.keys())
        if len(tier_keys) >= 3:
            self.populate_tier_tab(self.tab_perf, profiles[tier_keys[0]])
            self.populate_tier_tab(self.tab_bal, profiles[tier_keys[1]])
            self.populate_tier_tab(self.tab_max, profiles[tier_keys[2]])

        self.app.status_label.configure(text="Status: Optimization complete!", text_color="green")
        self.app.progress_bar.set(1.0)

    def populate_tier_tab(self, tab, settings_dict):
        scroll_frame = tab.scroll_frame

        for widget in scroll_frame.winfo_children():
            widget.destroy()

        scroll_frame.grid_columnconfigure(0, weight=1)
        scroll_frame.grid_columnconfigure(1, weight=1)

        row_idx = 0
        for setting, value in settings_dict.items():
            card = ctk.CTkFrame(scroll_frame, fg_color=("gray92", "gray15"), corner_radius=6)
            card.grid(row=row_idx, column=0, columnspan=2, sticky="ew", padx=5, pady=4)
            card.grid_columnconfigure(1, weight=1)

            key_lbl = ctk.CTkLabel(card, text=setting, font=ctk.CTkFont(size=13, weight="bold"), anchor="w", text_color=("black", "white"), fg_color="transparent")
            key_lbl.grid(row=0, column=0, padx=12, pady=8, sticky="w")

            val_str = str(value)
            val_color = ("gray20", "gray80")
            if "Enabled" in val_str or "DLSS" in val_str or "Ultra" in val_str:
                val_color = "#2ecc71"
            elif "Disabled" in val_str or "Off" in val_str or "Not Supported" in val_str:
                val_color = "#e74c3c"
            elif "UNPLAYABLE" in val_str or "Poor" in val_str or "Lowest" in val_str:
                val_color = "#e74c3c"

            val_lbl = ctk.CTkLabel(card, text=val_str, font=ctk.CTkFont(size=13), text_color=val_color, anchor="e", fg_color="transparent")
            val_lbl.grid(row=0, column=1, padx=12, pady=8, sticky="e")

            row_idx += 1