from unittest import TestCase
import requests
import time
import subprocess


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
    TEST_CID = "Qmf1rtki74jvYmGeqaaV51hzeiaa6DyWc98fzDiuPatzyy"
    TEST_FILE = "./data/hello.txt"

    @classmethod
    def setUpClass(cls):
        start_ipfs_if_needed()

        try:
            subprocess.run(["ipfs", "block", "stat", cls.TEST_CID], check=True)
        except subprocess.CalledProcessError:
            try:
                subprocess.run(["ipfs", "add", cls.TEST_FILE], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to add test file: {e}")
                raise Exception("Setup failed")
