#!/venv/bin/python3
"""
Main Thinking Controller with POMDP learning
Coordinates tile analysis and probabilistic learning
"""

from TileAnalyzer import TileAnalyzer
from TileLearner import TileLearner

class Think:
    def __init__(self, mappings_file="type_mappings.json"):
        self.analyzer = TileAnalyzer(mappings_file)
        self.learner = TileLearner(self.analyzer)
        self.show_types = False
        self.show_diag = False

    def process_frame(self, rgb_grid):
        """Process a frame through analysis and learning"""
        alias_grid = self.analyzer.analyze_grid(rgb_grid)
        
        if alias_grid is not None:
            # Process learning (automatically checks player position)
            self.learner.process_grid(rgb_grid, alias_grid)
            
            if self.show_diag:
                self.analyzer.show_diagnostics(alias_grid)
            else:
                self.analyzer.close_diagnostics()
        
        return alias_grid
    
    def reset_learning(self):
        """Reset the learning process"""
        self.learner.reset_learning()

    def _print_types(self, alias_grid):
        """Print tile types with learning stats"""
        stats = self.learner.get_observation_stats()
        print("\nCurrent Tile Types:")
        for row in alias_grid:
            print(" ".join(row))
        print(f"\nLearning Stats:")
        print(f"- Unique tiles observed: {stats['total_observed']}")
        print(f"- Total observations: {stats['total_observations']}")
        print(f"- Candidates ready: {stats['candidates_ready']}")

    def save_discovered_tiles(self):
        """Save candidate tiles with confirmation"""
        stats = self.learner.get_observation_stats()
        if stats['candidates_ready'] == 0:
            print("No tiles meet confidence thresholds yet")
            return False
            
        print(f"\nAbout to save {stats['candidates_ready']} tiles:")
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

if __name__ == "__main__":
    print("Initializing Think controller with POMDP learning...")
    controller = Think()