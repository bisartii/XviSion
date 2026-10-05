import cv2
import pickle
import numpy as np
import supervision as sv
import threading
import time
import sqlite3

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from insightface.app import FaceAnalysis


# =========================
# FASTAPI
# =========================

app = FastAPI(title="Terra Vision Camera API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# FACE AI
# =========================

print("Loading AI model...")

face_app = FaceAnalysis(name="buffalo_l")
face_app.prepare(
    ctx_id=0,
    det_size=(320, 320)
)

print("AI model loaded!")


# =========================
# DATABASE
# =========================

with open("face_database.pkl", "rb") as f:
    database = pickle.load(f)


# =========================
# BYTE TRACK
# =========================

tracker = sv.ByteTrack()


# =========================
# CAMERA
# =========================

camera = cv2.VideoCapture(0)

camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not camera.isOpened():
    print("ERROR: Webcam could not be opened!")


# Shared data
latest_frame = None
latest_state = {
    "running": False,
    "faces": 0,
    "tracks": 0,
    "fps": 0,
    "detections": []
}

lock = threading.Lock()

last_time = time.time()
frame_count = 0


# =========================
# RECOGNITION
# =========================

def recognize_face(embedding):

    best_name = "Unknown"
    best_score = -1

    for name, db_embeddings in database.items():

        for db_embedding in db_embeddings:

            score = np.dot(
                embedding,
                db_embedding
            ) / (
                np.linalg.norm(embedding)
                * np.linalg.norm(db_embedding)
            )

            if score > best_score:
                best_score = score
                best_name = name

    # Starter threshold
    if best_score < 0.45:
        best_name = "Unknown"

    return best_name, best_score


# =========================
# EVENT LOGGING
# =========================

last_logged = {}
LOG_COOLDOWN = 10


def log_event(person, score, track_id):

    key = (track_id, person)

    now = time.time()

    if key in last_logged:

        if now - last_logged[key] < LOG_COOLDOWN:
            return

    last_logged[key] = now

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

    cursor.execute("""
        INSERT INTO events
        (person, time, confidence, track_id)
        VALUES (?, datetime('now', 'localtime'), ?, ?)
    """, (
        person,
        float(score),
        int(track_id)
    ))

    conn.commit()
    conn.close()

    print(
        f"[EVENT] {person} | "
        f"ID:{track_id} | "
        f"Score:{score:.2f}"
    )


# =========================
# CAMERA PROCESSING
# =========================

def camera_loop():

    global latest_frame
    global latest_state
    global frame_count
    global last_time

    while True:

        ret, frame = camera.read()

        if not ret:
            time.sleep(0.1)
            continue

        frame_count += 1

        # -------------------------
        # FPS
        # -------------------------

        current_time = time.time()

        if current_time - last_time >= 1:

            fps = frame_count / (
                current_time - last_time
            )

            frame_count = 0
            last_time = current_time

        else:
            fps = latest_state["fps"]


        # -------------------------
        # INSIGHTFACE
        # -------------------------

        faces = face_app.get(frame)


        # -------------------------
        # BYTE TRACK
        # -------------------------

        detections = []

        for face in faces:

            x1, y1, x2, y2 = face.bbox

            detections.append([
                x1,
                y1,
                x2,
                y2,
                face.det_score
            ])


        if detections:

            detections = np.array(
                detections,
                dtype=np.float32
            )

            xyxy = detections[:, :4]

            confidence = detections[:, 4]

            sv_detections = sv.Detections(
                xyxy=xyxy,
                confidence=confidence,
                class_id=np.zeros(
                    len(xyxy),
                    dtype=int
                )
            )

            tracked = tracker.update_with_detections(
                sv_detections
            )

        else:

            tracked = sv.Detections.empty()


        results = []


        # -------------------------
        # MATCH TRACKS TO FACES
        # -------------------------

        for i in range(len(tracked)):

            x1, y1, x2, y2 = map(
                int,
                tracked.xyxy[i]
            )

            track_id = tracked.tracker_id[i]

            if track_id is None:
                continue


            # Find closest detected face
            best_face = None
            best_distance = float("inf")

            track_center_x = (x1 + x2) / 2
            track_center_y = (y1 + y2) / 2


            for face in faces:

                fx1, fy1, fx2, fy2 = face.bbox

                face_center_x = (
                    fx1 + fx2
                ) / 2

                face_center_y = (
                    fy1 + fy2
                ) / 2

                distance = (
                    (face_center_x - track_center_x) ** 2
                    +
                    (face_center_y - track_center_y) ** 2
                )

                if distance < best_distance:

                    best_distance = distance
                    best_face = face


            if best_face is None:
                continue


            # -------------------------
            # FACE RECOGNITION
            # -------------------------

            name, score = recognize_face(
                best_face.embedding
            )


            # -------------------------
            # LOG EVENT
            # -------------------------

            log_event(
                name,
                score,
                track_id
            )


            # -------------------------
            # DRAW BOX
            # -------------------------

            label = (
                f"{name} | "
                f"ID:{track_id} | "
                f"{score:.2f}"
            )

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            cv2.rectangle(
                frame,
                (x1, y1 - 30),
                (x1 + 250, y1),
                (0, 255, 0),
                -1
            )

            cv2.putText(
                frame,
                label,
                (x1 + 5, y1 - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 0, 0),
                2
            )


            # -------------------------
            # SAVE STATE
            # -------------------------

            results.append({
                "name": name,
                "confidence": round(
                    float(score),
                    3
                ),
                "track_id": int(track_id),
                "bbox": [
                    x1,
                    y1,
                    x2,
                    y2
                ]
            })


        # -------------------------
        # DRAW SYSTEM INFO
        # -------------------------

        cv2.putText(
            frame,
            f"Terra Vision | FPS: {fps:.1f}",
            (15, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )


        # -------------------------
        # JPEG ENCODE
        # -------------------------

        success, encoded = cv2.imencode(
            ".jpg",
            frame,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                80
            ]
        )

        if success:

            with lock:

                latest_frame = encoded.tobytes()

                latest_state = {
                    "running": True,
                    "faces": len(faces),
                    "tracks": len(results),
                    "fps": round(fps, 1),
                    "detections": results
                }


# =========================
# START CAMERA THREAD
# =========================

threading.Thread(
    target=camera_loop,
    daemon=True
).start()


# =========================
# VIDEO STREAM
# =========================

def generate_frames():

    while True:

        with lock:
            frame = latest_frame

        if frame is None:

            time.sleep(0.01)
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame
            + b"\r\n"
        )


@app.get("/video")
def video():

    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


# =========================
# CAMERA STATE
# =========================

@app.get("/api/camera/state")
def camera_state():

    with lock:
        return JSONResponse(
            content=latest_state
        )


# =========================
# PEOPLE
# =========================

@app.get("/api/people")
def people():

    result = []

    for name, embeddings in database.items():

        result.append({
            "name": name,
            "embeddings": len(embeddings)
        })

    return result


# =========================
# EVENTS
# =========================

@app.get("/api/events")
def events():

    conn = sqlite3.connect(
        "events.db"
    )

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            person,
            time,
            confidence,
            track_id
        FROM events
        ORDER BY id DESC
        LIMIT 100
    """)

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "person": row[1],
            "time": row[2],
            "confidence": row[3],
            "track_id": row[4]
        }

        for row in rows
    ]


# =========================
# STATUS
# =========================

@app.get("/api/status")
def status():

    return {
        "ai_engine": "ONLINE",
        "tracking": "ByteTrack",
        "recognition": "ArcFace",
        "face_detection": "SCRFD",
        "gpu": "RTX 3050",
        "database": "SQLite"
    }