import cv2
import numpy as np
import requests
import time

# Import  ML timing calculation (all files inside ML folder)
from .train_model import calculate_optimized_timing

CAMERA_URL = "http://100.70.1.10:8080/video"  
BACKEND_URL = "http://localhost:5001/api/update-counts" 
UPDATE_INTERVAL = 3  

MIN_CAR_AREA = 500  

FRAME_WIDTH = 640
FRAME_HEIGHT = 360

def widen_roi(x1, y1, x2, y2, width_increase=50, height_increase=20):
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2
    half_width = (x2 - x1) // 2 + width_increase // 2
    half_height = (y2 - y1) // 2 + height_increase // 2

    new_x1 = max(center_x - half_width, 0)
    new_x2 = min(center_x + half_width, FRAME_WIDTH)
    new_y1 = max(center_y - half_height, 0)
    new_y2 = min(center_y + half_height, FRAME_HEIGHT)
    return (new_x1, new_y1, new_x2, new_y2)

ROIS = {
    "north": widen_roi(int(855 * FRAME_WIDTH / 1920), 0, int(1065 * FRAME_WIDTH / 1920), int(461 * FRAME_HEIGHT / 1080)),
    "south": widen_roi(int(855 * FRAME_WIDTH / 1920), int(618 * FRAME_HEIGHT / 1080), int(1065 * FRAME_WIDTH / 1920), FRAME_HEIGHT),
    "east": widen_roi(int(1065 * FRAME_WIDTH / 1920), int(461 * FRAME_HEIGHT / 1080), FRAME_WIDTH, int(618 * FRAME_HEIGHT / 1080)),
    "west": widen_roi(0, int(461 * FRAME_HEIGHT / 1080), int(855 * FRAME_WIDTH / 1920), int(618 * FRAME_HEIGHT / 1080))
}

def draw_text_with_background(frame, text, position, font_scale=0.6, color=(255, 255, 255)):
    (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)
    cv2.rectangle(frame, (position[0], position[1] - h - 10), (position[0] + w + 10, position[1]), (0, 0, 0), -1)
    cv2.putText(frame, text, (position[0] + 5, position[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)

def main():
    cap = cv2.VideoCapture(CAMERA_URL)
    if not cap.isOpened():
        print(f"Could not open camera stream at {CAMERA_URL}")
        return

    backSub = cv2.createBackgroundSubtractorMOG2(history=1000, varThreshold=25, detectShadows=False)

    print("Camera stream opened. System is initializing...")
    print("IMPORTANT: Keep the road EMPTY for the first 5 seconds for background calibration.")
    time.sleep(5)
    print("Calibration complete! You can now place cars on the road.")

    last_backend_update = time.time()
    latest_counts = {name: 0 for name in ROIS.keys()}

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame. Retrying...")
            time.sleep(1)
            continue

        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        fgMask = backSub.apply(frame)
        fgMask = cv2.erode(fgMask, kernel, iterations=1)
        fgMask = cv2.dilate(fgMask, kernel, iterations=2)

        contours, _ = cv2.findContours(fgMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_cars = [cnt for cnt in contours if cv2.contourArea(cnt) > MIN_CAR_AREA]

        current_counts = {name: 0 for name in ROIS.keys()}
        for name, (x1, y1, x2, y2) in ROIS.items():
            for cnt in detected_cars:
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    if x1 < cX < x2 and y1 < cY < y2:
                        current_counts[name] += 1

        latest_counts = current_counts

        ns_count = latest_counts.get("north", 0) + latest_counts.get("south", 0)
        ew_count = latest_counts.get("east", 0) + latest_counts.get("west", 0)

        optimized_times = calculate_optimized_timing(ns_count, ew_count)

        current_time = time.time()
        if current_time - last_backend_update >= UPDATE_INTERVAL:
            last_backend_update = current_time
            payload = {
                "ns_vehicles": ns_count,
                "ew_vehicles": ew_count,
                "ns_time": optimized_times["ns_time"],
                "ew_time": optimized_times["ew_time"]
            }
            print(f"--> SENDING TO BACKEND: {payload}")
            try:
                requests.post(BACKEND_URL, json=payload, timeout=2)
            except requests.exceptions.RequestException:
                print("Could not send data to backend.")

        cv2.drawContours(frame, detected_cars, -1, (255, 0, 0), 2)
        for name, (x1, y1, x2, y2) in ROIS.items():
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            draw_text_with_background(frame, f"{name.upper()}: {latest_counts.get(name, 0)}", (x1, y1))

        cv2.imshow("Live Traffic Feed", frame)
        cv2.imshow("Detection Mask", fgMask)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("System shutdown.")

if __name__ == "__main__":
    main()
