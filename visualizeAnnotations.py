import cv2
import numpy as np
from pathlib import Path

# Configuration
ANNOTATED_DIR = Path("annotated")
LEGEND_FILE = ANNOTATED_DIR / "labels" / "_legend.txt"

def load_classes():
    """Load class names from _legend.txt"""
    if not LEGEND_FILE.exists():
        print(f"⚠️ Warning: {LEGEND_FILE} not found. Using default classes.")
        return ["treasure_chest"]  # Fallback
    
    classes = []
    with open(LEGEND_FILE, 'r') as f:
        for line in f:
            if ":" in line and line.split(":")[0].strip().isdigit():
                class_id, class_name = line.split(":", 1)
                classes.append(class_name.strip())
    return classes

CLASSES = load_classes()
COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))  # Random colors per class

def visualize_annotations(image_path):
    """Draw bounding boxes on image using YOLO annotation file"""
    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"Error: Could not load image {image_path}")
        return
    
    # Get corresponding label file
    label_path = ANNOTATED_DIR / "labels" / f"{image_path.stem}.txt"
    if not label_path.exists():
        print(f"No annotation file found for {image_path.name}")
        return
    
    # Read annotations
    with open(label_path) as f:
        annotations = [line.strip() for line in f if line.strip()]
    
    # Draw each annotation
    for ann in annotations:
        try:
            class_id, x_center, y_center, width, height = map(float, ann.split())
            class_id = int(class_id)
            
            # Skip if class_id is invalid
            if class_id >= len(CLASSES):
                print(f"⚠️ Warning: Class ID {class_id} is out of range (max: {len(CLASSES)-1})")
                continue
            
            # Convert YOLO format to pixel coordinates
            img_height, img_width = image.shape[:2]
            x1 = int((x_center - width/2) * img_width)
            y1 = int((y_center - height/2) * img_height)
            x2 = int((x_center + width/2) * img_width)
            y2 = int((y_center + height/2) * img_height)
            
            # Draw rectangle and label
            color = COLORS[class_id]
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            cv2.putText(image, f"{CLASSES[class_id]} ({class_id})", 
                       (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.5, color, 2)
        except Exception as e:
            print(f"⚠️ Error processing annotation line: '{ann}' ({e})")
    
    # Display result
    cv2.imshow("Annotation Visualizer", image)
    print(f"Displaying {len(annotations)} annotations (Press any key to close)")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def main():
    print(f"Loaded classes: {CLASSES}")
    
    # Get all annotated images
    image_files = list((ANNOTATED_DIR / "images").glob("*.[pj][np]g"))
    
    if not image_files:
        print("No images found in annotated/images/")
        return
    
    # Visualize each image
    for img_path in image_files:
        print(f"\nVisualizing: {img_path.name}")
        visualize_annotations(img_path)
        
        # Prompt to continue
        if input("Continue? (y/n): ").lower() != 'y':
            break

if __name__ == "__main__":
    main()