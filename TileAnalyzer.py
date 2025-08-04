#!/venv/bin/python3
"""
Base Tile Analyzer Class
Handles fundamental tile classification and diagnostics
"""

import json
from pathlib import Path
import cv2
import numpy as np

class TileAnalyzer:
    def __init__(self, mappings_file="type_mappings.json"):
        self.mappings_file = Path(mappings_file)
        self.color_to_type = {}
        self.type_aliases = {}
        self.tile_properties = {}
        self.next_type_id = 0
        self.diag_window = None
        self._load_mappings()

    def _load_mappings(self):
        """Load tile type mappings from JSON file"""
        try:
            if not self.mappings_file.exists():
                self._create_default_mappings()
                return

            with open(self.mappings_file, 'r') as f:
                data = json.load(f)
            
            self.color_to_type = data.get("color_to_type", {})
            self.type_aliases = data.get("type_aliases", {})
            self.tile_properties = data.get("tile_properties", {})
            self.next_type_id = data.get("next_type_id", 0)
            
        except Exception as e:
            print(f"Error loading mappings: {e}")
            self._create_default_mappings()

    def _create_default_mappings(self):
        """Create default empty mappings"""
        self.color_to_type = {}
        self.type_aliases = {}
        self.tile_properties = {
            "block": {"walkable": False, "interactable": False},
            "brick": {"walkable": True, "interactable": True},
            "player": {
                "walkable": False,
                "interactable": False,
                "is_player": True,
                "animation_frames": {
                    "left": ["151,130,198", "155,123,159"],
                    "up": ["129,127,255"],
                    "down": ["144,133,251"],
                    "right": ["170,127,181", "188,134,201"]
                },
                "current_direction": "down"
            },
            "unknown": {"walkable": True, "interactable": False}
        }
        self.next_type_id = 0
        self._save_mappings()

    def _save_mappings(self):
        """Save current mappings to file"""
        data = {
            "color_to_type": self.color_to_type,
            "type_aliases": self.type_aliases,
            "tile_properties": self.tile_properties,
            "next_type_id": self.next_type_id
        }
        with open(self.mappings_file, 'w') as f:
            json.dump(data, f, indent=2)

    def analyze_grid(self, rgb_grid):
        """Convert RGB grid to tile type aliases grid"""
        if rgb_grid is None:
            return None
            
        alias_grid = []
        for row in rgb_grid:
            alias_row = []
            for pixel in row:
                color_key = f"{pixel[2]},{pixel[1]},{pixel[0]}"
                type_id = self.color_to_type.get(color_key, -1)
                alias = self.type_aliases.get(str(type_id), "unknown")
                alias_row.append(alias)
            alias_grid.append(alias_row)
        return alias_grid

    def show_diagnostics(self, alias_grid):
        """Create diagnostics window with tile information"""
        if alias_grid is None:
            return

        scale_factor = 4
        h, w = len(alias_grid), len(alias_grid[0])
        diag_img = np.zeros((h*scale_factor*10, w*scale_factor*10, 3), dtype=np.uint8)
        
        for y in range(h):
            for x in range(w):
                alias = alias_grid[y][x]
                properties = self.tile_properties.get(alias, {})
                px = x * scale_factor * 10 + 5
                py = y * scale_factor * 10 + 5
                
                # Determine tile color
                if alias == "player":
                    bg_color = (255, 0, 0)  # Blue
                elif alias == "unknown":
                    bg_color = (100, 100, 100)  # Grey
                elif properties.get("walkable"):
                    bg_color = (0, 255, 0)  # Green
                else:
                    bg_color = (0, 0, 255)  # Red
                
                # Draw tile and text
                cv2.rectangle(diag_img, (px, py), (px + scale_factor*8, py + scale_factor*8), bg_color, -1)
                text_color = (0, 0, 0) if alias == "player" else (255, 255, 255)
                cv2.putText(diag_img, alias, (px, py + scale_factor*3), cv2.FONT_HERSHEY_SIMPLEX, 0.3, text_color, 1)
                
                if alias != "player":
                    cv2.putText(diag_img, f"Walk: {'Y' if properties.get('walkable') else 'N'}", 
                              (px, py + scale_factor*5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, text_color, 1)
                    cv2.putText(diag_img, f"Intr: {'Y' if properties.get('interactable') else 'N'}", 
                              (px, py + scale_factor*7), cv2.FONT_HERSHEY_SIMPLEX, 0.3, text_color, 1)
        
        if self.diag_window is None:
            self.diag_window = "Tile Diagnostics"
            cv2.namedWindow(self.diag_window, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.diag_window, 800, 800)
        
        cv2.imshow(self.diag_window, diag_img)

    def close_diagnostics(self):
        """Close diagnostics window if open"""
        if self.diag_window is not None:
            cv2.destroyWindow(self.diag_window)
            self.diag_window = None