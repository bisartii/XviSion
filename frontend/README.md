# Terra Vision React UI

A runnable React/Vite implementation of the Terra Vision visual language:
dark spatial UI, liquid glass, live-monitor mockup, people registry, event history,
alerts, cameras, analytics, and system settings.

## Run

1. Install Node.js (LTS).
2. Open this folder in VS Code.
3. In the terminal:

   npm install
   npm run dev

4. Open the local URL printed by Vite.

## Current state

This is the UI layer only. It uses realistic mock data.

The next integration step is to connect:
- events.db -> Event History
- face_database.pkl -> People
- recognize.py / ByteTrack -> Live Monitor
- FastAPI/WebSocket -> real-time communication

The original Stitch export is included under `stitch-source/` for reference.
