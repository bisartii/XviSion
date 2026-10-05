import cv2
import pickle
import os
from insightface.app import FaceAnalysis

# Load model
app = FaceAnalysis(name="buffalo_l")
app.prepare(ctx_id=0, det_size=(320, 320))

# Load existing database
if os.path.exists("face_database.pkl"):
    with open("face_database.pkl", "rb") as f:
        database = pickle.load(f)
else:
    database = {}

name = input("Enter person's name: ").strip()

if not name:
    print("Name cannot be empty!")
    exit()

print("\nWebcam starting...")
print("Look at the camera and move your face slightly.")
print("Press SPACE to capture.")
print("Press Q to quit.\n")

cap = cv2.VideoCapture(0)

embeddings = []

while True:

    ret, frame = cap.read()

    if not ret:
        break

    faces = app.get(frame)

    for face in faces:
        x1, y1, x2, y2 = map(int, face.bbox)

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"{len(embeddings)}/30",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

    cv2.imshow("Face Registration", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord(" "):

        if len(faces) == 1:

            embeddings.append(faces[0].embedding)

            print(f"Captured {len(embeddings)}/30")

        else:
            print("Make sure exactly ONE face is visible.")

    if key == ord("q"):
        break

    if len(embeddings) >= 30:
        break

cap.release()
cv2.destroyAllWindows()

# Save
if embeddings:
    database[name] = embeddings

    with open("face_database.pkl", "wb") as f:
        pickle.dump(database, f)

    print("\nRegistration successful!")
    print("Person:", name)
    print("Embeddings:", len(embeddings))
    print("People:", list(database.keys()))

else:
    print("\nNo embeddings captured.")