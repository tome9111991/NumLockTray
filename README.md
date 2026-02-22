# NumLockTray

NumLockTray is a lightweight Python application that lives in your system tray and provides a visual indicator of the current state of your **Num Lock** key. It is particularly useful for laptops or keyboards that lack a physical status LED.

## Features

- **Dynamic Tray Icon:** Instantly shows whether Num Lock is ON (green glowing LED) or OFF (red glowing LED).
- **Cross-Platform Support:** Works on Windows (via `ctypes`) and Linux (via `xset` or `sysfs`).
- **Configuration GUI:** On the first manual launch, a simple GUI helps you configure autostart and Linux desktop integration.
- **Resource Efficient:** Low-overhead background polling (every 0.3 seconds) ensures minimal CPU impact.

## Prerequisites

Ensure you have Python installed. You can install the required dependencies using the provided `requirements.txt`:

```bash
pip install -r requirements.txt
```

**Dependencies:**
- `Pillow`: For dynamic generation of the status icons.
- `pystray`: For system tray integration.
- `pymupdf`: (fitz) For high-quality SVG rendering of the icons.
- `tkinter`: (Usually bundled with Python) for the configuration dialog.

## Usage

### Normal Launch
To start the application normally:

```powershell
python numlock_tray.py
```
*Note: The autostart configuration window will appear on the first manual run if not yet configured.*

### Autostart Mode
To start the application silently (used by the system during boot):

```powershell
python numlock_tray.py --autostart
```

## Project Structure

- `numlock_tray.py`: The main script containing state detection, icon generation, and tray management logic.
- `requirements.txt`: List of required Python packages.

## Technical Details

The application handles system integration as follows:
- **Windows:** Uses the Registry key `Software\Microsoft\Windows\CurrentVersion\Run` for autostart.
- **Linux:** 
  - **Autostart:** Creates a `.desktop` file in `~/.config/autostart/`.
  - **App Menu:** Creates a `.desktop` file in `~/.local/share/applications/` to allow launching from the application menu without a terminal.
  - All `.desktop` files are configured with `Terminal=false` for silent background execution.
