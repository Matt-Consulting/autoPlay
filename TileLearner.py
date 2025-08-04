#!/venv/bin/python3
"""
Tile Learner Class with POMDP-style belief state
Handles probabilistic discovery and learning of new tiles
"""

import numpy as np

class TileLearner:
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.player_pos = (7, 7)  # Fixed player position (0-indexed)
        self.adjacent_offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        # Belief state tracking
        self.tile_beliefs = {}  # {color_key: {'walkable': belief, 'interactable': belief}}
        self.observation_counts = {}  # {color_key: count}
        self.candidate_tiles = {}  # Tiles ready for suggestion
        
        # Learning parameters
        self.walkable_prior = 0.7  # Initial belief that new tiles are walkable
        self.interactable_prior = 0.3
        self.confidence_threshold = 0.85  # Required confidence to suggest
        self.min_observations = 5  # Minimum observations before suggesting

    def process_grid(self, rgb_grid, alias_grid):
        """Process grid to discover and learn about unknown tiles"""
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
                    self._update_belief_state(rgb_grid[y][x])

    def _update_belief_state(self, rgb_value):
        """Update belief state for observed unknown tile"""
        color_key = f"{rgb_value[2]},{rgb_value[1]},{rgb_value[0]}"
        
        # Initialize beliefs if new tile
        if color_key not in self.tile_beliefs:
            self.tile_beliefs[color_key] = {
                'walkable': self.walkable_prior,
                'interactable': self.interactable_prior
            }
            self.observation_counts[color_key] = 0
        
        # Increment observation count
        self.observation_counts[color_key] += 1
        
        # Get current interaction observations (simplified - needs real game feedback)
        # In a full implementation, these would come from actual player interactions
        walk_observed = True  # Default assumption
        interact_observed = False  # Default assumption
        
        # Update beliefs using Bayesian learning
        walk_prior = self.tile_beliefs[color_key]['walkable']
        interact_prior = self.tile_beliefs[color_key]['interactable']
        
        # Simplified belief update (would be more sophisticated in full POMDP)
        self.tile_beliefs[color_key]['walkable'] = self._update_belief(
            walk_prior, walk_observed, learning_rate=0.1)
        self.tile_beliefs[color_key]['interactable'] = self._update_belief(
            interact_prior, interact_observed, learning_rate=0.05)
        
        # Check if ready to suggest
        self._check_suggestion_threshold(color_key)

    def _update_belief(self, prior, observed, learning_rate=0.1):
        """Update a single belief value"""
        if observed:
            return min(1.0, prior + learning_rate * (1 - prior))
        else:
            return max(0.0, prior - learning_rate * prior)

    def _check_suggestion_threshold(self, color_key):
        """Check if beliefs meet confidence threshold"""
        if self.observation_counts[color_key] < self.min_observations:
            return
            
        beliefs = self.tile_beliefs[color_key]
        walk_conf = max(beliefs['walkable'], 1 - beliefs['walkable'])
        interact_conf = max(beliefs['interactable'], 1 - beliefs['interactable'])
        
        if walk_conf >= self.confidence_threshold and interact_conf >= self.confidence_threshold/2:
            self.candidate_tiles[color_key] = {
                'walkable': beliefs['walkable'] > 0.5,
                'interactable': beliefs['interactable'] > 0.5,
                'observations': self.observation_counts[color_key]
            }
            self._suggest_new_tile(color_key)

    def _suggest_new_tile(self, color_key):
        """Suggest a new tile to be saved"""
        candidate = self.candidate_tiles[color_key]
        print(f"\nTile Suggestion Ready:")
        print(f"RGB: {color_key}")
        print(f"Observations: {candidate['observations']}")
        print(f"Properties:")
        print(f"- Walkable: {candidate['walkable']} (confidence: {self.tile_beliefs[color_key]['walkable']:.2f})")
        print(f"- Interactable: {candidate['interactable']} (confidence: {self.tile_beliefs[color_key]['interactable']:.2f})")
        print("Press 's' to save or keep observing")

    def save_new_tiles(self):
        """Save candidate tiles to mappings"""
        if not self.candidate_tiles:
            print("No candidate tiles ready for saving")
            return False
        
        new_tiles = []
        for color_key, props in self.candidate_tiles.items():
            new_alias = self._generate_alias()
            type_id = self.analyzer.next_type_id
            
            self.analyzer.color_to_type[color_key] = type_id
            self.analyzer.type_aliases[str(type_id)] = new_alias
            self.analyzer.tile_properties[new_alias] = {
                'walkable': props['walkable'],
                'interactable': props['interactable'],
                'learned': True,
                'rgb': color_key,
                'confidence': {
                    'walkable': float(self.tile_beliefs[color_key]['walkable']),
                    'interactable': float(self.tile_beliefs[color_key]['interactable'])
                }
            }
            self.analyzer.next_type_id += 1
            new_tiles.append((new_alias, color_key, props['observations']))
        
        if new_tiles:
            self.analyzer._save_mappings()
            # Clear saved candidates from tracking
            for color_key in self.candidate_tiles.keys():
                del self.tile_beliefs[color_key]
                del self.observation_counts[color_key]
            self.candidate_tiles = {}
            
            print("\nSaved new tiles:")
            for alias, color, count in new_tiles:
                print(f"- {alias}: {color} (from {count} observations)")
            return True
        return False

    def _generate_alias(self):
        """Generate next available alphabetical alias"""
        existing = [a for a in self.analyzer.type_aliases.values() 
                   if len(a) == 1 and a.isalpha()]
        return chr(65 + len(existing))  # A, B, C, etc.

    def get_observation_stats(self):
        """Return observation statistics"""
        return {
            'total_observed': len(self.observation_counts),
            'candidates_ready': len(self.candidate_tiles),
            'total_observations': sum(self.observation_counts.values())
        }