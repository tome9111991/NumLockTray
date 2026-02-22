import platform
import subprocess
import threading
import time
import os
import sys
import pystray
import re
import fitz
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
    """Creates a 64x64 dynamic icon based on the state using the SVG asset."""
    # Find base path for assets (handles PyInstaller bundle)
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        
    svg_path = os.path.join(base_path, "assets", "numlock.svg")
    
    try:
        with open(svg_path, "r", encoding="utf-8") as f:
            svg_content = f.read()
            
        if not active:
            # Ersetze die Farbe des leuchtenden LED-Elements durch Rot (#ff3333)
            # Sucht gezielt nach dem fill-Wert vor filter="url(#glow)"
            svg_content = re.sub(r'fill="([^"]+)"(?=\s+filter="url\(#glow\)")', r'fill="#ff3333"', svg_content)
            
        svg_doc = fitz.open("svg", svg_content.encode('utf-8'))
        pix = svg_doc[0].get_pixmap(alpha=True)
        image = Image.frombytes("RGBA", [pix.width, pix.height], pix.samples)
        
        # Scale to 64x64 for tray icon
        image = image.resize((64, 64), Image.Resampling.LANCZOS)
        return image
        
    except Exception as e:
        print(f"Error loading SVG: {e}")
        # Fallback to programmatic drawing
        image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        key_color = (0, 180, 0, 255) if active else (60, 60, 60, 255)
        text_color = (255, 255, 255, 255) if active else (150, 150, 150, 255)
        try:
            draw.rounded_rectangle((4, 4, 60, 60), radius=8, fill=key_color, outline=(200, 200, 200, 255), width=2)
        except AttributeError:
            draw.rectangle((4, 4, 60, 60), fill=key_color, outline=(200, 200, 200, 255), width=2)
        draw.line((24, 46, 40, 46), fill=text_color, width=6)
        draw.line((32, 18, 32, 46), fill=text_color, width=6)
        draw.line((22, 28, 32, 18), fill=text_color, width=6)
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
        
        # Find base path for assets
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, "assets", "numlock.svg")
        
        try:
            if enable:
                os.makedirs(autostart_dir, exist_ok=True)
                desktop_entry = f"""[Desktop Entry]
Type=Application
Exec={cmd}
Icon={icon_path}
Terminal=false
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=NumLockTray
Comment=NumLock Status Tray Icon
Categories=Utility;System;
Keywords=num;lock;tray;led;
"""
                with open(autostart_path, "w") as f:
                    f.write(desktop_entry)
            else:
                if os.path.exists(autostart_path):
                    os.remove(autostart_path)
        except Exception as e:
            print(f"Error setting Linux autostart: {e}")

def is_app_menu_installed():
    """Checks if the app is installed in the Linux application menu."""
    if platform.system() != "Linux":
        return False
    app_menu_path = os.path.expanduser("~/.local/share/applications/numlocktray.desktop")
    return os.path.exists(app_menu_path)

def set_app_menu(enable):
    """Creates or removes the .desktop file in the application menu."""
    if platform.system() != "Linux":
        return
        
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        cmd = f'"{sys.executable}" --autostart'
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        cmd = f'"{sys.executable}" "{os.path.abspath(__file__)}" --autostart'
        
    icon_path = os.path.join(base_path, "assets", "numlock.svg")
    apps_dir = os.path.expanduser("~/.local/share/applications")
    app_menu_path = os.path.join(apps_dir, "numlocktray.desktop")
    
    try:
        if enable:
            os.makedirs(apps_dir, exist_ok=True)
            desktop_entry = f"""[Desktop Entry]
Type=Application
Name=NumLockTray
Icon={icon_path}
Comment=NumLock Status Tray Icon
Exec={cmd}
Terminal=false
Categories=Utility;System;Settings;
Keywords=num;lock;tray;led;
"""
            with open(app_menu_path, "w") as f:
                f.write(desktop_entry)
        else:
            if os.path.exists(app_menu_path):
                os.remove(app_menu_path)
    except Exception as e:
        print(f"Error setting Linux app menu: {e}")

def show_startup_gui():
    """Shows a simple Tkinter GUI to set the autostart preference."""
    import tkinter as tk
    
    root = tk.Tk()
    root.title("NumLock Tray")
    
    # Center window
    window_width = 350
    window_height = 190 if platform.system() == "Linux" else 160
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
    
    cb_autostart = tk.Checkbutton(root, text="Beim Systemstart automatisch ausführen", variable=autostart_var, font=("Arial", 10))
    cb_autostart.pack(pady=5)
    
    if platform.system() == "Linux":
        app_menu_var = tk.BooleanVar(value=is_app_menu_installed())
        cb_app_menu = tk.Checkbutton(root, text="Im App-Menü installieren (Starter erstellen)", variable=app_menu_var, font=("Arial", 10))
        cb_app_menu.pack(pady=5)
    
    def on_ok():
        set_autostart(autostart_var.get())
        if platform.system() == "Linux":
            set_app_menu(app_menu_var.get())
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
