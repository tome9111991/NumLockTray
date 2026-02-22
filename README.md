# NumLockTray

NumLockTray is a lightweight Python application that lives in your system tray and provides a visual indicator of the current state of your **Num Lock** key. It is particularly useful for laptops or keyboards that lack a physical status LED.

## Features

- **Dynamic Tray Icon:** Instantly shows whether Num Lock is ON (green circle) or OFF (red circle with a cross).
- **Cross-Platform Support:** Works on Windows (via `ctypes`) and Linux (via `xset` or `sysfs`).
- **Autostart Configuration:** On the first manual launch, a simple GUI helps you configure the app to start automatically with your OS.
- **Resource Efficient:** Low-overhead background polling (every 0.3 seconds) ensures minimal CPU impact.

## Prerequisites

Ensure you have Python installed. You can install the required dependencies using the provided `requirements.txt`:

```powershell
pip install -r requirements.txt
```

**Dependencies:**
- `Pillow`: For dynamic generation of the status icons.
- `pystray`: For system tray integration.
- `tkinter`: (Usually bundled with Python) for the autostart configuration dialog.

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

The application handles autostart entries as follows:
- **Windows:** Uses the Registry key `Software\Microsoft\Windows\CurrentVersion\Run`.
- **Linux:** Creates a `.desktop` file in `~/.config/autostart/`.
