#!/venv/bin/python3
"""
Dragon Warrior Automation Controller
Main application loop
"""

import cv2
import time
import subprocess
import os
from pathlib import Path
from sense import DragonWarriorSensor
from think import Think  # Changed import

class Config:
    """Centralized configuration manager"""
    def __init__(self):
        # Emulator settings
        self.emulator_path = Path("Mesen.AppImage")
        self.rom_path = Path("./DragonWarrior.zip")
        self.emulator_start_delay = 2
        
        self.main_loop_rate = 0.1  # seconds
        
        """Ensure required files exist"""
        if not self.emulator_path.exists():
            raise FileNotFoundError(f"Mesen emulator not found at {self.emulator_path}")
        if not self.rom_path.exists():
            raise FileNotFoundError(f"ROM not found at {self.rom_path}")

def start_emulator(config):
    """Launch Mesen with default configuration"""
    config.emulator_path.chmod(0o755)  # Ensure executable
    
    process = subprocess.Popen(
        [str(config.emulator_path.absolute()), str(config.rom_path.absolute())],
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
        thinker = Think()  # Create Think controller
        
        print("\nControls:")
        print("  q - Quit")
        print("  g - Toggle grid overlay")
        print("  r - Toggle RGB values window")
        print("  d - Toggle diagnostics window")
        print("  s - Save discovered tiles")
        
        while True:
            frame, rgb_grid, _ = sensor.capture_frame()
            cv2.imshow("Dragon Warrior Sensor", frame)
            
            # Process frame through thinker
            thinker.process_frame(rgb_grid)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('g'):
                sensor.toggle_grid()
            elif key == ord('r'):
                sensor.toggle_rgb()
            elif key == ord('d'):
                thinker.toggle_diagnostics()
            elif key == ord('s'):
                thinker.save_discovered_tiles()
            
            time.sleep(config.main_loop_rate)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cv2.destroyAllWindows()
        thinker.toggle_diagnostics()  # Ensure diagnostics window closes
        if 'emulator' in locals():
            emulator.terminate()
        print("Application terminated")

if __name__ == "__main__":
    main()