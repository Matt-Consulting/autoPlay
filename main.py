#!/venv/bin/python3
"""
Dragon Warrior Automation Controller
Optimized version with non-blocking action system
"""

import cv2
import time
import subprocess
import os
import random
from pathlib import Path
from sense import DragonWarriorSensor
from think import Think

class Config:
    """Centralized configuration manager"""
    def __init__(self):
        # Emulator settings
        self.emulator_path = Path("Mesen.AppImage")
        self.rom_path = Path("./DragonWarrior.zip")
        self.emulator_start_delay = 2
        
        # Timing parameters
        self.loops_per_second = 15  # Target frame rate
        self.main_loop_delay = 1/self.loops_per_second

        # Display options
        self.show_rgb_by_default = True  # Enable RGB window on startup
        self.show_diagnostics_by_default = True  # Enable diagnostics window on startup
        
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

def initialize_game():
    """Initialize all game components"""
    try:
        config = Config()
        emulator = start_emulator(config)
        print(f"Emulator started (PID: {emulator.pid})")
        
        sensor = DragonWarriorSensor()
        thinker = Think()
        
        # Enable default windows if configured
        if config.show_rgb_by_default:
            sensor.toggle_rgb()
        if config.show_diagnostics_by_default:
            thinker.toggle_diagnostics()
        
        return emulator, sensor, thinker
    except Exception as e:
        print(f"Initialization failed: {e}")
        raise

def main():
    """Main application loop with non-blocking actions"""
    emulator = sensor = thinker = None
    config = Config()
    
    show_fps = False  # Track whether to display FPS
    
    try:
        # Initialize all components
        emulator, sensor, thinker = initialize_game()
        
        print("\nControls:")
        print("  q - Quit")
        print("  g - Toggle grid overlay")
        print("  r - Toggle RGB values window")
        print("  d - Toggle diagnostics window")
        print("  s - Save discovered tiles")
        print("  z - Reset learning process")
        print("  f - Toggle FPS display")
        print("  l - Toggle tile learning")
        
        # Main loop
        while True:
            # Start frame timing
            frame_start = time.time()
            
            # Capture and process frame
            frame, rgb_grid, _ = sensor.capture_frame()
            cv2.imshow("Dragon Warrior Sensor", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            
            # Only process frame if we have a valid RGB grid
            if rgb_grid is not None:
                thinker.process_frame(rgb_grid)
            
            # Handle input
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
            elif key == ord('z'):
                thinker.reset_learning()
            elif key == ord('f'):
                show_fps = not show_fps
                print(f"\nFPS display {'ON' if show_fps else 'OFF'}")
                if not show_fps:
                    print()  # Clear the line
            elif key == ord('l'):
                thinker.toggle_learning()
            
            # Maintain consistent timing
            elapsed = time.time() - frame_start
            remaining_time = config.main_loop_delay - elapsed
            if remaining_time > 0:
                time.sleep(remaining_time)

                        # Display FPS if enabled
            if show_fps:
                actual_frame_time = time.time() - frame_start
                current_fps = 1.0 / actual_frame_time
                fps_text = f"FPS: {current_fps:.1f} (Target: {config.loops_per_second})"
                print(f"\r{fps_text}", end="", flush=True)
            
    except KeyboardInterrupt:
        print("\nReceived interrupt signal")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        if sensor is not None:
            cv2.destroyAllWindows()
        if thinker is not None:
            thinker.toggle_diagnostics()
        if emulator is not None:
            emulator.terminate()
        print("\nApplication terminated")

if __name__ == "__main__":
    main()