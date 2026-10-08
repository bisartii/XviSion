import cv2
import pickle
import numpy as np
import supervision as sv
import threading
import time
import sqlite3
import hashlib
import secrets
import os
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta
import onnxruntime as ort

ort.preload_dlls(directory="")
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
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
# AUTHENTICATION DATABASE
# =========================

AUTH_DB = "auth.db"
SESSION_DAYS = 7

def auth_connection():
    return sqlite3.connect(AUTH_DB)


def init_auth_db():
    conn = auth_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 310000
    ).hex()


def create_session(user_id):
    token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expires = (datetime.utcnow() + timedelta(days=SESSION_DAYS)).isoformat()
    conn = auth_connection()
    conn.execute(
        "INSERT INTO sessions (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
        (user_id, token_hash, expires)
    )
    conn.commit()
    conn.close()
    return token


def current_user(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = authorization.split(" ", 1)[1].strip()
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    conn = auth_connection()
    row = conn.execute("""
        SELECT users.id, users.name, users.email, sessions.expires_at
        FROM sessions JOIN users ON users.id = sessions.user_id
        WHERE sessions.token_hash = ?
    """, (token_hash,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid session")

    try:
        expired = datetime.fromisoformat(row[3]) <= datetime.utcnow()
    except ValueError:
        expired = True

    if expired:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
        conn.commit()
        conn.close()
        raise HTTPException(status_code=401, detail="Session expired")

    conn.close()
    return {"id": row[0], "name": row[1], "email": row[2]}


def auth_user_response(user):
    return {"id": user[0], "name": user[1], "email": user[2]}


init_auth_db()


# =========================
# AUTH API
# =========================

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/auth/signup")
def signup(request: SignupRequest):
    name = request.name.strip()
    email = request.email.strip().lower()
    password = request.password

    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Enter a valid email")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    salt = secrets.token_hex(16)
    password_hash = hash_password(password, salt)

    conn = auth_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, salt, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, email, password_hash, salt, datetime.now().isoformat(timespec="seconds"))
        )
        user_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    conn.close()

    token = create_session(user_id)
    return {"token": token, "user": {"id": user_id, "name": name, "email": email}}


@app.post("/api/auth/login")
def login(request: LoginRequest):
    email = request.email.strip().lower()
    conn = auth_connection()
    row = conn.execute(
        "SELECT id, name, email, password_hash, salt FROM users WHERE email = ?",
        (email,)
    ).fetchone()
    conn.close()

    if not row or not secrets.compare_digest(hash_password(request.password, row[4]), row[3]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_session(row[0])
    return {"token": token, "user": auth_user_response(row)}


@app.get("/api/auth/me")
def me(authorization: str | None = Header(default=None)):
    return current_user(authorization)


@app.post("/api/auth/logout")
def logout(authorization: str | None = Header(default=None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1].strip()
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        conn = auth_connection()
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
        conn.commit()
        conn.close()
    return {"success": True}


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

last_unknown_alerts = {}
UNKNOWN_ALERT_COOLDOWN = 60


# =========================
# TELEGRAM
# =========================

load_dotenv(Path(__file__).resolve().parent / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("XVISION_TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("XVISION_TELEGRAM_CHAT_ID", "").strip()

print(f"[TELEGRAM] configured: {bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)}")

def send_telegram_alert(track_id, score, frame=None):
    """Send unknown-person alert with optional CCTV snapshot."""

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    message = (
        "🚨 *XviSion Security Alert*\n\n"
        "⚠️ Unknown person detected.\n"
        f"📷 Camera: `CAM-01`\n"
        f"🆔 Track ID: `{int(track_id)}`\n"
        f"🎯 Confidence: `{float(score) * 100:.1f}%`\n"
        f"🕐 Time: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
    )

    try:

        # --------------------------------
        # If no frame → send normal message
        # --------------------------------
        if frame is None:

            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

            payload = urllib.parse.urlencode({
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown"
            }).encode("utf-8")

            request = urllib.request.Request(
                url,
                data=payload,
                method="POST"
            )

            with urllib.request.urlopen(request, timeout=5) as response:
                return 200 <= response.status < 300

        # --------------------------------
        # Convert OpenCV frame → JPEG
        # --------------------------------
        success, encoded = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 80]
        )

        if not success:
            print("[TELEGRAM] Could not encode snapshot")
            return False

        # --------------------------------
        # Send photo to Telegram
        # --------------------------------
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"

        boundary = "----XviSionBoundary"

        body = bytearray()

        # chat_id
        body.extend(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
            f"{TELEGRAM_CHAT_ID}\r\n".encode()
        )

        # caption
        body.extend(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="caption"\r\n\r\n'
            f"{message}\r\n".encode()
        )

        body.extend(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="parse_mode"\r\n\r\n'
            f"Markdown\r\n".encode()
        )

        # photo
        body.extend(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="photo"; filename="xvision_alert.jpg"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n".encode()
        )

        body.extend(encoded.tobytes())
        body.extend(f"\r\n--{boundary}--\r\n".encode())

        request = urllib.request.Request(
            url,
            data=bytes(body),
            method="POST",
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}"
            }
        )

        with urllib.request.urlopen(request, timeout=10) as response:

            success = 200 <= response.status < 300

            if success:
                print("[TELEGRAM] Snapshot alert sent")

            return success

    except Exception as exc:

        print(f"[TELEGRAM ERROR] {exc}")

        return False
    """Send one unknown-person alert to the configured Telegram chat."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[TELEGRAM] Not configured.")
        return False

    message = (
        "🚨 *XviSion Security Alert*\n\n"
        "Unknown person detected.\n"
        f"Track ID: `{int(track_id)}`\n"
        f"Confidence: `{float(score) * 100:.1f}%`\n"
        f"Time: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }).encode("utf-8")

    try:
        request = urllib.request.Request(url, data=payload, method="POST")
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8", errors="replace")
            data = json.loads(body)

            if 200 <= response.status < 300 and data.get("ok"):
                print("[TELEGRAM] Alert sent successfully.")
                return True

            print(f"[TELEGRAM ERROR] {body}")
            return False

    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"[TELEGRAM ERROR] HTTP {exc.code}: {body}")
        return False

    except Exception as exc:
        print(f"[TELEGRAM ERROR] {exc}")
        return False


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

def log_event(person, score, track_id, frame=None):
    """Log recognized people only. Unknown detections go to alerts."""
    now = time.time()

    # Unknown = security alert, NOT a normal event.
    # Each new track can trigger an alert. The same track is rate-limited
    # so one person standing in front of the camera does not flood the system.
    if person == "Unknown":
        last_alert = last_unknown_alerts.get(int(track_id), 0)
        if now - last_alert < UNKNOWN_ALERT_COOLDOWN:
            return

        last_unknown_alerts[int(track_id)] = now

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

        # Phone notification is sent only after the alert is stored.
        send_telegram_alert(track_id, score, frame)

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
    track_id,
    frame.copy()
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
def camera_state(authorization: str | None = Header(default=None)):

    current_user(authorization)

    with lock:
        return JSONResponse(
            content=latest_state
        )


# =========================
# PEOPLE
# =========================

@app.get("/api/people")
def people(authorization: str | None = Header(default=None)):

    current_user(authorization)

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
def register_person(request: RegisterPersonRequest, authorization: str | None = Header(default=None)):
    current_user(authorization)
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
def delete_person(name: str, authorization: str | None = Header(default=None)):
    current_user(authorization)
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
def events(authorization: str | None = Header(default=None)):
    current_user(authorization)
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
def alerts(authorization: str | None = Header(default=None)):
    current_user(authorization)
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
def acknowledge_alert(alert_id: int, authorization: str | None = Header(default=None)):
    current_user(authorization)
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
# NOTIFICATIONS
# =========================

@app.get("/api/notifications/status")
def notification_status(authorization: str | None = Header(default=None)):
    current_user(authorization)
    return {
        "configured": bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID),
        "provider": "Telegram",
        "chat_id_configured": bool(TELEGRAM_CHAT_ID),
    }


# =========================
# STATUS
# =========================

@app.get("/api/status")
def status(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with lock:
        state = dict(latest_state)

    return {
        "ai_engine": "ONLINE",
        "tracking": "ByteTrack",
        "recognition": "ArcFace",
        "face_detection": "SCRFD",
        "gpu": "RTX 3050",
        "database": "SQLite",
        "registered_people": len(database),
        "camera_running": bool(state.get("running")),
        "fps": state.get("fps", 0),
        "faces": state.get("faces", 0),
        "tracks": state.get("tracks", 0),
        "detections": state.get("detections", []),
        "phone_notifications": bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
    }


@app.get("/api/dashboard")
def dashboard(authorization: str | None = Header(default=None)):
    """Real dashboard numbers from the camera state and SQLite event database."""
    current_user(authorization)

    conn = sqlite3.connect("events.db")
    ensure_event_tables(conn)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM events WHERE date(time, 'localtime') = date('now', 'localtime')")
    events_today = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM alerts WHERE date(time, 'localtime') = date('now', 'localtime')")
    alerts_today = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM alerts WHERE acknowledged = 0")
    active_alerts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM alerts WHERE date(time, 'localtime') = date('now', 'localtime')")
    unknown_today = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM events WHERE date(time, 'localtime') = date('now', 'localtime')")
    recognized_today = cursor.fetchone()[0]

    cursor.execute("""
        SELECT id, person, time, confidence, track_id
        FROM events
        ORDER BY id DESC
        LIMIT 6
    """)
    recent_rows = cursor.fetchall()

    conn.close()

    with lock:
        state = dict(latest_state)

    return {
        "faces_detected": state.get("faces", 0),
        "recognized_today": recognized_today,
        "unknown_today": unknown_today,
        "active_tracks": state.get("tracks", 0),
        "events_today": events_today,
        "alerts_today": alerts_today,
        "active_alerts": active_alerts,
        "fps": state.get("fps", 0),
        "detections": state.get("detections", []),
        "recent_events": [
            {
                "id": row[0],
                "person": row[1],
                "time": row[2],
                "confidence": row[3],
                "track_id": row[4]
            }
            for row in recent_rows
        ],
        "camera_running": bool(state.get("running")),
        "registered_people": len(database)
    }


@app.get("/api/notifications/test")
def test_notification(authorization: str | None = Header(default=None)):
    current_user(authorization)

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise HTTPException(
            status_code=400,
            detail="Telegram notification settings are not configured"
        )

    if not send_telegram_alert(0, 1.0):
        raise HTTPException(
            status_code=502,
            detail="Telegram notification failed. Check the backend console for the exact Telegram error."
        )

    return {"success": True, "message": "Test notification sent"}
