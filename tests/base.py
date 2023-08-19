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
    TEST_FILE = "tests/data/hello.txt"

    @classmethod
    def setUpClass(cls):
        start_ipfs_if_needed()

        # Check if the CID exists in the pinned objects
        result = subprocess.run(f"ipfs pin ls | grep {cls.TEST_CID}", shell=True)

        # If CID is not found, add the test file
        if result.returncode != 0:
            try:
                subprocess.run(["ipfs", "add", cls.TEST_FILE], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to add test file: {e}")
                raise Exception("Setup failed")
