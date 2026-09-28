import tkinter as tk
import customtkinter as ctk

class ToolTip:
    active_window = None

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.id = None
        try:
            self.widget.bind("<Enter>", self.enter)
            self.widget.bind("<Leave>", self.leave)
            self.widget.bind("<ButtonPress>", self.leave)
            self.widget.bind("<Unmap>", self.leave)
        except Exception:
            pass

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hide_tooltip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(400, self.show_tooltip)

    def unschedule(self):
        idx = self.id
        self.id = None
        if idx:
            try:
                self.widget.after_cancel(idx)
            except Exception:
                pass

    def show_tooltip(self, event=None):
        self.unschedule()
        if not self.text:
            return
        
        if ToolTip.active_window:
            try:
                ToolTip.active_window.destroy()
            except Exception:
                pass
            ToolTip.active_window = None
        
        try:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        except Exception:
            return

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        ToolTip.active_window = tw
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        
        label = tk.Label(tw, text=self.text, justify="left",
                         background="#252526", foreground="#d4d4d4", 
                         relief="solid", borderwidth=1,
                         font=("Segoe UI", 10, "normal"), padx=10, pady=8)
        label.pack()

    def hide_tooltip(self):
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            try:
                tw.destroy()
            except Exception:
                pass
        if ToolTip.active_window == tw:
            ToolTip.active_window = None