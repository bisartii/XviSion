import cv2
import pickle
import numpy as np
from insightface.app import FaceAnalysis

# Load model
app = FaceAnalysis(name="buffalo_l")
app.prepare(ctx_id=0, det_size=(640, 640))

# Load database
with open("face_database.pkl", "rb") as f:
    database = pickle.load(f)

# Read image
img = cv2.imread("test.jpg")

# Detect faces
faces = app.get(img)

for face in faces:

    embedding = face.embedding

    best_name = "Unknown"
    best_score = -1

    # Compare with database
    for name, db_embedding in database.items():

        score = np.dot(embedding, db_embedding) / (
            np.linalg.norm(embedding) *
            np.linalg.norm(db_embedding)
        )

        if score > best_score:
            best_score = score
            best_name = name

    # Threshold
    if best_score < 0.45:
        best_name = "Unknown"

    x1, y1, x2, y2 = map(int, face.bbox)

    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

    cv2.putText(
        img,
        f"{best_name} {best_score:.2f}",
        (x1, y1 - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )
scale = 0.5
img = cv2.resize(img, None, fx=scale, fy=scale)

# Show result
cv2.imshow("Face Recognition Test", img)
cv2.waitKey(0)
cv2.destroyAllWindows()