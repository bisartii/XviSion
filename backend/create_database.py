import os
import cv2
import pickle
import numpy as np
from insightface.app import FaceAnalysis

app = FaceAnalysis(name="buffalo_l")
app.prepare(ctx_id=0, det_size=(640, 640))

database = {}
dataset = "dataset"

for person in os.listdir(dataset):

    folder = os.path.join(dataset, person)
    embeddings = []

    for file in os.listdir(folder):

        path = os.path.join(folder, file)
        img = cv2.imread(path)

        if img is None:
            continue

        faces = app.get(img)

        if len(faces) == 0:
            print(f"No face: {file}")
            continue

        # Select largest face
        face = max(
            faces,
            key=lambda f: (f.bbox[2] - f.bbox[0]) *
                          (f.bbox[3] - f.bbox[1])
        )

        embeddings.append(face.embedding)

    if embeddings:
        database[person] = np.mean(embeddings, axis=0)
        print(f"{person}: {len(embeddings)} faces processed")

with open("face_database.pkl", "wb") as f:
    pickle.dump(database, f)

print("\nDatabase created successfully!")
print("People:", list(database.keys()))