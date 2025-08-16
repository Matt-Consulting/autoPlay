#!/venv/bin/python3
"""
Main Thinking Controller with POMDP learning and World Mapping
Coordinates tile analysis, probabilistic learning, and world mapping
"""

from TileAnalyzer import TileAnalyzer
from TileLearner import TileLearner
from mapping import WorldMapper

class Think:
    def __init__(self, mappings_file="type_mappings.json"):
        self.analyzer = TileAnalyzer(mappings_file)
        self.learner = TileLearner(self.analyzer)
        self.mapper = WorldMapper(self.analyzer)
        self.show_types = False
        self.show_diag = False
        self.show_map = False
        self.player_global_pos = (128, 128)  # Starting in middle of 256x256 map

    def process_frame(self, rgb_grid):
        """Process a frame through analysis, learning, and mapping"""
        alias_grid = self.analyzer.analyze_grid(rgb_grid)
        
        if alias_grid is not None:
            # Process learning (automatically checks player position)
            self.learner.process_grid(rgb_grid, alias_grid)
            
            if self.show_diag:
                self.analyzer.show_diagnostics(alias_grid)
            else:
                self.analyzer.close_diagnostics()
        
        return alias_grid
    
    def update_player_position(self, dx, dy):
        """Update player's global position based on movement"""
        self.player_global_pos = (
            self.player_global_pos[0] + dx,
            self.player_global_pos[1] + dy
        )
    
    def reset_learning(self):
        """Reset the learning process"""
        self.learner.reset_learning()

    def toggle_map(self):
        """Toggle diagnostics window"""
        self.show_map = not self.show_map
        self.mapper.toggle_map()

    def save_discovered_tiles(self):
        """Save candidate tiles with confirmation"""
        stats = self.learner.get_observation_stats()
        if stats['candidates_ready'] == 0:
            print("No tiles meet confidence thresholds yet")
            return False
            
        print(f"\nAbout to save {stats['candidates_ready']} tiles:")
        print(f"Average confidence: {stats['average_confidence']:.1%}")
        return self.learner.save_new_tiles()

    def toggle_diagnostics(self):
        """Toggle diagnostics window"""
        self.show_diag = not self.show_diag
        print(f"Diagnostics display {'ON' if self.show_diag else 'OFF'}")
        if not self.show_diag:
            self.analyzer.close_diagnostics()

    def toggle_learning(self):
        """Toggle the learning process on/off"""
        self.learner.toggle_learning()

    def get_learning_stats(self):
        """Return current learning statistics"""
        return self.learner.get_observation_stats()

if __name__ == "__main__":
    print("Initializing Think controller with POMDP learning and world mapping...")
    controller = Think()