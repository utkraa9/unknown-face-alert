"""
encode_faces.py
Scans the known_faces/ directory and builds a pickle file of face encodings.

Expected folder structure:
    known_faces/
        Alice/
            img1.jpg
            img2.jpg
        Bob/
            img1.jpg

Run:
    python encode_faces.py
"""

import os
import pickle
import face_recognition

KNOWN_FACES_DIR = "known_faces"
ENCODINGS_FILE = "encodings.pickle"


def build_encodings():
    known_encodings = []
    known_names = []

    if not os.path.isdir(KNOWN_FACES_DIR):
        raise SystemExit(f"'{KNOWN_FACES_DIR}' folder not found. Create it and add subfolders per person.")

    for person_name in sorted(os.listdir(KNOWN_FACES_DIR)):
        person_dir = os.path.join(KNOWN_FACES_DIR, person_name)
        if not os.path.isdir(person_dir):
            continue

        for filename in os.listdir(person_dir):
            if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            path = os.path.join(person_dir, filename)
            print(f"[ENCODING] {path}")
            image = face_recognition.load_image_file(path)
            boxes = face_recognition.face_locations(image, model="hog")

            if len(boxes) == 0:
                print(f"  -> No face found, skipping.")
                continue

            encodings = face_recognition.face_encodings(image, boxes)
            for enc in encodings:
                known_encodings.append(enc)
                known_names.append(person_name)

    data = {"encodings": known_encodings, "names": known_names}
    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump(data, f)

    print(f"\nDone. Saved {len(known_encodings)} encodings for {len(set(known_names))} people to {ENCODINGS_FILE}")


if __name__ == "__main__":
    build_encodings()
