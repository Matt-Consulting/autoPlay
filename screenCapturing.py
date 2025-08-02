# screenCapturing.py (with manual color mapping)
import cv2
import numpy as np
import os
import time
import subprocess
from mss import mss
from datetime import datetime
import json

class ScreenCapturer:
    def __init__(self, output_dir="screenshots", capture_interval=2, difference_threshold=1000):
        self.OUTPUT_DIR = output_dir
        self.CAPTURE_INTERVAL = capture_interval
        self.DIFFERENCE_THRESHOLD = difference_threshold
        self.setup_output_dir()
        self.sct = mss()
        self.monitor = self.get_window_geometry()
        self.last_saved_screenshot = None
        self.grid_visible = True
        self.rgb_values_visible = False
        self.type_mapping_visible = False
        self.grid_size = 16
        
        # Initialize color mapping system
        self.color_to_type = {}
        self.type_aliases = {}
        self.next_type_id = 0
        self.load_type_mappings()
        self.unmapped_colors = set()  # Track seen but unmapped colors
        
    def setup_output_dir(self):
        """Creates the output directory if it doesn't exist."""
        if not os.path.exists(self.OUTPUT_DIR):
            os.makedirs(self.OUTPUT_DIR)
            print(f"Created output directory: {self.OUTPUT_DIR}")

    def load_type_mappings(self):
        """Load type mappings from file if it exists."""
        mapping_file = os.path.join(self.OUTPUT_DIR, "type_mappings.json")
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r') as f:
                data = json.load(f)
                self.color_to_type = {tuple(map(int, k.split(','))): v for k, v in data['color_to_type'].items()}
                self.type_aliases = data['type_aliases']
                self.next_type_id = data.get('next_type_id', len(self.color_to_type))
            print("Loaded existing type mappings")
        else:
            # Initialize with some common mappings if file doesn't exist
            self.add_color_mapping((0x84, 0x84, 0x84), 0, "block")
            self.add_color_mapping((0x28, 0x2F, 0x60), 1, "brick")
            print("Initialized new type mappings")

    def save_type_mappings(self):
        """Save type mappings to file."""
        mapping_file = os.path.join(self.OUTPUT_DIR, "type_mappings.json")
        data = {
            'color_to_type': {f"{k[0]},{k[1]},{k[2]}": v for k, v in self.color_to_type.items()},
            'type_aliases': self.type_aliases,
            'next_type_id': self.next_type_id
        }
        with open(mapping_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved type mappings to {mapping_file}")

    def add_color_mapping(self, rgb, type_id=None, alias=None):
        """Add a new color to type mapping only if explicitly requested."""
        if type_id is None:
            type_id = self.next_type_id
            self.next_type_id += 1
        
        if rgb not in self.color_to_type:
            self.color_to_type[rgb] = type_id
            if alias:
                self.type_aliases[type_id] = alias
            self.save_type_mappings()
            if rgb in self.unmapped_colors:
                self.unmapped_colors.remove(rgb)
            return type_id
        return self.color_to_type[rgb]

    def get_type_for_color(self, rgb):
        """Get type ID for a given RGB color, returns -1 if unmapped."""
        return self.color_to_type.get(rgb, -1)

    def get_window_geometry(self):
        """Gets window geometry using xwininfo."""
        print("Please click on the game window to select it for screen capture...")
        try:
            xwininfo_output = subprocess.check_output(
                "xwininfo -id $(xdotool selectwindow)",
                shell=True,
                stderr=subprocess.PIPE
            ).decode()

            lines = xwininfo_output.split('\n')
            geometry = {
                "left": int(next(s for s in lines if "Absolute upper-left X" in s).split(':')[1].strip()),
                "top": int(next(s for s in lines if "Absolute upper-left Y" in s).split(':')[1].strip()),
                "width": int(next(s for s in lines if "Width" in s).split(':')[1].strip()),
                "height": int(next(s for s in lines if "Height" in s).split(':')[1].strip())
            }
            print(f"Successfully selected window. Capturing region: {geometry}")
            return geometry
        except Exception as e:
            print(f"Error during window selection: {e}. Falling back to default 256x256 region.")
            return {"top": 100, "left": 100, "width": 256, "height": 256}

    def calculate_grid_rgb(self, image):
        """Calculates average RGB values for each grid cell."""
        h, w = image.shape[:2]
        cell_width = 16
        cell_height = 16
        
        rgb_grid = np.zeros((self.grid_size, self.grid_size, 3), dtype=np.uint8)
        type_grid = np.zeros((self.grid_size, self.grid_size), dtype=np.int8)  # Use int8 to allow -1
        
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                # Define cell boundaries
                x1 = x * cell_width
                x2 = (x + 1) * cell_width
                y1 = y * cell_height
                y2 = (y + 1) * cell_height
                
                # Extract cell pixels
                cell = image[y1:y2, x1:x2]
                
                # Calculate mean RGB values (0-255)
                mean_rgb = tuple(np.mean(cell, axis=(0, 1)).astype(int))
                rgb_grid[y, x] = mean_rgb
                
                # Track unmapped colors
                if mean_rgb not in self.color_to_type:
                    self.unmapped_colors.add(mean_rgb)
                
                # Get type ID (-1 if unmapped)
                type_grid[y, x] = self.get_type_for_color(mean_rgb)
                
        return rgb_grid, type_grid

    def draw_grid(self, image):
        """Draws a 16x16 grid with labels and optional data displays."""
        h, w = image.shape[:2]
        cell_width = 16
        cell_height = 16
        
        # Calculate RGB and type values for each cell
        rgb_grid, type_grid = self.calculate_grid_rgb(image)
        
        # Draw grid lines
        for i in range(1, self.grid_size):
            # Vertical lines
            x = i * cell_width
            cv2.line(image, (x, 0), (x, h), (0, 255, 255), 1)
            # Horizontal lines
            y = i * cell_height
            cv2.line(image, (0, y), (w, y), (0, 255, 255), 1)
        
        # Draw row and column labels (0-F)
        for i in range(self.grid_size):
            # Column labels (top)
            label = format(i, 'X')
            x = i * cell_width + cell_width // 3
            cv2.putText(image, label, (x, 15), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.4, (0, 255, 255), 1)
            
            # Row labels (left)
            y = i * cell_height + cell_height // 3
            cv2.putText(image, label, (5, y), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.4, (0, 255, 255), 1)
        
        # Draw RGB values if enabled
        if self.rgb_values_visible:
            for y in range(self.grid_size):
                for x in range(self.grid_size):
                    center_x = x * cell_width + cell_width // 2
                    center_y = y * cell_height + cell_height // 2
                    
                    r, g, b = rgb_grid[y, x]
                    r_hex = format(r, '02X')
                    g_hex = format(g, '02X')
                    b_hex = format(b, '02X')
                    
                    cv2.putText(image, f"{r_hex}", 
                               (center_x - 15, center_y - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
                    cv2.putText(image, f"{g_hex}", 
                               (center_x - 15, center_y), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                    cv2.putText(image, f"{b_hex}", 
                               (center_x - 15, center_y + 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
        
        # Draw type mappings if enabled
        if self.type_mapping_visible:
            for y in range(self.grid_size):
                for x in range(self.grid_size):
                    center_x = x * cell_width + cell_width // 2
                    center_y = y * cell_height + cell_height // 2
                    
                    type_id = type_grid[y, x]
                    if type_id == -1:
                        # Show unmapped cells in red
                        cv2.putText(image, "NEW", 
                                   (center_x - 15, center_y + 5), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
                    else:
                        alias = self.type_aliases.get(type_id, f"t{type_id}")
                        cv2.putText(image, f"{type_id}:{alias[:4]}", 
                                   (center_x - 25, center_y + 5), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
        
        return image, rgb_grid, type_grid

    def are_images_different(self, img1, img2):
        """Compares two images for significant differences."""
        if img1 is None or img2 is None:
            return True
        diff = cv2.absdiff(img1, img2)
        return np.sum(diff) > self.DIFFERENCE_THRESHOLD

    def capture_screenshot(self, prefix="auto"):
        """Captures a single screenshot and saves it if different from last."""
        screenshot_rgba = np.array(self.sct.grab(self.monitor))
        screenshot_rgb = cv2.cvtColor(screenshot_rgba, cv2.COLOR_RGBA2RGB)
        
        if self.grid_visible:
            screenshot_rgb, rgb_grid, type_grid = self.draw_grid(screenshot_rgb.copy())
            self.print_analysis(rgb_grid, type_grid)
        else:
            rgb_grid, type_grid = self.calculate_grid_rgb(screenshot_rgb.copy())

        if self.are_images_different(self.last_saved_screenshot, screenshot_rgb):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{self.OUTPUT_DIR}/{prefix}_{timestamp}.png"
            cv2.imwrite(filename, cv2.cvtColor(screenshot_rgb, cv2.COLOR_RGB2BGR))
            print(f"Saved new unique screenshot: {filename}")
            self.last_saved_screenshot = screenshot_rgb
            return filename, rgb_grid, type_grid
        return None, None, None

    def print_analysis(self, rgb_grid, type_grid):
        """Prints the RGB and type grids to console."""
        print("\nRGB Grid Values (hexadecimal 00-FF):")
        print("   " + " ".join([f"{i:2X}" for i in range(self.grid_size)]))
        for y in range(self.grid_size):
            row_str = f"{y:X}: "
            for x in range(self.grid_size):
                r, g, b = rgb_grid[y, x]
                row_str += f"{r:02X}{g:02X}{b:02X} "
            print(row_str)
        
        print("\nType Grid Values:")
        print("   " + " ".join([f"{i:2X}" for i in range(self.grid_size)]))
        for y in range(self.grid_size):
            row_str = f"{y:X}: "
            for x in range(self.grid_size):
                type_id = type_grid[y, x]
                if type_id == -1:
                    row_str += "  NEW  "
                else:
                    alias = self.type_aliases.get(type_id, f"t{type_id}")
                    row_str += f"{alias[:6]:>6} "
            print(row_str)
        
        # Print legend of current mappings
        print("\nCurrent Type Mappings:")
        for rgb, type_id in sorted(self.color_to_type.items(), key=lambda x: x[1]):
            alias = self.type_aliases.get(type_id, "")
            print(f"Type {type_id:2}: {rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X} {alias}")
        
        # Print unmapped colors
        if self.unmapped_colors:
            print("\nUnmapped Colors (use 'm' to map):")
            for rgb in sorted(self.unmapped_colors):
                print(f"NEW: {rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}")

    def continuous_capture(self):
        """Runs continuous capture with preview window."""
        print("\n--- Screen Capture Started ---")
        print("Press 'q' in the preview window to quit.")
        print("Press 'g' to toggle grid visibility.")
        print("Press 'r' to toggle RGB values display.")
        print("Press 't' to toggle type mapping display.")
        print("Press 'm' to map a new color.")
        print("Press 'a' to add/edit a type alias.")
        
        try:
            while True:
                if self.CAPTURE_INTERVAL > 0:
                    self.capture_screenshot()
                    preview_rgba = np.array(self.sct.grab(self.monitor))
                    preview_bgr = cv2.cvtColor(preview_rgba, cv2.COLOR_RGBA2BGR)
                    
                    if self.grid_visible:
                        preview_bgr, _, _ = self.draw_grid(preview_bgr)
                    
                    cv2.imshow("Live Preview (Press 'q' to quit)", preview_bgr)
                    time.sleep(self.CAPTURE_INTERVAL)
                else:
                    preview_rgba = np.array(self.sct.grab(self.monitor))
                    preview_bgr = cv2.cvtColor(preview_rgba, cv2.COLOR_RGBA2BGR)
                    
                    if self.grid_visible:
                        preview_bgr, _, _ = self.draw_grid(preview_bgr)
                    
                    cv2.imshow("Live Preview (Press 's' to save, 'q' to quit)", preview_bgr)
                    key = cv2.waitKey(25) & 0xFF
                    if key == ord('s'):
                        filename, rgb_grid, type_grid = self.capture_screenshot(prefix="manual")
                        if filename:
                            print(f"Saved screenshot with analysis: {filename}")
                    elif key == ord('g'):
                        self.grid_visible = not self.grid_visible
                        print(f"Grid visibility: {'ON' if self.grid_visible else 'OFF'}")
                    elif key == ord('r'):
                        self.rgb_values_visible = not self.rgb_values_visible
                        print(f"RGB values display: {'ON' if self.rgb_values_visible else 'OFF'}")
                    elif key == ord('t'):
                        self.type_mapping_visible = not self.type_mapping_visible
                        print(f"Type mapping display: {'ON' if self.type_mapping_visible else 'OFF'}")
                    elif key == ord('m'):
                        self.map_new_color_interactive()
                    elif key == ord('a'):
                        self.add_type_alias_interactive()
                    elif key == ord('q'):
                        break
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            cv2.destroyAllWindows()
            print("--- Screen Capture Terminated ---")

    def map_new_color_interactive(self):
        """Interactive prompt to map a new color."""
        if not self.unmapped_colors:
            print("No unmapped colors found.")
            return
        
        print("\nUnmapped Colors:")
        for i, rgb in enumerate(sorted(self.unmapped_colors)):
            print(f"{i}: {rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}")
        
        try:
            choice = int(input("Enter number of color to map (or -1 to cancel): ").strip())
            if choice == -1:
                return
            rgb = sorted(self.unmapped_colors)[choice]
            
            print(f"\nMapping color {rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}")
            print("Current mappings:")
            for existing_rgb, type_id in sorted(self.color_to_type.items(), key=lambda x: x[1]):
                alias = self.type_aliases.get(type_id, "")
                print(f"Type {type_id:2}: {existing_rgb[0]:02X}{existing_rgb[1]:02X}{existing_rgb[2]:02X} {alias}")
            
            type_id = input("Enter type ID to assign (leave blank for new type): ").strip()
            if type_id:
                type_id = int(type_id)
            else:
                type_id = None
            
            alias = input("Enter alias for this type (optional): ").strip()
            if not alias:
                alias = None
            
            self.add_color_mapping(rgb, type_id, alias)
            print(f"Mapped {rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X} to type {self.color_to_type[rgb]}")
            
        except (ValueError, IndexError):
            print("Invalid selection")

    def add_type_alias_interactive(self):
        """Interactive prompt to add a new type alias."""
        print("\nCurrent type mappings:")
        for rgb, type_id in sorted(self.color_to_type.items(), key=lambda x: x[1]):
            alias = self.type_aliases.get(type_id, "")
            print(f"Type {type_id:2}: {rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X} {alias}")
        
        try:
            type_id = int(input("Enter type ID to alias: ").strip())
            if type_id not in set(self.color_to_type.values()):
                print("Invalid type ID")
                return
            
            current_alias = self.type_aliases.get(type_id, "")
            alias = input(f"Enter alias for type {type_id} [current: {current_alias}]: ").strip()
            if alias:
                self.type_aliases[type_id] = alias
                self.save_type_mappings()
                print(f"Updated alias for type {type_id}")
        except ValueError:
            print("Invalid input")

def main():
    capturer = ScreenCapturer()
    capturer.continuous_capture()

if __name__ == "__main__":
    main()