from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import pickle
import os

app = FastAPI(title="Terra Vision API")

# Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DATABASE_FILE = "face_database.pkl"
EVENTS_DB = "events.db"


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


@app.get("/api/people")
def people():

    if not os.path.exists(DATABASE_FILE):
        return []

    with open(DATABASE_FILE, "rb") as f:
        database = pickle.load(f)

    result = []

    for name, embeddings in database.items():
        result.append({
            "name": name,
            "embeddings": len(embeddings)
        })

    return result


@app.get("/api/events")
def events():

    if not os.path.exists(EVENTS_DB):
        return []

    conn = sqlite3.connect(EVENTS_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, person, time, confidence, track_id
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