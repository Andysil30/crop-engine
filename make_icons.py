from PIL import Image, ImageDraw
import os

os.makedirs("frontend/icons", exist_ok=True)

for s in (192, 512):
    img = Image.new("RGB", (s, s), "#2e7d32")
    d = ImageDraw.Draw(img)
    d.line([(s * 0.5, s * 0.8), (s * 0.5, s * 0.45)], fill="white", width=int(s * 0.04))
    d.ellipse([s * 0.22, s * 0.25, s * 0.5, s * 0.5], fill="white")    # left leaf
    d.ellipse([s * 0.5, s * 0.18, s * 0.78, s * 0.43], fill="white")   # right leaf
    img.save(f"frontend/icons/icon-{s}.png")

print("Icons saved in frontend/icons")