import cv2
from ultralytics import YOLO
import requests
import time
import numpy as np
import sys

# --- ML Import ---
try:
    sys.path.append("ML")
    from train_model import calculate_optimized_timing
except ImportError:
    print("⚠️ Could not import calculate_optimized_timing. Using fallback timings.")
    def calculate_optimized_timing(ns_count, ew_count):
        return {"ns_time": 10, "ew_time": 10}

# --- Configuration ---
CAMERA_URL = "http://10.206.97.185:8080"  # Update to your IP webcam URL
BACKEND_URL = "http://localhost:5001/api/update-counts"

# Load YOLOv8 model
model = YOLO("yolov8n.pt")

# Define Regions of Interest (ROIs) for each lane
ROIS = {
    "north": (300, 100, 340, 200),
    "south": (300, 280, 340, 380),
    "east": (400, 220, 500, 260),
    "west": (140, 220, 240, 260)
}

def count_cars_in_roi(detections, roi_coords):
    x_min, y_min, x_max, y_max = roi_coords
    count = 0
    for det in detections:
        if len(det.xyxy) == 0:
            continue
        box = det.xyxy[0].cpu().numpy().astype(int)
        x1, y1, x2, y2 = box[0], box[1], box[2], box[3]
        center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
        if x_min <= center_x <= x_max and y_min <= center_y <= y_max:
            count += 1
    return count

# --- Main Loop ---
def main():
    cap = cv2.VideoCapture(CAMERA_URL)
    if not cap.isOpened():
        print(f"❌ Could not open camera stream at {CAMERA_URL}")
        return

    print("✅ Camera stream opened. Starting traffic analysis...")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Failed to grab frame. Retrying in 2s...")
            cap.release()
            time.sleep(2)
            cap = cv2.VideoCapture(CAMERA_URL)
            continue

        try:
            frame = cv2.resize(frame, (640, 480))
        except cv2.error as e:
            print(f"⚠️ Error resizing frame: {e}")
            continue

        results = model(frame, classes=[2], verbose=False, conf=0.5)
        car_detections = results[0].boxes

        ns_count = count_cars_in_roi(car_detections, ROIS["north"]) + count_cars_in_roi(car_detections, ROIS["south"])
        ew_count = count_cars_in_roi(car_detections, ROIS["east"]) + count_cars_in_roi(car_detections, ROIS["west"])
        raw_counts = {"ns_vehicles": ns_count, "ew_vehicles": ew_count}

        try:
            optimized_times = calculate_optimized_timing(ns_count, ew_count)
        except Exception as e:
            print(f"⚠️ ML model error: {e}. Using fallback timings.")
            optimized_times = {"ns_time": 10, "ew_time": 10}

        # Draw detections and ROIs
        frame = results[0].plot()
        for name, (x1, y1, x2, y2) in ROIS.items():
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, name, (x1 + 5, y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.putText(frame, f"NS: {ns_count} | OPT: {optimized_times['ns_time']}s", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"EW: {ew_count} | OPT: {optimized_times['ew_time']}s", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Send to backend
        try:
            requests.post(BACKEND_URL, json=optimized_times, timeout=2)
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Could not send to backend: {e}")

        cv2.imshow("Live Traffic Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(5)

    cap.release()
    cv2.destroyAllWindows()
    print("🛑 System shutdown.")

if __name__ == "__main__":
    main()
