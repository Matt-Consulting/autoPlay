#!/venv/bin/python3
import cv2
import numpy as np
import subprocess
import time
from pathlib import Path
from mss import mss

class DragonWarriorSensor:
    def __init__(self, grid_visible=True, rgb_display=False, type_display=False):
        self.grid_visible = grid_visible
        self.rgb_display = rgb_display
        self.type_display = type_display
        self.sct = mss()
        
        # Initialize window geometry
        self.monitor = self._get_window_geometry()
        
        # Grid configuration
        self.GRID_SIZE = 15
        self.TILE_SIZE = 16
        
        # Color mappings (using decimal values)
        self.color_to_type = {
            (132, 132, 132): 0,  # block (0x84)
            (40, 47, 96): 1      # brick (0x28, 0x2F, 0x60)
        }
        self.type_aliases = {
            0: "block",
            1: "brick"
        }

    def _get_window_geometry(self):
        """Get window geometry using xdotool with automatic retries"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Get window ID
                result = subprocess.run(
                    ['xdotool', 'search', '--name', 'Mesen - Dragon Warrior'],
                    capture_output=True, text=True, timeout=2
                )
                window_ids = result.stdout.strip().split('\n')
                
                if not window_ids or not window_ids[0]:
                    raise ValueError("Mesen window not found")
                
                # Try all found windows
                for window_id in window_ids:
                    try:
                        # Get window geometry
                        result = subprocess.run(
                            ['xdotool', 'getwindowgeometry', window_id],
                            capture_output=True, text=True, timeout=2
                        )
                        geometry = result.stdout
                        
                        # Parse geometry output
                        lines = [line.strip() for line in geometry.split('\n') if line.strip()]
                        if len(lines) < 3:
                            continue
                            
                        # Extract position
                        pos_line = lines[1]
                        if '(' in pos_line:
                            pos_part = pos_line.split('(')[0].split(':')[1].strip()
                            x, y = map(int, pos_part.split(','))
                        else:
                            pos_part = pos_line.split(':')[1].replace(',', '').strip()
                            x, y = map(int, pos_part.split('+'))
                        
                        # Extract size
                        size_part = lines[2].split(':')[1].strip()
                        width, height = map(int, size_part.split('x'))
                        
                        print(f"Window geometry: x={x}, y={y}, width={width}, height={height}")
                        return {
                            "top": y - 40,
                            "left": x + 6,
                            "width": 240,
                            "height": 240
                        }
                        
                    except (IndexError, ValueError) as e:
                        continue
                
                raise ValueError("No window with valid geometry found")
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                time.sleep(1)
        
        print("Falling back to default window position")
        return {
            "top": 36,
            "left": 40,
            "width": 256,
            "height": 240
        }

    def manual_calibrate(self, top, left, width=256, height=256):
        """Manually set window capture coordinates"""
        self.monitor = {
            "top": top,
            "left": left,
            "width": width,
            "height": height
        }
        print(f"Manual calibration set: {self.monitor}")

    def capture_frame(self, debug=False):
        """Capture and process game frame"""
        try:
            # Capture screen region
            frame = np.array(self.sct.grab(self.monitor))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
            
            if debug:
                debug_file = Path("debug_capture.png")
                cv2.imwrite(str(debug_file), frame_rgb)
                print(f"Debug capture saved to {debug_file}")
                print(f"Capture area: {self.monitor}")
            
            if self.grid_visible:
                return self._process_frame(frame_rgb)
            return frame_rgb, None, None
            
        except Exception as e:
            print(f"Capture error: {e}")
            blank = np.zeros((256, 256, 3), dtype=np.uint8)
            return blank, None, None

    def _process_frame(self, frame):
        """Process frame with grid analysis"""
        h, w = frame.shape[:2]
        cell_size = h // self.GRID_SIZE
        
        rgb_grid = np.zeros((self.GRID_SIZE, self.GRID_SIZE, 3), dtype=np.uint8)
        type_grid = np.zeros((self.GRID_SIZE, self.GRID_SIZE), dtype=np.int8)
        
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                center_x = x * cell_size + cell_size // 2
                center_y = y * cell_size + cell_size // 2
                rgb = tuple(map(int, frame[center_y, center_x]))
                rgb_grid[y, x] = rgb
                type_grid[y, x] = self._match_color(rgb)
                self._draw_cell_overlay(frame, x * cell_size, y * cell_size, 
                                      cell_size, rgb, type_grid[y, x])
        
        return frame, rgb_grid, type_grid

    def _match_color(self, rgb, threshold=30):
        """Find closest color match with threshold (overflow-safe)"""
        for color, type_id in self.color_to_type.items():
            diff = sum(abs(int(c1) - int(c2)) for c1, c2 in zip(rgb, color))
            if diff < threshold:
                return type_id
        return -1  # Unknown type

    def _draw_cell_overlay(self, frame, x, y, size, rgb, type_id):
        """Draw cell annotations"""
        cv2.rectangle(frame, (x, y), (x+size, y+size), (0, 255, 0), 1)
        
        if self.rgb_display:
            cv2.putText(frame, f"{rgb[0]:02X}", (x+2, y+12), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255,255,255), 1)
            cv2.putText(frame, f"{rgb[1]:02X}", (x+2, y+24), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255,255,255), 1)
            cv2.putText(frame, f"{rgb[2]:02X}", (x+2, y+36), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255,255,255), 1)
        
        if self.type_display:
            alias = self.type_aliases.get(type_id, f"t{type_id}")
            cv2.putText(frame, alias, (x+5, y+size-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,0), 1)

    def toggle_grid(self): 
        self.grid_visible = not self.grid_visible
        print(f"Grid display {'ON' if self.grid_visible else 'OFF'}")

    def toggle_rgb(self): 
        self.rgb_display = not self.rgb_display
        print(f"RGB display {'ON' if self.rgb_display else 'OFF'}")

    def toggle_types(self): 
        self.type_display = not self.type_display
        print(f"Type display {'ON' if self.type_display else 'OFF'}")