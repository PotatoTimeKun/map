from PIL import Image
import os

for parent, dirs, files in os.walk("./images"):
  for f in files:
    path = os.path.join(parent,f)
    img = Image.open(path)
    resized = img.resize((128, 128), Image.NEAREST)  # ★補間なし
    resized.save(path)
