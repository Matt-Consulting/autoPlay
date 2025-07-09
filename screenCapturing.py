# screenCapturing.py (updated)
import cv2
import numpy as np
import os
import time
import subprocess
from mss import mss
from datetime import datetime

class ScreenCapturer:
    def __init__(self, output_dir="screenshots", capture_interval=2, difference_threshold=1000):
        self.OUTPUT_DIR = output_dir
        self.CAPTURE_INTERVAL = capture_interval
        self.DIFFERENCE_THRESHOLD = difference_threshold
        self.setup_output_dir()
        self.sct = mss()
        self.monitor = self.get_window_geometry()
        self.last_saved_screenshot = None

    def setup_output_dir(self):
        """Creates the output directory if it doesn't exist."""
        if not os.path.exists(self.OUTPUT_DIR):
            os.makedirs(self.OUTPUT_DIR)
            print(f"Created output directory: {self.OUTPUT_DIR}")

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

        if self.are_images_different(self.last_saved_screenshot, screenshot_rgb):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{self.OUTPUT_DIR}/{prefix}_{timestamp}.png"
            cv2.imwrite(filename, cv2.cvtColor(screenshot_rgb, cv2.COLOR_RGB2BGR))
            print(f"Saved new unique screenshot: {filename}")
            self.last_saved_screenshot = screenshot_rgb
            return filename
        return None

    def continuous_capture(self):
        """Runs continuous capture with preview window."""
        print("\n--- Screen Capture Started ---")
        print("Press 'q' in the preview window to quit.")
        
        try:
            while True:
                if self.CAPTURE_INTERVAL > 0:
                    self.capture_screenshot()
                    preview_rgba = np.array(self.sct.grab(self.monitor))
                    preview_bgr = cv2.cvtColor(preview_rgba, cv2.COLOR_RGBA2BGR)
                    cv2.imshow("Live Preview (Press 'q' to quit)", preview_bgr)
                    time.sleep(self.CAPTURE_INTERVAL)
                else:
                    preview_rgba = np.array(self.sct.grab(self.monitor))
                    preview_bgr = cv2.cvtColor(preview_rgba, cv2.COLOR_RGBA2BGR)
                    cv2.imshow("Live Preview (Press 's' to save, 'q' to quit)", preview_bgr)
                    key = cv2.waitKey(25) & 0xFF
                    if key == ord('s'):
                        self.capture_screenshot(prefix="manual")
                    elif key == ord('q'):
                        break
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            cv2.destroyAllWindows()
            print("--- Screen Capture Terminated ---")

def main():
    capturer = ScreenCapturer()
    capturer.continuous_capture()

if __name__ == "__main__":
    main()