import cv2
from ultralytics import YOLO
import requests
import time

# --- Configuration ---
# OPTION 1: Use your phone's IP Webcam (Update the IP and add /video)
CAMERA_URL = "http://192.168.29.158:8080/video" 

# OPTION 2: Use your laptop's built-in webcam (uncomment the line below)
# CAMERA_URL = 0

BACKEND_URL = "http://localhost:5001/api/signal-timings"
UPDATE_INTERVAL = 5  # How often to send data to the backend (in seconds)

# --- Performance Optimization ---
# FIX: Process every 3rd frame to make the video smoother.
# Increase this number (e.g., to 5) if the video is still slow.
PROCESS_EVERY_N_FRAMES = 3

# Load a pre-trained YOLOv8 model
model = YOLO('yolov8n.pt')

# --- Define Regions of Interest (ROIs) ---
# IMPORTANT: These are (x1, y1, x2, y2). Adjust these to fit your camera view.
ROIS = {
    "north": (280, 0, 360, 230),
    "south": (280, 250, 360, 480),
    "east": (370, 200, 640, 280),
    "west": (0, 200, 270, 280)
}

def count_cars_in_roi(detections, roi_coords):
    """Counts how many detected car centers fall within a given ROI."""
    x1_roi, y1_roi, x2_roi, y2_roi = roi_coords
    count = 0
    centers = []
    for det in detections:
        box = det.xyxy[0].cpu().numpy().astype(int)
        center_x = (box[0] + box[2]) // 2
        center_y = (box[1] + box[3]) // 2
        centers.append((center_x, center_y))
        if x1_roi < center_x < x2_roi and y1_roi < center_y < y2_roi:
            count += 1
    return count, centers

# --- Main Loop ---
def main():
    cap = cv2.VideoCapture(CAMERA_URL)
    if not cap.isOpened():
        print(f"❌ Could not open camera stream at {CAMERA_URL}")
        return

    print("✅ Camera stream opened. Starting traffic analysis...")
    last_update_time = time.time()
    frame_counter = 0
    
    # Initialize variables before the loop to ensure they always exist
    individual_counts = {name: 0 for name in ROIS.keys()}
    all_centers = []
    processed_frame = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Failed to grab frame. Retrying...")
            time.sleep(2)
            continue

        frame = cv2.resize(frame, (640, 480))
        frame_counter += 1
        
        # Only perform heavy AI processing on specified frames
        if frame_counter % PROCESS_EVERY_N_FRAMES == 0:
            results = model(frame, classes=[2], verbose=False, conf=0.45) # Lowered confidence slightly
            car_detections = results[0].boxes
            
            # Create a clean frame for drawing
            processed_frame = results[0].plot()

            # FIX: Update counts and centers in real-time whenever we process a frame
            temp_centers = []
            for name, roi in ROIS.items():
                count, centers = count_cars_in_roi(car_detections, roi)
                individual_counts[name] = count
                temp_centers.extend(centers)
            all_centers = temp_centers
        else:
            # For frames we skip, just use the original frame
            processed_frame = frame.copy()

        # Only send data to the backend every UPDATE_INTERVAL seconds
        current_time = time.time()
        if current_time - last_update_time >= UPDATE_INTERVAL:
            last_update_time = current_time
            ns_count = individual_counts.get("north", 0) + individual_counts.get("south", 0)
            ew_count = individual_counts.get("east", 0) + individual_counts.get("west", 0)
            vehicle_counts = {"ns_vehicles": ns_count, "ew_vehicles": ew_count}
            
            print(f"-> Sending to backend: NS={ns_count}, EW={ew_count}")
            try:
                requests.post(BACKEND_URL, json=vehicle_counts, timeout=2)
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Could not send data to backend: {e}")
        
        # --- Visual Debugging (drawn on every frame for a smooth experience) ---
        for name, (x1, y1, x2, y2) in ROIS.items():
            cv2.rectangle(processed_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            count_text = f"{name}: {individual_counts.get(name, 0)}"
            cv2.putText(processed_frame, count_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        for center in all_centers:
            cv2.circle(processed_frame, center, 3, (0, 0, 255), -1)

        cv2.imshow("Live Traffic Feed", processed_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("🛑 System shutdown.")

if __name__ == "__main__":
    main()

