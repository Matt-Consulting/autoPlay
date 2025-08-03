#!/venv/bin/python3
"""
Dragon Warrior Automation Controller
Uses Mesen emulator with default keybindings
"""

import cv2
import time
import subprocess
import os
from pathlib import Path
from sense import DragonWarriorSensor

class Config:
    """Centralized configuration manager"""
    
    def __init__(self):
        # Emulator settings
        self.emulator_paths = [
            "Mesen.AppImage",
            "Mesen (Linux x64 - AppImage).AppImage",
            "Mesen2.AppImage"
        ]
        self.rom_path = Path("./DragonWarrior.zip")
        self.emulator_start_delay = 5  # seconds
        
        # Sensor settings
        self.sensor_refresh_rate = 0.1  # seconds
        self.grid_visible = True
        self.rgb_display = False
        self.type_display = False
        
        # Keybindings (using ASCII codes)
        self.keybindings = {
            'quit': ord('q'),
            'toggle_grid': ord('g'),
            'toggle_rgb': ord('r'),
            'toggle_types': ord('t')
        }
        
        self.validate_paths()

    def validate_paths(self):
        """Ensure required files exist"""
        if not any(Path(p).exists() for p in self.emulator_paths):
            raise FileNotFoundError("Mesen emulator not found")
        if not self.rom_path.exists():
            raise FileNotFoundError(f"ROM not found at {self.rom_path}")

def start_emulator(config):
    """Launch Mesen with default configuration"""
    mesen_path = next(Path(p) for p in config.emulator_paths if Path(p).exists())
    mesen_path.chmod(0o755)  # Ensure executable
    
    process = subprocess.Popen(
        [str(mesen_path.absolute()), str(config.rom_path.absolute())],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=os.getcwd()
    )
    
    time.sleep(config.emulator_start_delay)
    return process

def main():
    """Main application loop"""
    try:
        config = Config()
        emulator = start_emulator(config)
        print(f"Emulator started (PID: {emulator.pid})")
        
        sensor = DragonWarriorSensor()
        sensor.grid_visible = config.grid_visible
        sensor.rgb_display = config.rgb_display
        sensor.type_display = config.type_display
        
        while True:
            frame, _, _ = sensor.capture_frame()
            cv2.imshow("Dragon Warrior Sensor", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == config.keybindings['quit']:
                break
            elif key == config.keybindings['toggle_grid']:
                sensor.grid_visible = not sensor.grid_visible
            elif key == config.keybindings['toggle_rgb']:
                sensor.rgb_display = not sensor.rgb_display
            elif key == config.keybindings['toggle_types']:
                sensor.type_display = not sensor.type_display
            
            time.sleep(config.sensor_refresh_rate)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cv2.destroyAllWindows()
        if 'emulator' in locals():
            emulator.terminate()
        print("Application terminated")

if __name__ == "__main__":
    main()