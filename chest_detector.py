import cv2
import yaml
from pathlib import Path
from ultralytics import YOLO

# Configuration
ANNOTATED_DIR = Path("annotated")
MODELS_DIR = Path("runs/detect")  # Where YOLO saves trained models
LEGEND_FILE = ANNOTATED_DIR / "labels" / "_legend.txt"

def get_latest_model():
    """Find the most recently trained model in runs/detect"""
    model_files = sorted(MODELS_DIR.glob("*/weights/best.pt"), 
                        key=lambda x: x.stat().st_mtime, 
                        reverse=True)
    return model_files[0] if model_files else None

def load_classes():
    """Load class names from _legend.txt"""
    if not LEGEND_FILE.exists():
        raise FileNotFoundError(f"{LEGEND_FILE} not found")
    
    classes = {}
    with open(LEGEND_FILE, 'r') as f:
        for line in f:
            if ":" in line and line.split(":")[0].strip().isdigit():
                class_id = int(line.split(":")[0].strip())
                class_name = line.split(":")[1].strip()
                classes[class_id] = class_name
    return classes

def create_dataset_yaml():
    """Create dataset.yaml dynamically from _legend.txt"""
    classes = load_classes()
    dataset_yaml = ANNOTATED_DIR / "dataset.yaml"
    
    yaml_content = {
        "path": str(ANNOTATED_DIR),
        "train": "images",
        "val": "images",
        "names": {k: v for k, v in sorted(classes.items())}
    }
    
    with open(dataset_yaml, 'w') as f:
        yaml.dump(yaml_content, f, sort_keys=False)
    
    print(f"Created dataset.yaml with classes: {classes}")
    return dataset_yaml

def train_model():
    dataset_yaml = create_dataset_yaml()
    
    model = YOLO("yolov8m.pt")  
    results = model.train(
        data=dataset_yaml,
        epochs=100,  # Increased epochs
        imgsz=256,
        batch=8,
        name="treasure_chest_detector",
        augment=True,  # Enable built-in augmentation
        hsv_h=0.015,  # Hue augmentation
        hsv_s=0.7,    # Saturation augmentation
        hsv_v=0.4,    # Value augmentation
        degrees=15,   # Rotation
        translate=0.1,  # Translation
        scale=0.5,     # Scale
        shear=0.0,
        flipud=0.0,
        fliplr=0.5,    # 50% chance of horizontal flip
        mosaic=1.0     # Mosaic augmentation
    )
    return model

def detect_chests(model, img_path, confidence_threshold=0.25):  # Add parameter here
    """Detect chests in new image with adjustable confidence threshold"""
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"Error loading image: {img_path}")
        return None, []
    
    results = model.predict(img, conf=confidence_threshold)  # Use the parameter here
    
    chests = []
    for result in results:
        for box in result.boxes:
            if int(box.cls) == 0:  # Class 0 = treasure_chest
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                chests.append({
                    "position": ((x1 + x2)//2, (y1 + y2)//2),
                    "confidence": float(box.conf)
                })
    return img, chests

def main():
    # Try to load the most recent model first
    latest_model = get_latest_model()
    if latest_model:
        model = YOLO(latest_model)
        print(f"Loaded most recent model: {latest_model}")
    else:
        print("No trained model found. Training new model...")
        model = train_model()
        latest_model = get_latest_model()
        print(f"Training complete. Model saved to: {latest_model}")
    
    # Get all test images
    test_images = list(ANNOTATED_DIR.glob("images/*.png"))
    if not test_images:
        print("No test images found in annotated/images/")
        return
    
    # Initialize confidence threshold and image index
    CONFIDENCE_THRESHOLD = 0.25  # Start with 25% confidence threshold
    current_image_idx = 0
    
    while True:
        test_img = test_images[current_image_idx]
        print(f"\nProcessing: {test_img.name} (Threshold: {CONFIDENCE_THRESHOLD:.2f})")
        
        img, chests = detect_chests(model, test_img, confidence_threshold=CONFIDENCE_THRESHOLD)
        if img is None:
            current_image_idx = (current_image_idx + 1) % len(test_images)
            continue
        
        # Draw detections with confidence scores
        for chest in chests:
            x, y = chest["position"]
            cv2.circle(img, (x, y), 10, (0, 255, 0), -1)
            cv2.putText(img, f"{chest['confidence']:.2f}", 
                       (x, y - 15), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.5, (0, 255, 0), 2)
        
        # Display current threshold
        cv2.putText(img, f"Threshold: {CONFIDENCE_THRESHOLD:.2f} (+/- to adjust)", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.7, (0, 0, 255), 2)
        
        # Display instructions
        cv2.putText(img, "SPACE: Next Image | Q: Quit", 
                   (10, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.5, (255, 255, 255), 1)
        
        print(f"Detected {len(chests)} treasure chests:")
        for i, chest in enumerate(chests, 1):
            print(f"Chest {i}: Position={chest['position']}, Confidence={chest['confidence']:.2f}")
        
        cv2.imshow("Treasure Chest Detector", img)
        
        # Handle key presses
        key = cv2.waitKey(0) & 0xFF
        if key == ord(' '):  # Space bar - next image
            current_image_idx = (current_image_idx + 1) % len(test_images)
        elif key == ord('q'):  # Q - quit
            break
        elif key == ord('+') or key == ord('='):  # Increase threshold
            CONFIDENCE_THRESHOLD = min(0.9, CONFIDENCE_THRESHOLD + 0.05)
        elif key == ord('-') or key == ord('_'):  # Decrease threshold
            CONFIDENCE_THRESHOLD = max(0.1, CONFIDENCE_THRESHOLD - 0.05)
    
    cv2.destroyAllWindows()
    print("\nDetection complete. Final confidence threshold:", CONFIDENCE_THRESHOLD)

if __name__ == "__main__":
    main()
