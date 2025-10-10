import cv2
import numpy as np
import requests
import time

# ===================================================================================
# --- CONFIGURATION ---
# ===================================================================================
# --- YOUR SETUP ---
CAMERA_URL = "http://192.168.29.92:8080/video" # Or use 0 for webcam
BACKEND_URL = "http://localhost:5001/api/signal-timings"
UPDATE_INTERVAL = 3 # Update backend more frequently
MIN_CAR_AREA = 500 # The smallest size (in pixels) to be considered a car.

# --- YOUR REGIONS OF INTEREST (ROIs) ---
# These are (x1, y1, x2, y2). Adjust these to perfectly match your camera's view.
ROIS = {
    "north": (270, 0, 370, 220),
    "south": (270, 260, 370, 480),
    "east": (380, 210, 640, 270),
    "west": (0, 210, 260, 270)
}
# ===================================================================================

def draw_text_with_background(frame, text, position, font_scale=0.6, color=(255, 255, 255)):
    """Draws text with a black background for better readability."""
    (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)
    cv2.rectangle(frame, (position[0], position[1] - h - 10), (position[0] + w + 10, position[1]), (0,0,0), -1)
    cv2.putText(frame, text, (position[0] + 5, position[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)

def main():
    cap = cv2.VideoCapture(CAMERA_URL)
    if not cap.isOpened():
        print(f"❌ Could not open camera stream at {CAMERA_URL}")
        return

    # Create the background subtractor object. This is the core of our new detection method.
    # It learns the background and identifies new objects.
    backSub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)

    print("✅ Camera stream opened. System is initializing...")
    print("🔴 IMPORTANT: Keep the road EMPTY for the first 5 seconds for background calibration.")
    time.sleep(5) # Give it time to learn the background
    print("🟢 Calibration complete! You can now place cars on the road.")

    last_backend_update = time.time()
    latest_counts = {name: 0 for name in ROIS.keys()}

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Failed to grab frame. Retrying...")
            time.sleep(1)
            continue

        frame = cv2.resize(frame, (640, 480))
        
        # 1. Apply the background subtractor to get a "mask" of the foreground (cars)
        fgMask = backSub.apply(frame)
        
        # 2. Clean up the mask to remove noise
        # Erode gets rid of small white speckles, Dilate makes the main objects bigger.
        kernel = np.ones((5,5),np.uint8)
        fgMask = cv2.erode(fgMask, kernel, iterations=1)
        fgMask = cv2.dilate(fgMask, kernel, iterations=2)

        # 3. Find the contours (outlines) of the detected objects
        contours, _ = cv2.findContours(fgMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detected_cars = []
        for cnt in contours:
            # If a contour is too small, ignore it (it's likely noise)
            if cv2.contourArea(cnt) > MIN_CAR_AREA:
                detected_cars.append(cnt)

        # 4. Count cars by checking if a contour's center is in an ROI
        current_counts = {name: 0 for name in ROIS.keys()}
        for name, (x1, y1, x2, y2) in ROIS.items():
            for car_contour in detected_cars:
                # Calculate the center of the contour
                M = cv2.moments(car_contour)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    # Check if the center is inside the current ROI
                    if x1 < cX < x2 and y1 < cY < y2:
                        current_counts[name] += 1
        
        latest_counts = current_counts
        
        # 5. Send data to the backend periodically
        current_time = time.time()
        if current_time - last_backend_update >= UPDATE_INTERVAL:
            last_backend_update = current_time
            ns_count = latest_counts.get("north", 0) + latest_counts.get("south", 0)
            ew_count = latest_counts.get("east", 0) + latest_counts.get("west", 0)
            vehicle_counts = {"ns_vehicles": ns_count, "ew_vehicles": ew_count}
            print(f"--> SENDING TO BACKEND: {vehicle_counts}")
            try:
                requests.post(BACKEND_URL, json=vehicle_counts, timeout=2)
            except requests.exceptions.RequestException:
                print("    ⚠️ Could not send data to backend.")

        # --- Visual Display ---
        # Draw the detected car contours in BLUE
        cv2.drawContours(frame, detected_cars, -1, (255, 0, 0), 2)
        
        # Draw the ROIs and their live counts
        for name, (x1, y1, x2, y2) in ROIS.items():
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            draw_text_with_background(frame, f"{name.upper()}: {latest_counts.get(name, 0)}", (x1, y1))

        cv2.imshow("Live Traffic Feed", frame)
        cv2.imshow("Detection Mask", fgMask) # Shows you what the computer "sees"

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("🛑 System shutdown.")

if __name__ == "__main__":
    main()

