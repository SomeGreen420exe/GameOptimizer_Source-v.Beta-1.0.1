import requests
import customtkinter as ctk
from tkinter import messagebox
from ui_widgets import ToolTip

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Advanced Settings")
        self.geometry("450x650")
        self.attributes("-topmost", True)
        
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Section 1: Appearance ---
        app_frame = ctk.CTkFrame(container, fg_color=("gray90", "gray15"), corner_radius=8)
        app_frame.pack(fill="x", pady=(0, 15))
        
        app_title = ctk.CTkLabel(app_frame, text="🎨 Appearance & UI", font=ctk.CTkFont(size=14, weight="bold"))
        app_title.pack(anchor="w", padx=15, pady=(10, 5))
        ToolTip(app_title, "Settings related to how the application looks on your screen.")
        
        app_inner = ctk.CTkFrame(app_frame, fg_color="transparent")
        app_inner.pack(fill="x", padx=15, pady=(0, 15))
        
        theme_lbl = ctk.CTkLabel(app_inner, text="Theme Mode:")
        theme_lbl.pack(side="left")
        ToolTip(theme_lbl, "Switch the visual styling of the interface.")
        
        app_menu = ctk.CTkOptionMenu(app_inner, values=["Dark", "Light", "System"], width=130, command=self.change_appearance_mode)
        app_menu.set(ctk.get_appearance_mode())
        app_menu.pack(side="right")
        ToolTip(app_menu, "Change the visual theme of the application (Light, Dark, or sync with Windows System).")

        # --- Section 2: Engine ---
        eng_frame = ctk.CTkFrame(container, fg_color=("gray90", "gray15"), corner_radius=8)
        eng_frame.pack(fill="x", pady=15)
        
        eng_title = ctk.CTkLabel(eng_frame, text="⚙️ Optimization Engine", font=ctk.CTkFont(size=14, weight="bold"))
        eng_title.pack(anchor="w", padx=15, pady=(10, 5))
        ToolTip(eng_title, "Configure how the internal logic predicts frame rates and handles specific rendering technologies.")
        
        fg_switch = ctk.CTkSwitch(eng_frame, text="Enable Frame Generation (DLSS 3 / FSR 3)", variable=self.app.setting_enable_fg, command=self.refresh_optimization)
        fg_switch.pack(anchor="w", padx=15, pady=(10, 5))
        ToolTip(fg_switch, "Allows the engine to simulate AI frame generation for RTX 40/50 and RX 7000 series GPUs.\nProvides massive FPS boosts in supported AAA games.")
        
        rt_switch = ctk.CTkSwitch(eng_frame, text="Enable Ray Tracing (If supported by GPU)", variable=self.app.setting_enable_rt, command=self.refresh_optimization)
        rt_switch.pack(anchor="w", padx=15, pady=(5, 10))
        ToolTip(rt_switch, "Instructs the engine to recommend Ray Tracing settings for realistic lighting.\nDisable this if you prefer raw FPS performance over visual fidelity.")
        
        fps_inner = ctk.CTkFrame(eng_frame, fg_color="transparent")
        fps_inner.pack(fill="x", padx=15, pady=(10, 20))
        
        fps_lbl = ctk.CTkLabel(fps_inner, text="FPS Display Format:")
        fps_lbl.pack(side="left")
        ToolTip(fps_lbl, "How you want the predicted frame rates to be displayed on your screen.")
        
        fps_menu = ctk.CTkOptionMenu(
            fps_inner, 
            values=["Show Range (Min - Max)", "Show Average (~Avg)", "Show Minimum (> Min)"], 
            variable=self.app.setting_fps_format, 
            width=200,
            command=self.refresh_optimization
        )
        fps_menu.pack(side="right")
        
        fps_tooltip_text = (
            "Range: Shows minimum drops and maximum peaks (e.g., 60-75 FPS).\n"
            "Average: Shows a single expected stable framerate (e.g., ~65 FPS).\n"
            "Minimum: Shows the baseline frame rate you shouldn't drop below (e.g., > 60 FPS)."
        )
        ToolTip(fps_menu, fps_tooltip_text)

        # --- Section 3: Network & Data ---
        net_frame = ctk.CTkFrame(container, fg_color=("gray90", "gray15"), corner_radius=8)
        net_frame.pack(fill="x", pady=15)
        
        net_title = ctk.CTkLabel(net_frame, text="🌐 Network & Data", font=ctk.CTkFont(size=14, weight="bold"))
        net_title.pack(anchor="w", padx=15, pady=(10, 5))
        ToolTip(net_title, "Manage data connections and local storage files.")
        
        btn_inner = ctk.CTkFrame(net_frame, fg_color="transparent")
        btn_inner.pack(fill="x", padx=15, pady=(10, 15))
        test_api_btn = ctk.CTkButton(btn_inner, text="Test Steam API", command=self.test_connection, fg_color=("gray75", "gray30"), text_color=("black", "white"), width=150)
        test_api_btn.pack(side="left")
        ToolTip(test_api_btn, "Sends a ping to the Steam Store API to verify your firewall is not blocking the connection.")
        
        clear_cache_btn = ctk.CTkButton(btn_inner, text="Clear Cache", command=lambda: self.app.clear_cache(self), fg_color="#c0392b", hover_color="#e74c3c", width=150)
        clear_cache_btn.pack(side="right")
        ToolTip(clear_cache_btn, "Deletes all locally saved benchmark scores and resets the application to factory defaults.")

        version_text = "Game Optimizer Beta 1.0\nHardware Optimization Suite"
        version_lbl = ctk.CTkLabel(container, text=version_text, text_color="gray", justify="center")
        version_lbl.pack(pady=20)
        ToolTip(version_lbl, "Current build version.")

    def change_appearance_mode(self, new_mode):
        ctk.set_appearance_mode(new_mode)

    def refresh_optimization(self, *args):
        if self.app.search_tab:
            self.app.search_tab.refresh_optimization()

    def test_connection(self):
        try:
            resp = requests.get("https://steamcommunity.com", timeout=3)
            if resp.status_code == 200:
                messagebox.showinfo("Connection Test", "Successfully connected to Steam API!")
            else:
                messagebox.showwarning("Connection Test", f"Failed with status code: {resp.status_code}")
        except Exception as e:
            messagebox.showerror("Connection Test", f"Connection failed: {str(e)}")