#!/venv/bin/python3
import cv2
import numpy as np
import subprocess
import time
from pathlib import Path
import pyautogui
import json

class DragonWarriorSensor:
    def __init__(self, grid_visible=True, rgb_display=False):
        self.rgb_window = None  # Renamed from diagnostic_window
        self.grid_visible = grid_visible
        self.rgb_display = rgb_display
        self.window_geometry = self._get_window_geometry()
        
        # Grid configuration
        self.GRID_SIZE = 15
        self.TILE_SIZE = 16

    def _get_window_geometry(self):
        """Get window geometry using xdotool with automatic retries"""
        result = subprocess.run(
            ['xdotool', 'search', '--name', 'Mesen - Dragon Warrior'],
            capture_output=True, text=True, timeout=2
        )
        window_ids = result.stdout.strip().split('\n')
        
        if not window_ids or not window_ids[0]:
            raise ValueError("Mesen window not found")
        
        for window_id in window_ids:
            try:
                result = subprocess.run(
                    ['xdotool', 'getwindowgeometry', window_id],
                    capture_output=True, text=True, timeout=2
                )
                geometry = result.stdout
                
                lines = [line.strip() for line in geometry.split('\n') if line.strip()]
                if len(lines) < 3:
                    continue
                    
                pos_line = lines[1]
                if '(' in pos_line:
                    pos_part = pos_line.split('(')[0].split(':')[1].strip()
                    x, y = map(int, pos_part.split(','))
                else:
                    pos_part = pos_line.split(':')[1].replace(',', '').strip()
                    x, y = map(int, pos_part.split('+'))
                
                size_part = lines[2].split(':')[1].strip()
                width, height = map(int, size_part.split('x'))
                
                print(f"Window geometry: x={x}, y={y}, width={width}, height={height}")
                return {
                    "left": x + 6,
                    "top": y - 40,
                    "width": 240,
                    "height": 240
                }
                
            except (IndexError, ValueError) as e:
                continue

    def _create_rgb_window(self, rgb_grid):
        """Create window showing RGB values for each tile"""
        scale_factor = 4
        h, w = rgb_grid.shape[0], rgb_grid.shape[1]
        rgb_img = np.zeros((h*scale_factor*10, w*scale_factor*10, 3), dtype=np.uint8)
        
        for y in range(h):
            for x in range(w):
                r, g, b = rgb_grid[y, x]
                px = x * scale_factor * 10 + 5
                py = y * scale_factor * 10 + 5
                
                # Draw colored rectangle (BGR order for OpenCV)
                cv2.rectangle(rgb_img, 
                            (px, py), 
                            (px + scale_factor*8, py + scale_factor*8),
                            (int(b), int(g), int(r)), -1)
                
                # Show RGB values
                cv2.putText(rgb_img, f"R:{r:03}",
                          (px, py + scale_factor*3),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255,255,255), 1)
                cv2.putText(rgb_img, f"G:{g:03}",
                          (px, py + scale_factor*5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255,255,255), 1)
                cv2.putText(rgb_img, f"B:{b:03}",
                          (px, py + scale_factor*7),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255,255,255), 1)
        
        return rgb_img
    
    def capture_frame(self, debug=False):
        """Capture and process game frame using PyAutoGUI"""
        try:
            # Capture screen region with PyAutoGUI
            screenshot = pyautogui.screenshot(
                region=(
                    self.window_geometry["left"],
                    self.window_geometry["top"],
                    self.window_geometry["width"],
                    self.window_geometry["height"]
                )
            )
            
            # Convert to numpy array and then to RGB format
            frame_rgb = np.array(screenshot)

            if debug:
                debug_file = Path("debug_capture.png")
                cv2.imwrite(str(debug_file), frame_rgb)

            if self.grid_visible:
                frame, rgb_grid = self._process_frame(frame_rgb)
                if self.rgb_display:
                    rgb_img = self._create_rgb_window(rgb_grid)
                    if self.rgb_window is None:
                        self.rgb_window = "Tile RGB Values"
                        cv2.namedWindow(self.rgb_window, cv2.WINDOW_NORMAL)
                        cv2.resizeWindow(self.rgb_window, 650, 700)
                    cv2.imshow(self.rgb_window, rgb_img)
                
                return frame, rgb_grid, None
            else:
                # When grid is disabled, return the frame with None for rgb_grid
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
        
        for grid_y in range(self.GRID_SIZE):
            for grid_x in range(self.GRID_SIZE):
                x_start = grid_x * cell_size + 2
                x_end = x_start + cell_size - 4
                y_pos = grid_y * cell_size + cell_size // 2
                
                row_segment = frame[y_pos, x_start:x_end]
                avg_rgb = np.mean(row_segment, axis=0).astype(np.uint8)
                rgb_grid[grid_y, grid_x] = [avg_rgb[0], avg_rgb[1], avg_rgb[2]]
                
                self._draw_cell_overlay(frame, 
                                     grid_x * cell_size, 
                                     grid_y * cell_size,
                                     cell_size, 
                                     rgb_grid[grid_y, grid_x])
        
        return frame, rgb_grid

    def _draw_cell_overlay(self, frame, x, y, size, rgb):
        """Draw cell annotations"""
        cv2.rectangle(frame, (x, y), (x+size, y+size), (0, 255, 0), 1)

    def toggle_grid(self): 
        self.grid_visible = not self.grid_visible
        print(f"Grid display {'ON' if self.grid_visible else 'OFF'}")

    def toggle_rgb(self): 
        self.rgb_display = not self.rgb_display
        if not self.rgb_display and self.rgb_window is not None:
            cv2.destroyWindow(self.rgb_window)
            self.rgb_window = None
        print(f"RGB display {'ON' if self.rgb_display else 'OFF'}")