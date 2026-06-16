import cv2
import requests
import base64
import time
import datetime
import os
import threading
import copy
from ultralytics import YOLO

# Configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:5000/api/iot/alert")
CAMERA_ID = 0  # 0 for default webcam
DETECTION_INTERVAL = 15  # Seconds between alerts
CONFIDENCE_THRESHOLD = 0.5

# We focus on specific classes if we use the default YOLOv8 COCO model
# Focus ONLY on wild animals. We ignore pets (dogs) and cattle.
# NOTE: The default COCO model lacks a 'Leopard' class, so leopards are typically detected as 'cat' (15).
COCO_FALLBACK_CLASSES = {
    15: "Leopard (Detected as Feline)",
    20: "Elephant",
    21: "Bear"
}

# Global state for multithreading
shared_frame = None
shared_detections = []
ai_fps = 0
ai_thread_running = True
camera_fps = 0

def ai_worker_thread(custom_model, standard_model):
    """Background thread to run Dual YOLO inference."""
    global shared_frame, shared_detections, ai_fps, ai_thread_running
    
    prev_time = 0
    last_alert_time = 0
    
    while ai_thread_running:
        if shared_frame is None:
            time.sleep(0.01)
            continue
            
        frame_to_process = copy.deepcopy(shared_frame)
        new_time = time.time()
        
        # Performance monitoring
        fps_value = 1 / (new_time - prev_time) if prev_time > 0 else 0
        prev_time = new_time
        ai_fps = int(fps_value)
        
        new_detections = []
        current_frame_animal = None
        human_boxes = []

        # --- PHASE 1: HUMAN DETECTION (Standard Model acts as a filter) ---
        results_std = standard_model(frame_to_process, verbose=False, conf=0.4)
        if results_std is None:
            results_std = []
        for result in results_std:
            if result.boxes is None:
                continue
            for box in result.boxes:
                cls_id = int(box.cls[0])
                if cls_id == 0: # Person
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    human_boxes.append((x1, y1, x2, y2))

        # --- PHASE 2: EXPERT DETECTION (Custom Model) ---
        if custom_model:
            # Lower confidence threshold to 0.45 to be more sensitive for testing custom models
            results_custom = custom_model(frame_to_process, verbose=False, conf=0.45)
            if results_custom is None:
                results_custom = []
            for result in results_custom:
                if result.boxes is None:
                    continue
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    class_name = custom_model.names[cls_id]
                    confidence = float(box.conf[0])
                    cx1, cy1, cx2, cy2 = map(int, box.xyxy[0])
                    
                    print(f"DEBUG: Custom model spotted '{class_name}' with confidence {confidence:.2f}")
                    
                    # ANTI-HUMAN CHECK: Does this leopard overlap with a detected person?
                    is_actually_human = False
                    for hx1, hy1, hx2, hy2 in human_boxes:
                        # Check for box intersection/overlap
                        if not (cx2 < hx1 or cx1 > hx2 or cy2 < hy1 or cy1 > hy2):
                            is_actually_human = True
                            break
                    
                    if not is_actually_human:
                        current_frame_animal = class_name
                        new_detections.append({"class_name": f"EXPERT: {class_name} ({confidence:.2f})", "box": (cx1, cy1, cx2, cy2)})
                    else:
                        print(f"DEBUG: Ignored '{class_name}' detection because it overlaps with a detected Human (for testing, try standing away from the image!)")

        # --- PHASE 3: OTHER WILD ANIMALS ---
        for result in results_std:
            if result.boxes is None:
                continue
            for box in result.boxes:
                cls_id = int(box.cls[0])
                confidence = float(box.conf[0])
                WILD_ANIMALS = [15, 20, 21, 22, 23] # Cat/Feline (Leopard fallback), Elephant, Bear, Zebra, Giraffe
                
                if cls_id in WILD_ANIMALS:
                    # Critical Fix: Prevent low confidence cat detections triggering Leopard warnings
                    if cls_id == 15 and confidence < 0.65:
                        continue
                        
                    class_name = COCO_FALLBACK_CLASSES.get(cls_id, standard_model.names[cls_id])
                    if not current_frame_animal:
                        current_frame_animal = class_name
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    new_detections.append({"class_name": class_name, "box": (x1, y1, x2, y2)})
                    
        # Update safely for main thread
        shared_detections = new_detections
        
        # Network Alert Logic
        if current_frame_animal and (new_time - last_alert_time > DETECTION_INTERVAL):
            detected_animal = current_frame_animal
            print(f"Alert Triggered: {detected_animal} detected! Sending to dashboard...")
            
            _, buffer = cv2.imencode('.jpg', frame_to_process)
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            
            payload = {
                "location": "Main Entrance (Camera 1)",
                "description": f"DANGER: {detected_animal.capitalize()} detected!",
                "species": detected_animal,
                "distance": 25.0,
                "image_data": jpg_as_text
            }
            
            try:
                response = requests.post(BACKEND_URL, json=payload, timeout=5)
                if response.status_code == 201:
                    last_alert_time = new_time
            except Exception as e:
                print(f"Error sending alert: {e}")

def capture_and_send():
    global shared_frame, shared_detections, ai_fps, ai_thread_running, camera_fps
    
    print("Initializing Dual-AI System...")
    
    # Load Standard Model (Common Animals)
    standard_model = YOLO("yolov8s.pt")
    
    # Load Custom Model (Leopard Expert)
    custom_model = None
    possible_paths = [
        os.path.join(os.path.dirname(__file__), 'custom_animal_model.pt'),
        os.path.join(os.path.dirname(__file__), '..', 'edge_device', 'custom_animal_model.pt'),
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
        print(f"--> Expert Model Found and Loaded: {custom_model_path}")
        custom_model = YOLO(custom_model_path)
        print(f"--> Expert Model Classes: {custom_model.names}")
    else:
        print("--> Expert Model NOT FOUND. Using standard mode only.")
    
    # Scan camera indices 0-5 to find an active physical webcam robustly
    cap = None
    webcam_found = False
    
    # We will try default backend, then DSHOW, then MSMF for each index
    for idx in [0, 1, 2, 3, 4, 5]:
        print(f"Checking webcam index {idx}...")
        for backend_name, backend_flag in [("Default", None), ("DSHOW", cv2.CAP_DSHOW), ("MSMF", cv2.CAP_MSMF)]:
            try:
                if backend_flag is None:
                    test_cap = cv2.VideoCapture(idx)
                else:
                    test_cap = cv2.VideoCapture(idx, backend_flag)
                    
                if test_cap.isOpened():
                    # Read a frame to verify it works (sometimes isOpened() is True but read() fails)
                    ret, test_frame = test_cap.read()
                    if ret and test_frame is not None:
                        cap = test_cap
                        webcam_found = True
                        print(f"--> SUCCESS: Connected to webcam index {idx} using {backend_name} backend!")
                        break
                    else:
                        test_cap.release()
            except Exception:
                pass
        if webcam_found:
            break
            
    if not cap or not cap.isOpened():
        print("\n==================================================================")
        print("ERROR: Could not open any physical webcam (checked indices 0-5).")
        print("Please check the following:")
        print("1. Is your webcam physically plugged in and turned on?")
        print("2. Is another program using the camera (e.g. Zoom, Teams, Chrome, OBS)?")
        print("3. Check Windows Privacy Settings: 'Allow desktop apps to access your camera' must be enabled.")
        print("==================================================================\n")
        return
        
    # Start the background AI Thread with BOTH models
    ai_thread = threading.Thread(target=ai_worker_thread, args=(custom_model, standard_model), daemon=True)
    ai_thread.start()
    
    prev_frame_time = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Provide the newest frame to the AI thread
        shared_frame = frame

        # Calculate exact Camera FPS
        new_frame_time = time.time()
        fps_value = 1 / (new_frame_time - prev_frame_time) if prev_frame_time > 0 else 0
        prev_frame_time = new_frame_time
        camera_fps = int(fps_value)

        # Draw the latest detections from AI overlay
        for det in shared_detections:
            x1, y1, x2, y2 = det["box"]
            class_name = det["class_name"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, f"{class_name.upper()}", (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        # Display dual FPS text
        cv2.putText(frame, f"Cam FPS: {camera_fps} | AI FPS: {ai_fps}", (15, 35), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        cv2.imshow("WildGuard Animal Detection", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    ai_thread_running = False
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    capture_and_send()
