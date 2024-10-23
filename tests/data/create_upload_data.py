from io import BytesIO
import subprocess
from pathlib import Path


def create_text_file():
    with open("hello.txt", "w") as f:
        f.write("Hello World!")
        subprocess.run(["ipfs", "add", "hello.txt"])


def create_image_file():
    # Create a 50x50 image
    img_path = Path("tests", "data", "image.png").as_posix()
    from PIL import Image

    with open(img_path, "wb") as f:
        image = Image.new("RGB", (50, 50))
        image_bytes = BytesIO()
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)
        f.write(image_bytes.read())
        subprocess.run(["ipfs", "add", img_path])
