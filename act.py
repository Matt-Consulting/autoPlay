#!/venv/bin/python3
"""
Game Interaction Controller - Non-Blocking Version
Handles emulator input using counter-based timing
"""

import time
import subprocess
from pynput.keyboard import Controller, Key

class Action:
    def __init__(self):
        self.keyboard = Controller()
        self.emulator_window = None
        self._find_emulator_window()
        
        # Key mappings
        self.KEY_MAP = {
            'up': Key.up,
            'down': Key.down,
            'left': Key.left,
            'right': Key.right,
            'b': 'a',
            'a': 's',
            'select': 'z',
            'start': 'x',
            'load_1': Key.f1,
            'load_2': Key.f2,
            'load_3': Key.f3,
            'save_1': [Key.shift, Key.f1],
            'save_2': [Key.shift, Key.f2],
            'save_3': [Key.shift, Key.f3]
        }
        
        # Action state tracking
        self.current_action = None
        self.action_remaining = 0
        self.loops_per_second = 30  # Target loop frequency

    def _find_emulator_window(self):
        """Locate the emulator window using xdotool"""
        try:
            result = subprocess.run(
                ['xdotool', 'search', '--name', 'Mesen'],
                capture_output=True, text=True
            )
            if result.stdout.strip():
                self.emulator_window = result.stdout.strip().split('\n')[0]
        except Exception as e:
            print(f"Window finding error: {e}")

    def _focus_emulator(self):
        """Bring emulator window to focus if not already focused"""
        if self.emulator_window:
            subprocess.run(['xdotool', 'windowactivate', self.emulator_window],
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL)

    def start_action(self, action, duration_sec):
        """Begin a new non-blocking action"""
        if action not in self.KEY_MAP:
            raise ValueError(f"Unknown action: {action}")
        
        self._focus_emulator()
        self.current_action = action
        self.action_remaining = int(duration_sec * self.loops_per_second)
        self._execute_key_press(True)  # Initial key press

    def update(self):
        """Update action state - call each main loop iteration"""
        if self.action_remaining > 0:
            self.action_remaining -= 1
            if self.action_remaining == 0:
                self._execute_key_press(False)  # Final key release
                self.current_action = None
            return True
        return False

    def _execute_key_press(self, press):
        """Handle the actual key press/release"""
        key = self.KEY_MAP[self.current_action]
        
        if isinstance(key, list):
            if press:
                self.keyboard.press(Key.shift)
                self.keyboard.press(key[1])
            else:
                self.keyboard.release(key[1])
                self.keyboard.release(Key.shift)
        else:
            if press:
                self.keyboard.press(key)
            else:
                self.keyboard.release(key)

    def start_move(self, direction):
        """Start a movement action (0.4s duration)"""
        self.start_action(direction, 0.4)

    def update(self):
        """Update action state - returns True if action in progress"""
        if self.action_remaining > 0:
            self.action_remaining -= 1
            if self.action_remaining == 0:
                self._execute_key_press(False)
                self.current_action = None
            return True
        return False

    def start_state_load(self, slot):
        """Start a state load action"""
        self.start_action(f'load_{slot}', 0.2)

    def start_state_save(self, slot):
        """Start a state save action"""
        self.start_action(f'save_{slot}', 0.2)

if __name__ == "__main__":
    # Example usage
    action = Action()
    print("Testing non-blocking controls...")
    
    # In your main loop you would do:
    action.start_state_load(1)
    while action.update():
        time.sleep(1/action.loops_per_second)
    
    action.start_move('right')
    while action.update():
        time.sleep(1/action.loops_per_second)