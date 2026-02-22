import platform
import subprocess
import threading
import time
import os
import sys
import pystray
from PIL import Image, ImageDraw

def get_num_lock_state():
    """Returns True if Num Lock is ON, False if OFF, None if unknown."""
    sys_name = platform.system()
    if sys_name == "Windows":
        import ctypes
        # VK_NUMLOCK is 0x90
        # GetKeyState returns short where low bit is toggle state
        return bool(ctypes.WinDLL("User32.dll").GetKeyState(0x90) & 1)
    elif sys_name == "Linux":
        try:
            output = subprocess.check_output(["xset", "q"], stderr=subprocess.DEVNULL).decode()
            return "Num Lock:  on" in output or "Num Lock: on" in output
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        # Fallback for some Linux systems
        try:
            led_path = "/sys/class/leds/"
            for folder in os.listdir(led_path):
                if "numlock" in folder.lower():
                    with open(os.path.join(led_path, folder, "brightness"), "r") as f:
                        return f.read().strip() != "0"
        except Exception:
            pass
    return None

def create_icon(active):
    """Creates a 64x64 dynamic icon based on the state."""
    # Create an image with a transparent background
    image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Colors: Green if active, Red if inactive
    bg_color = (0, 200, 0, 255) if active else (200, 0, 0, 255)
    
    # Draw a rounded circle as the base
    draw.ellipse((4, 4, 60, 60), fill=bg_color)
    
    if active:
        # Draw a smaller white inner circle if active
        draw.ellipse((20, 20, 44, 44), fill=(255, 255, 255, 255))
    else:
        # Draw a white cross if inactive
        draw.line((20, 20, 44, 44), fill=(255, 255, 255, 255), width=6)
        draw.line((20, 44, 44, 20), fill=(255, 255, 255, 255), width=6)
        
    return image

def is_autostart_enabled():
    """Checks if the app is configured for autostart."""
    sys_name = platform.system()
    if sys_name == "Windows":
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, "NumLockTray")
            winreg.CloseKey(key)
            return True
        except OSError:
            return False
    elif sys_name == "Linux":
        autostart_path = os.path.expanduser("~/.config/autostart/numlocktray.desktop")
        return os.path.exists(autostart_path)
    return False

def set_autostart(enable):
    """Enables or disables autostart for the current OS."""
    sys_name = platform.system()
    
    # Construct the command to run
    if getattr(sys, 'frozen', False):
        cmd = f'"{sys.executable}" --autostart'
    else:
        cmd = f'"{sys.executable}" "{os.path.abspath(__file__)}" --autostart'
        
    if sys_name == "Windows":
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
            if enable:
                winreg.SetValueEx(key, "NumLockTray", 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, "NumLockTray")
                except OSError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Error setting Windows autostart: {e}")
            
    elif sys_name == "Linux":
        autostart_dir = os.path.expanduser("~/.config/autostart")
        autostart_path = os.path.join(autostart_dir, "numlocktray.desktop")
        
        try:
            if enable:
                os.makedirs(autostart_dir, exist_ok=True)
                desktop_entry = f"""[Desktop Entry]
Type=Application
Exec={cmd}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=NumLockTray
Comment=NumLock Status Tray Icon
"""
                with open(autostart_path, "w") as f:
                    f.write(desktop_entry)
            else:
                if os.path.exists(autostart_path):
                    os.remove(autostart_path)
        except Exception as e:
            print(f"Error setting Linux autostart: {e}")

def show_startup_gui():
    """Shows a simple Tkinter GUI to set the autostart preference."""
    import tkinter as tk
    
    root = tk.Tk()
    root.title("NumLock Tray")
    
    # Center window
    window_width = 350
    window_height = 160
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width / 2)
    center_y = int(screen_height/2 - window_height / 2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    root.resizable(False, False)
    
    # Try to set icon if possible, ignore if fails
    try:
        root.iconbitmap(default='') 
    except:
        pass

    tk.Label(root, text="NumLock Tray Einstellungen", font=("Arial", 12, "bold")).pack(pady=15)
    
    autostart_var = tk.BooleanVar(value=is_autostart_enabled())
    
    cb = tk.Checkbutton(root, text="Beim Systemstart automatisch ausführen", variable=autostart_var, font=("Arial", 10))
    cb.pack(pady=5)
    
    def on_ok():
        set_autostart(autostart_var.get())
        root.destroy()
        
    tk.Button(root, text="OK & Starten", command=on_ok, width=15, font=("Arial", 10)).pack(pady=15)
    
    # Bring window to front
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)
    
    root.mainloop()

class NumLockTrayApp:
    def __init__(self):
        self.running = True
        self.current_state = get_num_lock_state() or False
        self.autostart_enabled = is_autostart_enabled()
        
        # Setup tray icon
        self.icon = pystray.Icon(
            "NumLockTray", 
            create_icon(self.current_state), 
            f"Num Lock: {'ON' if self.current_state else 'OFF'}", 
            menu=pystray.Menu(
                pystray.MenuItem(
                    "Mit System starten", 
                    self.toggle_autostart, 
                    checked=lambda item: self.autostart_enabled
                ),
                pystray.MenuItem("Beenden", self.quit_app)
            )
        )
        
    def toggle_autostart(self, icon, item):
        self.autostart_enabled = not self.autostart_enabled
        set_autostart(self.autostart_enabled)
        
    def monitor_state(self):
        while self.running:
            state = get_num_lock_state()
            if state != self.current_state and state is not None:
                self.current_state = state
                self.icon.icon = create_icon(self.current_state)
                self.icon.title = f"Num Lock: {'ON' if self.current_state else 'OFF'}"
            time.sleep(0.3)
            
    def quit_app(self, icon, item):
        self.running = False
        self.icon.stop()

    def run(self):
        # Start background polling thread
        thread = threading.Thread(target=self.monitor_state, daemon=True)
        thread.start()
        # Start icon event loop (blocks until stopped)
        self.icon.run()

if __name__ == "__main__":
    # If not started automatically by the system, show the configuration GUI first
    if "--autostart" not in sys.argv:
        show_startup_gui()
        
    app = NumLockTrayApp()
    app.run()
