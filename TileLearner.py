#!/venv/bin/python3
"""
Tile Learner Class
Handles discovery and learning of new tile RGB values with probability tracking
"""

import time
from collections import defaultdict

class TileLearner:
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.player_pos = (7, 7)  # Fixed player position (0-indexed)
        self.adjacent_offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        # RGB value tracking
        self.rgb_beliefs = defaultdict(dict)  # {position: {rgb_value: count}}
        self.observation_counts = defaultdict(int)  # {position: total_count}
        self.candidate_positions = set()  # Positions ready for suggestion
        self.most_recent_candidate = None  # Track the most recent candidate
        
        # Learning parameters
        self.min_observations = 20  # Minimum observations before suggesting
        self.max_rgb_options = 3  # Max RGB values to track per position
        self.learning_enabled = True  # Add this line

    def toggle_learning(self):
        """Toggle the learning process on/off"""
        self.learning_enabled = not self.learning_enabled
        status = "ON" if self.learning_enabled else "OFF"
        print(f"\nTile learning {status}")

    def reset_learning(self):
        """Reset all learning progress and observations"""
        self.rgb_beliefs = defaultdict(dict)
        self.observation_counts = defaultdict(int)
        self.candidate_positions = set()
        self.most_recent_candidate = None
        print("\nLearning process has been reset - all observations cleared")

    def process_grid(self, rgb_grid, alias_grid):
        """Process grid to discover unknown tiles"""
        if not self.learning_enabled:  # Add this check
            return

        """Process grid to discover unknown tiles"""
        if rgb_grid is None or alias_grid is None:
            return

        # Only process if player is at known position
        if alias_grid[self.player_pos[1]][self.player_pos[0]] != "player":
            return

        px, py = self.player_pos
        
        # Check adjacent tiles
        for dx, dy in self.adjacent_offsets:
            x, y = px + dx, py + dy
            if 0 <= x < len(alias_grid[0]) and 0 <= y < len(alias_grid):
                if alias_grid[y][x] == "unknown":
                    self._update_rgb_beliefs((x, y), tuple(rgb_grid[y][x]))

    def _update_rgb_beliefs(self, position, rgb_value):
        """Update RGB belief counts for a position"""
        # Increment count for this RGB value at this position
        if rgb_value not in self.rgb_beliefs[position]:
            self.rgb_beliefs[position][rgb_value] = 0
        self.rgb_beliefs[position][rgb_value] += 1
        self.observation_counts[position] += 1
        
        # Prune to only keep top N RGB values
        if len(self.rgb_beliefs[position]) > self.max_rgb_options:
            # Remove least observed RGB value
            min_rgb = min(self.rgb_beliefs[position].items(), key=lambda x: x[1])[0]
            del self.rgb_beliefs[position][min_rgb]
        
        # Check if ready to suggest
        if self.observation_counts[position] >= self.min_observations:
            self.candidate_positions.add(position)
            self.most_recent_candidate = position
            self._suggest_new_tile(position)

    def _get_top_rgb_values(self, position):
        """Return top RGB values by observation count"""
        rgb_counts = self.rgb_beliefs[position]
        total = self.observation_counts[position]
        sorted_rgbs = sorted(rgb_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            (rgb, count, count/total) 
            for rgb, count in sorted_rgbs[:self.max_rgb_options]
        ]

    def _suggest_new_tile(self, position):
        """Suggest a new tile to be saved"""
        top_rgbs = self._get_top_rgb_values(position)
        total_obs = self.observation_counts[position]
        
        print(f"\nTile Suggestion Ready at position {position}:")
        print(f"Total observations: {total_obs}")
        print("Top RGB values:")
        
        for i, (rgb, count, confidence) in enumerate(top_rgbs, 1):
            print(f"{i}. RGB({rgb[0]}, {rgb[1]}, {rgb[2]}) - "
                  f"{count} obs ({confidence:.1%})")
        
        print("Press 's' to save the most likely RGB value(s)")

    def save_new_tiles(self):
        """Save the most recent candidate tile to mappings"""
        if not self.most_recent_candidate:
            print("No candidate tiles ready for saving")
            return False
        
        position = self.most_recent_candidate
        top_rgbs = self._get_top_rgb_values(position)
        
        if not top_rgbs:
            print("No RGB values found for this position")
            return False
            
        new_alias = self._generate_alias()
        type_id = self.analyzer.next_type_id
        
        # Determine if this is a single RGB or multiple (for animation)
        if len(top_rgbs) == 1:
            # Single RGB value
            rgb, count, confidence = top_rgbs[0]
            rgb_key = f"{rgb[0]},{rgb[1]},{rgb[2]}"
            
            self.analyzer.color_to_type[rgb_key] = type_id
            self.analyzer.type_aliases[str(type_id)] = new_alias
            self.analyzer.tile_properties[new_alias] = {
                'walkable': True,  # Default assumption
                'interactable': False,  # Default assumption
                'learned': True,
                'rgb': rgb_key
            }
        else:
            # Multiple RGB values (animation frames)
            rgb_values = [rgb for rgb, count, confidence in top_rgbs]
            
            self.analyzer.type_aliases[str(type_id)] = new_alias
            self.analyzer.tile_properties[new_alias] = {
                'walkable': True,  # Default for NPCs
                'interactable': True,  # Default for NPCs
                'learned': True,
                'animation_frames': {
                    'default': [f"{rgb[0]},{rgb[1]},{rgb[2]}" for rgb in rgb_values]
                }
            }
            # Map all RGB values to same type
            for rgb in rgb_values:
                rgb_key = f"{rgb[0]},{rgb[1]},{rgb[2]}"
                self.analyzer.color_to_type[rgb_key] = type_id
        
        self.analyzer.next_type_id += 1
        self.analyzer._save_mappings()
        
        # Clean up
        del self.rgb_beliefs[position]
        del self.observation_counts[position]
        self.candidate_positions.discard(position)
        self.most_recent_candidate = None
        
        print(f"\nSaved new tile: {new_alias}")
        if len(top_rgbs) > 1:
            print("As animated tile with RGB values:")
            for rgb, count, confidence in top_rgbs:
                print(f"- RGB({rgb[0]}, {rgb[1]}, {rgb[2]})")
        else:
            rgb = top_rgbs[0][0]
            print(f"RGB: ({rgb[0]}, {rgb[1]}, {rgb[2]})")
        print(f"From {self.observation_counts[position]} observations")
        return True

    def _generate_alias(self):
        """Generate next available alphabetical alias"""
        existing = [a for a in self.analyzer.type_aliases.values() 
                   if len(a) == 1 and a.isalpha()]
        return chr(65 + len(existing))  # A, B, C, etc.

    def get_observation_stats(self):
        """Return observation statistics"""
        return {
            'positions_observed': len(self.observation_counts),
            'candidates_ready': len(self.candidate_positions),
            'total_observations': sum(self.observation_counts.values())
        }