#!/venv/bin/python3
"""
Dragon Warrior Automation Controller with World Mapping
"""

import cv2
import time
import subprocess
import os
from pathlib import Path
from sense import DragonWarriorSensor
from think import Think
from mapping import WorldMapper

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
        self.show_rgb_by_default = True
        self.show_diagnostics_by_default = True
        self.show_map_by_default = True
        
        if not self.emulator_path.exists():
            raise FileNotFoundError(f"Emulator not found at {self.emulator_path}")
        if not self.rom_path.exists():
            raise FileNotFoundError(f"ROM not found at {self.rom_path}")

def start_emulator(config):
    """Launch Mesen with default configuration"""
    config.emulator_path.chmod(0o755)
    process = subprocess.Popen(
        [str(config.emulator_path.absolute()), str(config.rom_path.absolute())],
        stdout=None,
        stderr=None
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
        if config.show_map_by_default:
            thinker.toggle_map()
        
        return emulator, sensor, thinker, config
    except Exception as e:
        print(f"Initialization failed: {e}")
        raise

def main():
    """Main application loop with world mapping"""
    emulator = sensor = thinker = None
    config = Config()
    show_fps = False
    show_map = True
    
    try:
        # Initialize all components
        emulator, sensor, thinker, config = initialize_game()
        
        print("\nControls:")
        print("  q - Quit")
        print("  g - Toggle grid overlay")
        print("  r - Toggle RGB values window")
        print("  d - Toggle diagnostics window")
        print("  m - Toggle world map display")
        print("  z - Reset learning process")
        print("  f - Toggle FPS display")
        print("  l - Toggle tile learning")
        print("  arrow keys - Simulate movement (for testing)")
        
        # Main loop
        while True:
            frame_start = time.time()
            
            # Capture and process frame
            frame, rgb_grid, _ = sensor.capture_frame()
            cv2.imshow("Dragon Warrior Sensor", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            
            # Process frame if we have valid data
            alias_grid = None
            if rgb_grid is not None:
                alias_grid = thinker.process_frame(rgb_grid)
                
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
            elif key == ord('m'):
                thinker.toggle_map()
            elif key == ord('s'):
                thinker.save_discovered_tiles()
            elif key == ord('z'):
                thinker.reset_learning()
            elif key == ord('f'):
                show_fps = not show_fps
                print(f"\nFPS display {'ON' if show_fps else 'OFF'}")
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
        cv2.destroyAllWindows()
        if emulator is not None:
            emulator.terminate()
        print("\nApplication terminated")

if __name__ == "__main__":
    main()