# import cv2
# import numpy as np
# import requests
# import time


# # ===================================================================================
# # --- CONFIGURATION & CALIBRATION ---
# # ===================================================================================
# CAMERA_URL = "http://192.168.29.92:8080/video"  # Or use 0 for webcam
# BACKEND_URL = "http://localhost:5001/api/signal-timings"
# UPDATE_INTERVAL = 3

# MIN_CAR_AREA = 2300  # Adjust as needed

# # Resize frames for faster processing (e.g., 640x360)
# FRAME_WIDTH = 640
# FRAME_HEIGHT = 360

# # Adjust ROIs for resized frames (scale coordinates down from 1920x1080 to 640x360)
# ROIS = {
#     "north": (int(855 * FRAME_WIDTH / 1920), 0, int(1065 * FRAME_WIDTH / 1920), int(461 * FRAME_HEIGHT / 1080)),
#     "south": (int(855 * FRAME_WIDTH / 1920), int(618 * FRAME_HEIGHT / 1080), int(1065 * FRAME_WIDTH / 1920), FRAME_HEIGHT),
#     "east":  (int(1065 * FRAME_WIDTH / 1920), int(461 * FRAME_HEIGHT / 1080), FRAME_WIDTH, int(618 * FRAME_HEIGHT / 1080)),
#     "west":  (0, int(461 * FRAME_HEIGHT / 1080), int(855 * FRAME_WIDTH / 1920), int(618 * FRAME_HEIGHT / 1080))
# }

# LANE_LINES = {
#     "yellow_box": ((int(855 * FRAME_WIDTH / 1920), int(461 * FRAME_HEIGHT / 1080)),
#                    (int(1065 * FRAME_WIDTH / 1920), int(618 * FRAME_HEIGHT / 1080))),
#     "west_stop_line": ((int(855 * FRAME_WIDTH / 1920), int(461 * FRAME_HEIGHT / 1080)),
#                        (int(855 * FRAME_WIDTH / 1920), int(618 * FRAME_HEIGHT / 1080))),
#     "east_stop_line": ((int(1065 * FRAME_WIDTH / 1920), int(461 * FRAME_HEIGHT / 1080)),
#                        (int(1065 * FRAME_WIDTH / 1920), int(618 * FRAME_HEIGHT / 1080))),
#     "north_stop_line": ((int(855 * FRAME_WIDTH / 1920), int(461 * FRAME_HEIGHT / 1080)),
#                         (int(1065 * FRAME_WIDTH / 1920), int(461 * FRAME_HEIGHT / 1080))),
#     "south_stop_line": ((int(855 * FRAME_WIDTH / 1920), int(618 * FRAME_HEIGHT / 1080)),
#                         (int(1065 * FRAME_WIDTH / 1920), int(618 * FRAME_HEIGHT / 1080))),
# }


# def draw_text_with_background(frame, text, position, font_scale=0.5, color=(255, 255, 255)):
#     (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)
#     cv2.rectangle(frame, (position[0], position[1]), (position[0] + w + 10, position[1] + h + 10), (0, 0, 0), -1)
#     cv2.putText(frame, text, (position[0] + 5, position[1] + h + 5), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)


# def main():
#     cap = cv2.VideoCapture(CAMERA_URL)
#     if not cap.isOpened():
#         print(f"❌ Could not open camera stream at {CAMERA_URL}")
#         return

#     # Higher history for stable background model, lower varThreshold for subtle changes
#     backSub = cv2.createBackgroundSubtractorMOG2(history=1000, varThreshold=25, detectShadows=True)

#     print("✅ Camera stream opened. System is initializing...")
#     print("🔴 IMPORTANT: Keep the road EMPTY for the first 5 seconds for background calibration.")
#     time.sleep(5)
#     print("🟢 Calibration complete! You can now place cars on the road.")

#     last_backend_update = time.time()
#     latest_counts = {name: 0 for name in ROIS.keys()}

#     kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             print("⚠️ Failed to grab frame. Retrying...")
#             time.sleep(1)
#             continue

#         frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

#         blurred_frame = cv2.GaussianBlur(frame, (5, 5), 0)
#         fgMask = backSub.apply(blurred_frame)

#         # Apply median blur for smoother mask (remove salt and pepper noise)
#         fgMask = cv2.medianBlur(fgMask, 5)

#         fgMask = cv2.morphologyEx(fgMask, cv2.MORPH_OPEN, kernel)

#         contours, _ = cv2.findContours(fgMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

#         detected_cars = []
#         for cnt in contours:
#             area = cv2.contourArea(cnt)
#             if area > MIN_CAR_AREA / ((1920*1080)/(FRAME_WIDTH*FRAME_HEIGHT)):  # scale area threshold for smaller frame
#                 x, y, w, h = cv2.boundingRect(cnt)
#                 aspect_ratio = w / float(h) if h != 0 else 0
#                 if 0.8 < aspect_ratio < 3.5 and h > 15:
#                     detected_cars.append(cnt)

#         current_counts = {name: 0 for name in ROIS.keys()}
#         for name, (x1, y1, x2, y2) in ROIS.items():
#             for car_contour in detected_cars:
#                 M = cv2.moments(car_contour)
#                 if M["m00"] != 0:
#                     cX = int(M["m10"] / M["m00"])
#                     cY = int(M["m01"] / M["m00"])
#                     if x1 < cX < x2 and y1 < cY < y2:
#                         current_counts[name] += 1

#         latest_counts = current_counts

#         current_time = time.time()
#         if current_time - last_backend_update >= UPDATE_INTERVAL:
#             last_backend_update = current_time
#             ns_count = latest_counts.get("north", 0) + latest_counts.get("south", 0)
#             ew_count = latest_counts.get("east", 0) + latest_counts.get("west", 0)
#             vehicle_counts = {"ns_vehicles": ns_count, "ew_vehicles": ew_count}
#             print(f"--> SENDING TO BACKEND: {vehicle_counts}")
#             try:
#                 requests.post(BACKEND_URL, json=vehicle_counts, timeout=2)
#             except requests.exceptions.RequestException:
#                 print("    ⚠️ Could not send data to backend.")

#         # Visual Display in smaller window
#         cv2.rectangle(frame, LANE_LINES["yellow_box"][0], LANE_LINES["yellow_box"][1], (0, 255, 255), 2)
#         for name, coords in LANE_LINES.items():
#             if "line" in name:
#                 cv2.line(frame, coords[0], coords[1], (255, 255, 255), 2)

#         for car_contour in detected_cars:
#             x, y, w, h = cv2.boundingRect(car_contour)
#             cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

#         for name, (x1, y1, x2, y2) in ROIS.items():
#             cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
#             draw_text_with_background(frame, f"{name.upper()}: {latest_counts.get(name, 0)}", (x1 + 5, y1 + 5))

#         cv2.imshow("Live Traffic Feed (Small)", frame)
#         cv2.imshow("Detection Mask (Small)", cv2.resize(fgMask, (FRAME_WIDTH, FRAME_HEIGHT)))


#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

#     cap.release()
#     cv2.destroyAllWindows()
#     print("🛑 System shutdown.")


# if __name__ == "__main__":
#     main()



import cv2
import numpy as np
import requests
import time


# ===================================================================================
# --- CONFIGURATION & CALIBRATION ---
# ===================================================================================
CAMERA_URL = "http://192.168.29.92:8080/video"  # Or use 0 for webcam
BACKEND_URL = "http://localhost:5001/api/signal-timings"
UPDATE_INTERVAL = 3

MIN_CAR_AREA = 2300  # Adjust as needed

# Resize frames for faster processing (e.g., 640x360)
FRAME_WIDTH = 640
FRAME_HEIGHT = 360

# Original ROIs scaled down from 1920x1080 to 640x360
ROIS = {
    "north": (int(855 * FRAME_WIDTH / 1920), 0, int(1065 * FRAME_WIDTH / 1920), int(461 * FRAME_HEIGHT / 1080)),
    "south": (int(855 * FRAME_WIDTH / 1920), int(618 * FRAME_HEIGHT / 1080), int(1065 * FRAME_WIDTH / 1920), FRAME_HEIGHT),
    "east":  (int(1065 * FRAME_WIDTH / 1920), int(461 * FRAME_HEIGHT / 1080), FRAME_WIDTH, int(618 * FRAME_HEIGHT / 1080)),
    "west":  (0, int(461 * FRAME_HEIGHT / 1080), int(855 * FRAME_WIDTH / 1920), int(618 * FRAME_HEIGHT / 1080))
}

# Function to widen ROI keeping center fixed
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

# Widen all ROIs
ROIS = {name: widen_roi(*coords, width_increase=50, height_increase=20) for name, coords in ROIS.items()}

LANE_LINES = {
    "yellow_box": ((int(855 * FRAME_WIDTH / 1920), int(461 * FRAME_HEIGHT / 1080)),
                   (int(1065 * FRAME_WIDTH / 1920), int(618 * FRAME_HEIGHT / 1080))),
    "west_stop_line": ((int(855 * FRAME_WIDTH / 1920), int(461 * FRAME_HEIGHT / 1080)),
                       (int(855 * FRAME_WIDTH / 1920), int(618 * FRAME_HEIGHT / 1080))),
    "east_stop_line": ((int(1065 * FRAME_WIDTH / 1920), int(461 * FRAME_HEIGHT / 1080)),
                       (int(1065 * FRAME_WIDTH / 1920), int(618 * FRAME_HEIGHT / 1080))),
    "north_stop_line": ((int(855 * FRAME_WIDTH / 1920), int(461 * FRAME_HEIGHT / 1080)),
                        (int(1065 * FRAME_WIDTH / 1920), int(461 * FRAME_HEIGHT / 1080))),
    "south_stop_line": ((int(855 * FRAME_WIDTH / 1920), int(618 * FRAME_HEIGHT / 1080)),
                        (int(1065 * FRAME_WIDTH / 1920), int(618 * FRAME_HEIGHT / 1080))),
}


def draw_text_with_background(frame, text, position, font_scale=0.5, color=(255, 255, 255)):
    (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)
    cv2.rectangle(frame, (position[0], position[1]), (position[0] + w + 10, position[1] + h + 10), (0, 0, 0), -1)
    cv2.putText(frame, text, (position[0] + 5, position[1] + h + 5), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)


def main():
    cap = cv2.VideoCapture(CAMERA_URL)
    if not cap.isOpened():
        print(f"❌ Could not open camera stream at {CAMERA_URL}")
        return

    backSub = cv2.createBackgroundSubtractorMOG2(history=1000, varThreshold=25, detectShadows=True)

    print("✅ Camera stream opened. System is initializing...")
    print("🔴 IMPORTANT: Keep the road EMPTY for the first 5 seconds for background calibration.")
    time.sleep(5)
    print("🟢 Calibration complete! You can now place cars on the road.")

    last_backend_update = time.time()
    latest_counts = {name: 0 for name in ROIS.keys()}

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Failed to grab frame. Retrying...")
            time.sleep(1)
            continue

        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        blurred_frame = cv2.GaussianBlur(frame, (5, 5), 0)
        fgMask = backSub.apply(blurred_frame)

        fgMask = cv2.medianBlur(fgMask, 5)
        fgMask = cv2.morphologyEx(fgMask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(fgMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detected_cars = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > MIN_CAR_AREA / ((1920*1080)/(FRAME_WIDTH*FRAME_HEIGHT)):
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = w / float(h) if h != 0 else 0
                if 0.8 < aspect_ratio < 3.5 and h > 15:
                    detected_cars.append(cnt)

        current_counts = {name: 0 for name in ROIS.keys()}
        for name, (x1, y1, x2, y2) in ROIS.items():
            for car_contour in detected_cars:
                M = cv2.moments(car_contour)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    if x1 < cX < x2 and y1 < cY < y2:
                        current_counts[name] += 1

        latest_counts = current_counts

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

        # Visual Display in smaller window
        cv2.rectangle(frame, LANE_LINES["yellow_box"][0], LANE_LINES["yellow_box"][1], (0, 255, 255), 2)
        for name, coords in LANE_LINES.items():
            if "line" in name:
                cv2.line(frame, coords[0], coords[1], (255, 255, 255), 2)

        for car_contour in detected_cars:
            x, y, w, h = cv2.boundingRect(car_contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        for name, (x1, y1, x2, y2) in ROIS.items():
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            draw_text_with_background(frame, f"{name.upper()}: {latest_counts.get(name, 0)}", (x1 + 5, y1 + 5))

        cv2.imshow("Live Traffic Feed (Small)", frame)
        cv2.imshow("Detection Mask (Small)", cv2.resize(fgMask, (FRAME_WIDTH, FRAME_HEIGHT)))

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("🛑 System shutdown.")


if __name__ == "__main__":
    main()
