import cv2
import pickle
import numpy as np
import supervision as sv
import sqlite3
import time
from datetime import datetime
from insightface.app import FaceAnalysis

# -----------------------------
# Load InsightFace
# -----------------------------
app = FaceAnalysis(name="buffalo_l")
app.prepare(ctx_id=0, det_size=(320, 320))

# -----------------------------
# Load face database
# -----------------------------
with open("face_database.pkl", "rb") as f:
    database = pickle.load(f)

# -----------------------------
# SQLite database
# -----------------------------
conn = sqlite3.connect("events.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person TEXT,
    time TEXT,
    confidence REAL,
    track_id INTEGER
)
""")

conn.commit()

# -----------------------------
# ByteTrack
# -----------------------------
tracker = sv.ByteTrack()

# Prevent duplicate logging
last_logged = {}

LOG_COOLDOWN = 10   # seconds

# -----------------------------
# Webcam
# -----------------------------
cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

while True:

    ret, frame = cap.read()

    if not ret:
        break

    # -----------------------------
    # Face detection
    # -----------------------------
    faces = app.get(frame)

    detections = []

    for face in faces:

        x1, y1, x2, y2 = face.bbox

        detections.append([
            x1, y1, x2, y2, face.det_score
        ])

    # -----------------------------
    # Tracking
    # -----------------------------
    if detections:

        detections = np.array(detections)

        sv_detections = sv.Detections(
            xyxy=detections[:, :4],
            confidence=detections[:, 4],
            class_id=np.zeros(len(detections))
        )

        tracked = tracker.update_with_detections(
            sv_detections
        )

    else:

        tracked = sv.Detections.empty()

    # -----------------------------
    # Recognition
    # -----------------------------
    for i in range(len(tracked)):

        x1, y1, x2, y2 = map(
            int,
            tracked.xyxy[i]
        )

        track_id = int(tracked.tracker_id[i])

        # Find matching InsightFace face
        best_face = None
        best_distance = float("inf")

        for face in faces:

            fx1, fy1, fx2, fy2 = face.bbox

            distance = abs(
                ((fx1 + fx2) / 2) -
                ((x1 + x2) / 2)
            )

            if distance < best_distance:

                best_distance = distance
                best_face = face

        if best_face is None:
            continue

        embedding = best_face.embedding

        best_name = "Unknown"
        best_score = -1

        # -----------------------------
        # Compare embeddings
        # -----------------------------
        for name, db_embeddings in database.items():

            for db_embedding in db_embeddings:

                score = np.dot(
                    embedding,
                    db_embedding
                ) / (
                    np.linalg.norm(embedding) *
                    np.linalg.norm(db_embedding)
                )

                if score > best_score:

                    best_score = score
                    best_name = name

        if best_score < 0.45:
            best_name = "Unknown"

        # -----------------------------
        # Event logging
        # -----------------------------
        current_time = time.time()

        key = (track_id, best_name)

        if (
            key not in last_logged
            or current_time - last_logged[key] > LOG_COOLDOWN
        ):

            now = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            cursor.execute(
                """
                INSERT INTO events
                (person, time, confidence, track_id)
                VALUES (?, ?, ?, ?)
                """,
                (
                    best_name,
                    now,
                    float(best_score),
                    track_id
                )
            )

            conn.commit()

            last_logged[key] = current_time

            print(
                f"[EVENT] {now} | "
                f"{best_name} | "
                f"ID:{track_id} | "
                f"Score:{best_score:.2f}"
            )

        # -----------------------------
        # Draw
        # -----------------------------
        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        text = (
            f"{best_name} | "
            f"ID:{track_id} | "
            f"{best_score:.2f}"
        )

        cv2.putText(
            frame,
            text,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

    cv2.imshow(
        "AI Face Tracking",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# -----------------------------
# Cleanup
# -----------------------------
cap.release()
cv2.destroyAllWindows()
conn.close()