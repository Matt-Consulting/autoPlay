import os
import cv2
import shutil
from pathlib import Path
from datetime import datetime

# Directory setup
SCRIPT_DIR = Path(__file__).parent
SCREENSHOTS_DIR = SCRIPT_DIR / "screenshots"
ANNOTATED_DIR = SCRIPT_DIR / "annotated"
ANNOTATED_IMAGES = ANNOTATED_DIR / "images"
ANNOTATED_LABELS = ANNOTATED_DIR / "labels"

# Grid configuration
GRID_WIDTH = 15       # Number of tiles horizontally
GRID_HEIGHT = 15      # Number of tiles vertically
TILE_SIZE = 16        # Size of each tile in pixels
SCREEN_OFFSET_X = 16   # Horizontal offset from left edge of window
SCREEN_OFFSET_Y = 0  # Vertical offset from top edge of window

# Initialize with default classes
CLASSES = ["chest"]  # Predefined
current_selection = None
grid_visible = True

def setup_dirs():
    """Create required directories"""
    ANNOTATED_DIR.mkdir(parents=True, exist_ok=True)
    ANNOTATED_IMAGES.mkdir(parents=True, exist_ok=True)
    ANNOTATED_LABELS.mkdir(parents=True, exist_ok=True)

def save_legend():
    """Save class ID mapping to _legend.txt"""
    legend_path = ANNOTATED_LABELS / "_legend.txt"
    with open(legend_path, 'w') as f:
        f.write("Class ID to Name Mapping:\n")
        f.write("========================\n")
        for idx, name in enumerate(CLASSES):
            f.write(f"{idx}: {name}\n")
    print(f"Saved class legend to {legend_path}")

def get_class_id():
    """Get class ID through number or text input"""
    print("\nCurrent classes:")
    for idx, name in enumerate(CLASSES):
        print(f"{idx}: {name}")
    
    while True:
        user_input = input("Enter class name or number: ").strip()
        
        # Try to interpret as number first
        if user_input.isdigit():
            class_id = int(user_input)
            if 0 <= class_id < len(CLASSES):
                return class_id
            print(f"Invalid number. Must be between 0-{len(CLASSES)-1}")
            continue
        
        # Otherwise treat as class name
        class_name = user_input.lower()
        if class_name in CLASSES:
            return CLASSES.index(class_name)
        
        # Option to add new class
        add_new = input(f"Class '{class_name}' not found. Add it? (y/n): ").lower()
        if add_new == 'y':
            CLASSES.append(class_name)
            save_legend()
            return len(CLASSES) - 1
        
        print("Please try again")

def mouse_callback(event, x, y, flags, param):
    global current_selection
    
    # Adjust coordinates for screen offset
    x -= SCREEN_OFFSET_X
    y -= SCREEN_OFFSET_Y
    
    # Only process clicks within the grid area
    if 0 <= x < GRID_WIDTH * TILE_SIZE and 0 <= y < GRID_HEIGHT * TILE_SIZE:
        if event == cv2.EVENT_LBUTTONDOWN:
            # Calculate which tile was clicked
            tile_x = x // TILE_SIZE
            tile_y = y // TILE_SIZE
            current_selection = (tile_x, tile_y)
            
            # Get class for this tile
            class_id = get_class_id()
            
            # Store annotation (YOLO format)
            x_center = (tile_x * TILE_SIZE + TILE_SIZE/2) / (GRID_WIDTH * TILE_SIZE)
            y_center = (tile_y * TILE_SIZE + TILE_SIZE/2) / (GRID_HEIGHT * TILE_SIZE)
            width = TILE_SIZE / (GRID_WIDTH * TILE_SIZE)
            height = TILE_SIZE / (GRID_HEIGHT * TILE_SIZE)
            
            # Check if this tile already has an annotation
            existing_idx = None
            for i, ann in enumerate(param['annotations']):
                ann_class, ann_x, ann_y, ann_w, ann_h = ann.split()
                ann_x = float(ann_x)
                ann_y = float(ann_y)
                
                # Check if this annotation is for the same tile
                if (int(ann_x * GRID_WIDTH) == tile_x and 
                    int(ann_y * GRID_HEIGHT) == tile_y):
                    existing_idx = i
                    break
            
            if existing_idx is not None:
                # Replace existing annotation
                param['annotations'][existing_idx] = (
                    f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
                )
            else:
                # Add new annotation
                param['annotations'].append(
                    f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
                )

def draw_grid(image):
    """Draw the grid lines on the image"""
    for x in range(0, GRID_WIDTH + 1):
        px = x * TILE_SIZE + SCREEN_OFFSET_X
        cv2.line(image, (px, SCREEN_OFFSET_Y), 
                (px, SCREEN_OFFSET_Y + GRID_HEIGHT * TILE_SIZE), 
                (0, 255, 255), 1)
    
    for y in range(0, GRID_HEIGHT + 1):
        py = y * TILE_SIZE + SCREEN_OFFSET_Y
        cv2.line(image, (SCREEN_OFFSET_X, py), 
                (SCREEN_OFFSET_X + GRID_WIDTH * TILE_SIZE, py), 
                (0, 255, 255), 1)

def annotate_image(img_path):
    global grid_visible
    
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"Error loading {img_path}")
        return
    
    annotations = []
    cv2.namedWindow("Dragon Warrior Annotation Tool")
    cv2.setMouseCallback("Dragon Warrior Annotation Tool", mouse_callback, 
                       param={'image': img, 'annotations': annotations})
    
    print(f"\nAnnotating: {img_path.name}")
    print("Instructions:")
    print("1. Click on any tile to annotate it")
    print("2. Enter class name or number when prompted")
    print("3. Keys: s=Save, q=Quit, g=Toggle Grid")
    
    while True:
        display_img = img.copy()
        
        # Draw grid if visible
        if grid_visible:
            draw_grid(display_img)
        
        # Draw existing annotations
        for ann in annotations:
            class_id, x, y, w, h = map(float, ann.split())
            class_name = CLASSES[int(class_id)]
            
            # Convert normalized coords to pixels
            x1 = int((x - w/2) * GRID_WIDTH * TILE_SIZE) + SCREEN_OFFSET_X
            y1 = int((y - h/2) * GRID_HEIGHT * TILE_SIZE) + SCREEN_OFFSET_Y
            x2 = int((x + w/2) * GRID_WIDTH * TILE_SIZE) + SCREEN_OFFSET_X
            y2 = int((y + h/2) * GRID_HEIGHT * TILE_SIZE) + SCREEN_OFFSET_Y
            
            cv2.rectangle(display_img, (x1,y1), (x2,y2), (0,255,0), 1)
            cv2.putText(display_img, f"{class_name[:3]}", 
                       (x1+2,y1+12), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.3, (0,255,0), 1)
        
        # Highlight current selection
        if current_selection:
            tile_x, tile_y = current_selection
            x1 = tile_x * TILE_SIZE + SCREEN_OFFSET_X
            y1 = tile_y * TILE_SIZE + SCREEN_OFFSET_Y
            x2 = x1 + TILE_SIZE
            y2 = y1 + TILE_SIZE
            cv2.rectangle(display_img, (x1,y1), (x2,y2), (0,0,255), 2)
        
        # Display instructions
        cv2.putText(display_img, "Click: Annotate | S: Save | Q: Quit | G: Toggle Grid", 
                   (10, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.5, (255, 255, 255), 1)
        
        cv2.imshow("Dragon Warrior Annotation Tool", display_img)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('s'):  # Save
            if annotations:
                # Save annotations
                label_file = ANNOTATED_LABELS / f"{img_path.stem}.txt"
                with open(label_file, 'w') as f:
                    f.write("\n".join(annotations))
                
                # Copy image
                dest_img = ANNOTATED_IMAGES / img_path.name
                shutil.copy(img_path, dest_img)
                print(f"Saved {len(annotations)} annotations to {label_file}")
            break
            
        elif key == ord('q'):  # Quit
            print("Discarding annotations...")
            break
            
        elif key == ord('g'):  # Toggle grid
            grid_visible = not grid_visible
            print(f"Grid visibility: {'ON' if grid_visible else 'OFF'}")

    cv2.destroyAllWindows()
    return annotations

def main():
    setup_dirs()
    save_legend()  # Create initial legend file
    
    print(f"Dragon Warrior Annotation Tool")
    print(f"Grid: {GRID_WIDTH}x{GRID_HEIGHT} tiles ({TILE_SIZE}x{TILE_SIZE}px each)")
    print(f"Screen offset: X={SCREEN_OFFSET_X}, Y={SCREEN_OFFSET_Y}")
    print(f"Initial classes: {CLASSES}")
    
    screenshots = list(SCREENSHOTS_DIR.glob("*.[pj][np]g"))  # Finds .png/.jpg
    if not screenshots:
        print(f"No images found in {SCREENSHOTS_DIR}")
        return
    
    for img_path in screenshots:
        annotate_image(img_path)
        print("\n" + "="*50 + "\n")
    
    print(f"\nFinal class legend:")
    for i, name in enumerate(CLASSES):
        print(f"{i}: {name}")
    print(f"\nAll annotations saved to {ANNOTATED_DIR}")

if __name__ == "__main__":
    main()