@echo off
echo Starte Build-Prozess fuer NumLockTray...

:: Sicherstellen, dass die Anforderungen installiert sind
echo Installiere Abhaengigkeiten...
py -m pip install -r requirements.txt
py -m pip install pyinstaller

:: Build mit PyInstaller
echo Erstelle .exe Datei...
py -m PyInstaller --noconfirm --onefile --noconsole --clean --icon="assets\numlock.ico" --add-data "assets;assets" numlock_tray.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build erfolgreich! Die .exe befindet sich im 'dist' Ordner.
) else (
    echo.
    echo Fehler beim Build-Prozess.
)

pause
