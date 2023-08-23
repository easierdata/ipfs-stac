from PIL import Image
from io import BytesIO
import subprocess

def create_text_file():
    with open("hello.txt", "w") as f:
        f.write("Hello World!")
        subprocess.run(["ipfs", "add", "hello.txt"])


def create_image_file():
    # Create a 50x50 image
    with open("tests/data/image.png", "wb") as f:
        image = Image.new("RGB", (50, 50))
        image_bytes = BytesIO()
        image.save(image_bytes, format='PNG')
        image_bytes.seek(0)
        f.write(image_bytes.read())
        subprocess.run(["ipfs", "add", "tests/data/image.png"])
