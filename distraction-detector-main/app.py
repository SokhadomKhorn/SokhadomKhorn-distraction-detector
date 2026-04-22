import cv2
import numpy as np
import time
import winsound
from ultralytics import YOLO

from logger import log_distracted_alert

model = YOLO("best.pt")

results = model.predict(
    source=0,        # 0 = default camera
    show=False,      # don't use built-in display, we'll handle it
    conf=0.25,
    stream=True
)

distracted_start_time = None
last_alert_time = None


def draw_hud(frame, status, status_color, alert_on):
    header_height = 96 if not alert_on else 128
    header = np.full((header_height, frame.shape[1], 3), (14, 14, 20), dtype=np.uint8)

    # Clean gradient-style tint on header for a nicer HUD look.
    tint = np.full_like(header, (28, 24, 34))
    header = cv2.addWeighted(header, 0.82, tint, 0.18, 0)

    # Accent separator line.
    cv2.line(header, (0, 0), (frame.shape[1], 0), (90, 190, 255), 2)
    cv2.line(header, (0, header_height - 1), (frame.shape[1], header_height - 1), (34, 34, 44), 1)

    def put_clean_text(img, text, org, scale, color, thickness=1):
        shadow_org = (org[0] + 1, org[1] + 1)
        cv2.putText(
            img,
            text,
            shadow_org,
            cv2.FONT_HERSHEY_DUPLEX,
            scale,
            (0, 0, 0),
            thickness + 1,
            cv2.LINE_AA,
        )
        cv2.putText(
            img,
            text,
            org,
            cv2.FONT_HERSHEY_DUPLEX,
            scale,
            color,
            thickness,
            cv2.LINE_AA,
        )

    status_label = f"STATUS: {status}"
    put_clean_text(header, "Press Q to Quit", (frame.shape[1] - 184, 31), 0.58, (200, 200, 200), 1)
    put_clean_text(header, status_label, (30, 68), 0.88, (240, 240, 240), 1)

    if alert_on:
        cv2.rectangle(header, (16, 94), (frame.shape[1] - 16, 120), (18, 18, 26), -1)
        cv2.rectangle(header, (16, 94), (frame.shape[1] - 16, 120), (0, 0, 190), 2)
        put_clean_text(
            header,
            "ALERT: DISTRACTION EXCEEDED 5 SECONDS",
            (24, 113),
            0.56,
            (255, 255, 255),
            1,
        )

    return np.vstack((header, frame))

for result in results:
    # Keep model-drawn bounding boxes/labels on the video frame
    frame = result.plot()
    is_distracted = False
    has_phone = False
    # For this custom model, any detection usually implies presence in frame.
    person_detected = len(result.boxes) > 0
    
    if len(result.boxes) == 0:
        print("Nothing detected.")
    else:
        for box in result.boxes:
            class_id = int(box.cls)
            class_name = model.names[class_id]
            confidence = float(box.conf)
            print(f"{class_name}: {confidence:.2%}")
            
            # Check for person-like classes if available
            if any(tag in class_name.lower() for tag in ["person", "face", "driver"]):
                person_detected = True
            
            # Check for phone or distraction
            if "phone" in class_name.lower():
                has_phone = True
            if "distracted" in class_name.lower():
                is_distracted = True
    
    # Determine status
    if not person_detected:
        status = "NO PERSON DETECTED"
        status_color = (0, 165, 255)  # Orange
        distracted_start_time = None
        last_alert_time = None
    elif is_distracted or has_phone:
        status = "DISTRACTED"
        status_color = (0, 0, 255)  # Red
        if distracted_start_time is None:
            distracted_start_time = time.time()
            last_alert_time = distracted_start_time
    else:
        status = "FOCUSED"
        status_color = (0, 255, 0)  # Green
        distracted_start_time = None
        last_alert_time = None

    # Trigger alert every 5 seconds while distracted.
    # Show alert text only after the first 5-second threshold is reached.
    alert_on = False
    if status == "DISTRACTED" and distracted_start_time is not None:
        current_time = time.time()
        distracted_elapsed = current_time - distracted_start_time
        alert_on = (current_time - distracted_start_time) >= 5
        if last_alert_time is not None and (current_time - last_alert_time) >= 5:
            alert_message = "ALERT: User has been distracted for 5 seconds"
            print(alert_message)
            log_distracted_alert(alert_message)
            winsound.Beep(880, 300)
            last_alert_time = current_time
    else:
        distracted_elapsed = 0

    display_frame = draw_hud(frame, status, status_color, alert_on)
    
    # Display frame
    cv2.imshow("Distraction Detector", display_frame)
    
    # Handle quit key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Quitting...")
        break

cv2.destroyAllWindows()