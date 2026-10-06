import cv2
import pickle
import numpy as np
import supervision as sv
import threading
import time
import sqlite3
import onnxruntime as ort

ort.preload_dlls(directory="")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from insightface.app import FaceAnalysis


# =========================
# FASTAPI
# =========================

app = FastAPI(title="XviSion Camera API")

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

face_app = FaceAnalysis(
    name="buffalo_l",
    providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
)
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
latest_raw_frame = None
latest_state = {
    "running": False,
    "faces": 0,
    "tracks": 0,
    "fps": 0,
    "detections": []
}

lock = threading.Lock()
ai_lock = threading.Lock()

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
# EVENT / ALERT LOGGING
# =========================

last_logged = {}
LOG_COOLDOWN = 10

# Unknown detections are alerts, not normal events.
# Keep this long enough to prevent one unknown person from flooding the alert center.
last_unknown_alert = 0
UNKNOWN_ALERT_COOLDOWN = 60


def ensure_event_tables(conn):
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
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            severity TEXT,
            title TEXT,
            time TEXT,
            confidence REAL,
            track_id INTEGER,
            acknowledged INTEGER DEFAULT 0
        )
    """)
    conn.commit()


def log_event(person, score, track_id):
    """Log recognized people only. Unknown detections go to alerts."""
    global last_unknown_alert

    now = time.time()

    # Unknown = security alert, NOT a normal event.
    if person == "Unknown":
        if now - last_unknown_alert < UNKNOWN_ALERT_COOLDOWN:
            return

        last_unknown_alert = now

        conn = sqlite3.connect("events.db")
        ensure_event_tables(conn)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alerts
            (severity, title, time, confidence, track_id, acknowledged)
            VALUES (?, ?, datetime('now', 'localtime'), ?, ?, 0)
        """, (
            "warning",
            "Unknown person detected",
            float(score),
            int(track_id)
        ))
        conn.commit()
        conn.close()

        print(f"[ALERT] Unknown | ID:{track_id} | Score:{score:.2f}")
        return

    # Recognized people are normal events.
    key = (track_id, person)
    if key in last_logged and now - last_logged[key] < LOG_COOLDOWN:
        return
    last_logged[key] = now

    conn = sqlite3.connect("events.db")
    ensure_event_tables(conn)
    cursor = conn.cursor()
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

    print(f"[EVENT] {person} | ID:{track_id} | Score:{score:.2f}")


# =========================
# CAMERA PROCESSING
# =========================

def camera_loop():

    global latest_frame
    global latest_raw_frame
    global latest_state
    global frame_count
    global last_time

    while True:

        ret, frame = camera.read()

        if not ret:
            time.sleep(0.1)
            continue

        with lock:
            latest_raw_frame = frame.copy()

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

        with ai_lock:
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
            f"XviSion | FPS: {fps:.1f}",
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
# PERSON MANAGEMENT
# =========================

class RegisterPersonRequest(BaseModel):
    name: str


def save_database():
    """Save the face database safely to disk."""
    temp_file = "face_database.pkl.tmp"
    with open(temp_file, "wb") as f:
        pickle.dump(database, f)
    import os
    os.replace(temp_file, "face_database.pkl")


@app.post("/api/people/register")
def register_person(request: RegisterPersonRequest):
    """Capture 30 face embeddings from the live camera and save a person."""
    name = request.name.strip()

    if not name:
        return JSONResponse(
            status_code=400,
            content={"error": "Person name is required"}
        )

    if name in database:
        return JSONResponse(
            status_code=409,
            content={"error": f"{name} is already registered"}
        )

    embeddings = []
    deadline = time.time() + 30
    last_capture = 0

    while len(embeddings) < 30 and time.time() < deadline:
        with lock:
            frame = None if latest_raw_frame is None else latest_raw_frame.copy()

        if frame is None:
            time.sleep(0.1)
            continue

        # Avoid repeatedly saving the same frame too quickly.
        if time.time() - last_capture < 0.12:
            time.sleep(0.03)
            continue

        with ai_lock:
            faces = face_app.get(frame)

        if faces:
            # If multiple faces are visible, use the largest one.
            face = max(
                faces,
                key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])
            )
            if face.embedding is not None:
                embeddings.append(np.asarray(face.embedding, dtype=np.float32))
                last_capture = time.time()

        time.sleep(0.03)

    if len(embeddings) < 30:
        return JSONResponse(
            status_code=408,
            content={
                "error": "Could not capture 30 clear face samples. Keep one face visible and try again.",
                "captured": len(embeddings)
            }
        )

    database[name] = embeddings
    save_database()

    return {
        "success": True,
        "name": name,
        "embeddings": len(embeddings)
    }


@app.delete("/api/people/{name}")
def delete_person(name: str):
    name = name.strip()

    if name not in database:
        return JSONResponse(
            status_code=404,
            content={"error": f"{name} is not registered"}
        )

    del database[name]
    save_database()

    return {
        "success": True,
        "name": name,
        "message": f"{name} removed successfully"
    }


# =========================
# EVENTS
# =========================

@app.get("/api/events")
def events():
    conn = sqlite3.connect("events.db")
    ensure_event_tables(conn)
    cursor = conn.cursor()

    # Unknown detections are intentionally excluded from the event history.
    cursor.execute("""
        SELECT id, person, time, confidence, track_id
        FROM events
        WHERE person != 'Unknown'
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
# ALERTS
# =========================

@app.get("/api/alerts")
def alerts():
    conn = sqlite3.connect("events.db")
    ensure_event_tables(conn)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, severity, title, time, confidence, track_id, acknowledged
        FROM alerts
        ORDER BY id DESC
        LIMIT 100
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "severity": row[1],
            "title": row[2],
            "time": row[3],
            "confidence": row[4],
            "track_id": row[5],
            "acknowledged": bool(row[6])
        }
        for row in rows
    ]


@app.patch("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int):
    conn = sqlite3.connect("events.db")
    ensure_event_tables(conn)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE alerts SET acknowledged = 1 WHERE id = ?",
        (alert_id,)
    )
    conn.commit()
    changed = cursor.rowcount
    conn.close()

    if not changed:
        return JSONResponse(status_code=404, content={"error": "Alert not found"})

    return {"success": True, "id": alert_id}


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
        "database": "SQLite",
        "registered_people": len(database)
    }