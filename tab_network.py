import threading
import subprocess
import re
import time
import requests
import customtkinter as ctk

from ui_widgets import ToolTip

class NetworkSpeedTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.servers = [
            {"name": "Google DNS (Global Baseline)", "ip": "8.8.8.8"},
            {"name": "Cloudflare DNS (Global Baseline)", "ip": "1.1.1.1"},
            {"name": "Rocket League (EU West)", "ip": "104.153.85.99"},
            {"name": "CS2 / Valve (EU Server)", "ip": "146.66.152.1"},
            {"name": "League of Legends (EUW)", "ip": "104.160.141.3"}
        ]
        
        self.result_widgets = []
        self.create_widgets()

    def create_widgets(self):
        # Header Section
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.header_label = ctk.CTkLabel(self.header_frame, text="Network Speed & Latency Diagnostics", font=ctk.CTkFont(size=22, weight="bold"))
        self.header_label.pack(side="left", padx=5)
        ToolTip(self.header_label, "Measures connection bandwidth (Speedometer) and server latencies.")

        # Dashboard / Tachometer Section (Speed Test)
        self.dash_frame = ctk.CTkFrame(self, fg_color=("gray95", "gray15"), corner_radius=8)
        self.dash_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        self.dash_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Download Speed Box
        self.dl_box = ctk.CTkFrame(self.dash_frame, fg_color=("gray85", "gray20"), corner_radius=6)
        self.dl_box.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(self.dl_box, text="DOWNLOAD SPEED", font=ctk.CTkFont(size=11, weight="bold"), text_color=("gray50", "gray70")).pack(pady=(8, 0))
        self.dl_val_label = ctk.CTkLabel(self.dl_box, text="0.0", font=ctk.CTkFont(size=28, weight="bold"), text_color="#3498db")
        self.dl_val_label.pack(pady=(0, 0))
        ctk.CTkLabel(self.dl_box, text="Mbps", font=ctk.CTkFont(size=12, weight="bold"), text_color=("gray50", "gray70")).pack(pady=(0, 8))

        # Upload Speed Box
        self.ul_box = ctk.CTkFrame(self.dash_frame, fg_color=("gray85", "gray20"), corner_radius=6)
        self.ul_box.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(self.ul_box, text="UPLOAD SPEED", font=ctk.CTkFont(size=11, weight="bold"), text_color=("gray50", "gray70")).pack(pady=(8, 0))
        self.ul_val_label = ctk.CTkLabel(self.ul_box, text="0.0", font=ctk.CTkFont(size=28, weight="bold"), text_color="#9b59b6")
        self.ul_val_label.pack(pady=(0, 0))
        ctk.CTkLabel(self.ul_box, text="Mbps", font=ctk.CTkFont(size=12, weight="bold"), text_color=("gray50", "gray70")).pack(pady=(0, 8))

        # Controls & Start Button Box
        self.action_box = ctk.CTkFrame(self.dash_frame, fg_color="transparent")
        self.action_box.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        
        self.start_btn = ctk.CTkButton(self.action_box, text="Start Full Test", width=180, height=40, font=ctk.CTkFont(weight="bold", size=14), fg_color="#27ae60", hover_color="#2ecc71", command=self.start_test)
        self.start_btn.pack(pady=(5, 5))
        
        self.status_label = ctk.CTkLabel(self.action_box, text="Ready to test.", text_color=("gray50", "gray70"), font=ctk.CTkFont(size=12))
        self.status_label.pack()

        # Results Table Section (Ping & Jitter)
        self.results_frame = ctk.CTkScrollableFrame(self, fg_color=("gray85", "gray17"), corner_radius=6)
        self.results_frame.grid(row=2, column=0, sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=3)
        self.results_frame.grid_columnconfigure((1, 2, 3), weight=1)
        
        ctk.CTkLabel(self.results_frame, text="Server / Game", font=ctk.CTkFont(weight="bold", size=14)).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        ctk.CTkLabel(self.results_frame, text="Avg Ping", font=ctk.CTkFont(weight="bold", size=14)).grid(row=0, column=1, padx=10, pady=10)
        ctk.CTkLabel(self.results_frame, text="Jitter", font=ctk.CTkFont(weight="bold", size=14)).grid(row=0, column=2, padx=10, pady=10)
        ctk.CTkLabel(self.results_frame, text="Packet Loss", font=ctk.CTkFont(weight="bold", size=14)).grid(row=0, column=3, padx=10, pady=10)

    def start_test(self):
        self.start_btn.configure(state="disabled")
        self.dl_val_label.configure(text="0.0")
        self.ul_val_label.configure(text="0.0")
        
        for widgets in self.result_widgets:
            for w in widgets:
                w.destroy()
        self.result_widgets.clear()
        
        threading.Thread(target=self.run_full_network_test, daemon=True).start()

    def run_full_network_test(self):
        # 1. Bandwidth Speed Test (Tachometr)
        self.update_status("Testing Download Speed...", "orange")
        dl_speed = self.measure_download_speed()
        self.after(0, lambda: self.dl_val_label.configure(text=f"{dl_speed:.1f}"))
        
        self.update_status("Testing Upload Speed...", "orange")
        ul_speed = self.measure_upload_speed()
        self.after(0, lambda: self.ul_val_label.configure(text=f"{ul_speed:.1f}"))

        # 2. Server Latency Tests
        for idx, server in enumerate(self.servers):
            self.update_status(f"Pinging {server['name']}...", "orange")
            
            try:
                result = subprocess.run(['ping', '-n', '5', server['ip']], capture_output=True, text=True, errors='ignore', creationflags=0x08000000)
                output = result.stdout
                
                times = re.findall(r'[=<]\s*(\d+)\s*ms', output, re.IGNORECASE)
                sent = 5
                received = len(times)
                loss = int(((sent - received) / sent) * 100) if sent > 0 else 100
                
                if times:
                    times = [int(t) for t in times]
                    avg_ping = sum(times) // len(times)
                    jitter = max(times) - min(times)
                else:
                    avg_ping = 0
                    jitter = 0
                    
                self.after(0, self.add_result_row, idx + 1, server['name'], avg_ping, jitter, loss)
                
            except Exception:
                self.after(0, self.add_result_row, idx + 1, server['name'], 0, 0, 100)
                
        self.finish_test()

    def measure_download_speed(self):
        try:
            # Download a ~10MB test file from Cloudflare CDN
            url = "https://speed.cloudflare.com/__down?bytes=10000000"
            start_time = time.time()
            resp = requests.get(url, timeout=10)
            duration = time.time() - start_time
            
            if resp.status_code == 200 and duration > 0:
                size_bits = len(resp.content) * 8
                mbps = (size_bits / duration) / 1_000_000
                return mbps
        except Exception:
            pass
        return 0.0

    def measure_upload_speed(self):
        try:
            # Upload ~2MB of random data to Cloudflare CDN
            url = "https://speed.cloudflare.com/__up"
            data = os_urandom_safe(2000000)
            start_time = time.time()
            resp = requests.post(url, data=data, timeout=10)
            duration = time.time() - start_time
            
            if resp.status_code == 200 and duration > 0:
                size_bits = len(data) * 8
                mbps = (size_bits / duration) / 1_000_000
                return mbps
        except Exception:
            pass
        return 0.0

    def update_status(self, text, color):
        self.after(0, lambda: self.status_label.configure(text=text, text_color=color))
        self.after(0, lambda: self.app.status_label.configure(text=f"Status: {text}", text_color=color))

    def add_result_row(self, row_idx, name, ping, jitter, loss):
        bg_color = "#252526" if row_idx % 2 == 0 else "#1e1e1f"
        
        row_frame = ctk.CTkFrame(self.results_frame, fg_color=bg_color, corner_radius=4)
        row_frame.grid(row=row_idx, column=0, columnspan=4, sticky="ew", padx=5, pady=2)
        row_frame.grid_columnconfigure(0, weight=3)
        row_frame.grid_columnconfigure((1, 2, 3), weight=1)
        
        name_lbl = ctk.CTkLabel(row_frame, text=name, font=ctk.CTkFont(size=13, weight="bold"))
        name_lbl.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        ping_color = "#2ecc71" if 0 < ping <= 50 else ("#f39c12" if 50 < ping <= 100 else "#e74c3c")
        if ping == 0: ping_color = ("gray50", "gray70")
        ping_txt = f"{ping} ms" if ping > 0 else "Timeout"
        ping_lbl = ctk.CTkLabel(row_frame, text=ping_txt, text_color=ping_color, font=ctk.CTkFont(weight="bold"))
        ping_lbl.grid(row=0, column=1, padx=10, pady=10)
        
        jitter_color = "#2ecc71" if jitter <= 10 else ("#f39c12" if jitter <= 25 else "#e74c3c")
        if ping == 0: jitter_color = ("gray50", "gray70")
        jitter_txt = f"{jitter} ms" if ping > 0 else "-"
        jitter_lbl = ctk.CTkLabel(row_frame, text=jitter_txt, text_color=jitter_color)
        jitter_lbl.grid(row=0, column=2, padx=10, pady=10)
        
        loss_color = "#2ecc71" if loss == 0 else "#e74c3c"
        loss_lbl = ctk.CTkLabel(row_frame, text=f"{loss}%", text_color=loss_color, font=ctk.CTkFont(weight="bold"))
        loss_lbl.grid(row=0, column=3, padx=10, pady=10)
        
        self.result_widgets.append((row_frame, name_lbl, ping_lbl, jitter_lbl, loss_lbl))

    def finish_test(self):
        self.start_btn.configure(state="normal")
        self.update_status("Network diagnostics completed successfully.", "green")

def os_urandom_safe(size):
    import os
    try:
        return os.urandom(size)
    except Exception:
        return b'0' * size