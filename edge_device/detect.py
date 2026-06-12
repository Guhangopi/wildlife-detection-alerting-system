import cv2
import time
import requests
import base64
from ultralytics import YOLO

# Configuration
import os
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:5000/api/iot/alert")
CAMERA_INDEX = 0  # Default system webcam
POLL_INTERVAL = 2  # Process 1 frame every 2 seconds to save processing power

import os

# We focus on specific classes if we use the default YOLOv8 COCO model.
# NOTE: The default COCO model doesn't know exact species like Leopard, Wild Boar, etc.
# For exact names, users must train a custom model and save as 'custom_animal_model.pt'.
# Focus ONLY on wild animals. We ignore pets (dogs) and cattle.
# NOTE: The default COCO model lacks a 'Leopard' class, so leopards are typically detected as 'cat' (15).
COCO_FALLBACK_CLASSES = {
    15: "Leopard (Detected as Feline)",
    20: "Elephant",
    21: "Bear"
}

def capture_and_detect():
    print("Loading AI model...")
    # Check if a custom trained model exists for exact species detection
    possible_paths = [
        os.path.join(os.path.dirname(__file__), 'custom_animal_model.pt'),
        os.path.join(os.path.dirname(__file__), '..', 'backend', 'custom_animal_model.pt'),
        os.path.join(os.path.dirname(__file__), '..', 'custom_animal_model.pt'),
        os.path.join(os.getcwd(), 'custom_animal_model.pt'),
        os.path.join(os.getcwd(), 'backend', 'custom_animal_model.pt'),
        os.path.join(os.getcwd(), 'edge_device', 'custom_animal_model.pt')
    ]
    
    custom_model_path = None
    for p in possible_paths:
        if os.path.exists(p):
            custom_model_path = os.path.abspath(p)
            break
            
    if custom_model_path:
        print(f"--> Found custom model! Loading exactly trained species from: {custom_model_path}")
        model = YOLO(custom_model_path)
        print(f"--> Model Classes: {model.names}")
        using_custom_model = True
    else:
        print("--> Using default YOLOv8 COCO model (yolov8n.pt).")
        print("    NOTE: For exact species like 'Leopard' or 'Wild Boar', please train a custom YOLO model.")
        print("    See 'backend/train_custom_yolo.py' for instructions.")
        model = YOLO('yolov8s.pt') # Upgraded to Small model for better accuracy
        using_custom_model = False
    
    print(f"Opening webcam at index {CAMERA_INDEX}...")
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    last_inference_time = 0
    last_alert_time = 0
    COOLDOWN = 10 # Wait 10 seconds before sending another alert to avoid spam

    print("--- Starting wildlife detection stream ---")
    print("Press 'q' in the video window to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        # Display the live feed
        cv2.imshow("Wildlife Edge Detector", frame)

        # Process every few seconds
        current_time = time.time()
        if current_time - last_inference_time > POLL_INTERVAL:
            last_inference_time = current_time
            # Run inference
            results = model.predict(source=frame, save=False, conf=0.4, verbose=False)
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    class_id = int(box.cls[0].item())
                    confidence = round(box.conf[0].item(), 2)

                    species_detected = None
                    if using_custom_model:
                        # Exact labels from the custom trained model! No mapping needed.
                        species_detected = model.names[class_id]
                    else:
                        # Fallback COCO mapping
                        if class_id in COCO_FALLBACK_CLASSES:
                            class_name = COCO_FALLBACK_CLASSES[class_id]
                            
                            # Critical Fix: Prevent humans from triggering "Leopard" via poor Cat misclassifications
                            if class_id == 15 and confidence < 0.65:
                                continue # Too low confidence to risk a false leopard alarm
                                
                            species_detected = class_name

                    if species_detected:
                        
                        # Calculate distance mock based on bounding box size
                        # Tighter box = further away. Larger box = closer.
                        # This is a basic mock for the geofencing requirement
                        box_height = box.xywh[0][3].item() 
                        frame_height = frame.shape[0]
                        ratio = box_height / frame_height
                        
                        # Mock mapping: 
                        # ratio > 0.6 => ~10 meters (Emergency)
                        # ratio 0.3 - 0.6 => ~50 meters (Warning)
                        # ratio < 0.3 => ~150 meters (Info)
                        if ratio > 0.6:
                            distance = 15.0
                        elif ratio > 0.3:
                            distance = 60.0
                        else:
                            distance = 150.0

                        print(f"[{time.strftime('%X')}] DETECTED: {species_detected} (Conf: {confidence}) approx {distance}m away.")

                        # Draw bounding boxes on the image before sending so dashboard shows visual proof!
                        annotated_frame = result.plot()
                        
                        # Encode image to base64
                        _, buffer = cv2.imencode('.jpg', annotated_frame)
                        img_str = base64.b64encode(buffer).decode('utf-8')

                        payload = {
                            "location": "North Campus Boundary (Cam 1)",
                            "description": f"Automated Detection: {species_detected}",
                            "species": species_detected,
                            "distance": distance,
                            "image_data": img_str
                        }

                        if current_time - last_alert_time > COOLDOWN:
                            print(f">>> Sending payload to Cloud Server...")
                            try:
                                response = requests.post(BACKEND_URL, json=payload, timeout=5)
                                if response.status_code == 201:
                                    print(">>> Alert successfully transmitted!")
                                    last_alert_time = time.time()
                                else:
                                    print(f">>> Backend returned error: {response.text}")
                            except Exception as e:
                                print(f">>> Communication error: {e}")
                            
                            break # Only send one alert per frame

        # Break loop on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    capture_and_detect()
