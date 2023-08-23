from unittest import TestCase
import requests
import time
import subprocess
import os

def start_ipfs_if_needed():
    try:
        requests.get("http://127.0.0.1:5001/")
    except requests.exceptions.ConnectionError:
        subprocess.Popen(["ipfs", "daemon"])

        time.sleep(5)

        try:
            requests.get("http://127.0.0.1:5001/")
        except requests.exceptions.ConnectionError:
            raise Exception("Failed to start IPFS daemon")


class SetUp(TestCase):
    TEXT_FILE_CID = "Qmf1rtki74jvYmGeqaaV51hzeiaa6DyWc98fzDiuPatzyy"
    IMAGE_FILE_CID = "QmQeQAWNJ6WXuPp3hms9qNSX5uQiSNSybYfRUqEe9PinL9"
    TEXT_FILE_PATH = "tests/data/hello.txt"
    IMAGE_FILE_PATH = "tests/data/image.jpg"

    @classmethod
    def setUpClass(cls):
        start_ipfs_if_needed()

        if any(not os.path.exists(path) for path in [cls.TEXT_FILE_PATH, cls.IMAGE_FILE_PATH]):
            subprocess.run(["python3", "tests/data/create_upload_data.py"])
            
            
