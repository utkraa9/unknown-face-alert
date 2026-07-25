"""
detect_faces.py
Real-time webcam face recognition. Known faces are matched by name.
Any face that does NOT match a known encoding is treated as "unknown":
  - a snapshot is saved locally
  - a POST request (image + metadata) is sent to your n8n Webhook URL

Run:
    python detect_faces.py
Press 'q' to quit the preview window.
"""

import os
import cv2
import time
import pickle
import requests
import face_recognition
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

ENCODINGS_FILE = "encodings.pickle"
SNAPSHOT_DIR = "snapshots"
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/unknown-face")
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
TOLERANCE = float(os.getenv("TOLERANCE", "0.5"))   # lower = stricter match
FRAME_RESIZE_SCALE = 0.25                           # speed optimization
PROCESS_EVERY_N_FRAMES = 1                         # skip frames for speed
ALERT_COOLDOWN_SECONDS = int(os.getenv("ALERT_COOLDOWN_SECONDS", "30"))

os.makedirs(SNAPSHOT_DIR, exist_ok=True)


def load_known_faces():
    if not os.path.exists(ENCODINGS_FILE):
        raise SystemExit(
            f"'{ENCODINGS_FILE}' not found. Run 'python encode_faces.py' first."
        )
    with open(ENCODINGS_FILE, "rb") as f:
        data = pickle.load(f)
    return data["encodings"], data["names"]


def send_alert(image_path, label="unknown"):
    """POST the snapshot + metadata to the n8n webhook."""
    try:
        with open(image_path, "rb") as img_file:
            files = {"file": (os.path.basename(image_path), img_file, "image/jpeg")}
            payload = {
                "event": "unknown_face_detected",
                "label": label,
                "timestamp": datetime.now().isoformat(),
                "camera_id": "cam-01",
            }
            resp = requests.post(N8N_WEBHOOK_URL, data=payload, files=files, timeout=5)
            print(f"[ALERT] Sent to n8n -> status {resp.status_code}")
    except Exception as e:
        print(f"[ALERT] Failed to send webhook: {e}")


def main():
    known_encodings, known_names = load_known_faces()
    print(f"Loaded {len(known_encodings)} known encodings for: {sorted(set(known_names))}")

    video = cv2.VideoCapture(CAMERA_INDEX)
    if not video.isOpened():
        raise SystemExit("Could not open webcam. Check CAMERA_INDEX.")

    frame_count = 0
    last_alert_time = 0

    print("Starting detection. Press 'q' to quit.")

    while True:
        ret, frame = video.read()
        if not ret:
            print("Failed to grab frame.")
            break

        frame_count += 1
        process_this_frame = frame_count % PROCESS_EVERY_N_FRAMES == 0

        if process_this_frame:
            small_frame = cv2.resize(frame, (0, 0), fx=FRAME_RESIZE_SCALE, fy=FRAME_RESIZE_SCALE)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            unknown_present = False

            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=TOLERANCE)
                name = "Unknown"

                if True in matches:
                    distances = face_recognition.face_distance(known_encodings, face_encoding)
                    best_match_index = distances.argmin()
                    if matches[best_match_index]:
                        name = known_names[best_match_index]
                else:
                    unknown_present = True

                face_names.append(name)

            # draw boxes on the full-res frame
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                scale = int(1 / FRAME_RESIZE_SCALE)
                top, right, bottom, left = top * scale, right * scale, bottom * scale, left * scale
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # trigger alert with cooldown so it doesn't spam n8n
            now = time.time()
            if unknown_present and (now - last_alert_time) > ALERT_COOLDOWN_SECONDS:
                last_alert_time = now
                filename = f"unknown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                filepath = os.path.join(SNAPSHOT_DIR, filename)
                cv2.imwrite(filepath, frame)
                print(f"[UNKNOWN FACE] Saved snapshot -> {filepath}")
                send_alert(filepath)

        cv2.imshow("Unknown Face Detection - press q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    video.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
