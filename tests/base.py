from unittest import TestCase
import requests
import time
import subprocess
import os
import json
from pathlib import Path


# Default config properties and params. DO NOT MODIFY.
# These are the default values for the configuration file. Modify these values in the `config.json` file.
CONFIG_FILE_NAME = "config.json"
IPFS_GATEWAY_ADDR = "127.0.0.1"
IPFS_API_PORT = "5001"
IPFS_GATEWAY_PORT = "8080"
STAC_ENDPOINT = "https://stac.easierdata.info"

# Set default configuration dictionary
DEFAULT_CONFIG = {
    "ipfs_gateway_ip": IPFS_GATEWAY_ADDR,
    "ipfs_api_port": IPFS_API_PORT,
    "ipfs_gateway_port": IPFS_GATEWAY_PORT,
    "stac_endpoint": STAC_ENDPOINT,
}


def get_tests_dir():
    # Path.cwd()
    return Path(Path.cwd(), "tests").as_posix()


# Get the path to the test directory
TEST_DIR = get_tests_dir()
TEST_DATA_DIR = Path(TEST_DIR, "data")
# cwd = Path(os.getcwd())
# cwd = Path(cwd.parent, "tests")


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


def import_configuration():

    try:
        with open(Path(TEST_DIR, CONFIG_FILE_NAME), "r") as f:
            config = json.load(f)
        return config
    except FileNotFoundError as e:
        print(
            f"""
            Error: {e}
            
            Configuration file missing. Creating now with default settings.
            
            NOTE: You can modify the configuration settings by modifying config.json file found in {TEST_DIR}.
        """
        )
        config = DEFAULT_CONFIG
        save_config(config)
        return config


def save_config(config_dict):
    # create file if it does not exist
    Path.touch(Path(TEST_DIR, CONFIG_FILE_NAME), exist_ok=True)
    json.dump(config_dict, open(Path(TEST_DIR, CONFIG_FILE_NAME), "w"))


class SetUp(TestCase):
    TEXT_FILE_CID = "Qmf1rtki74jvYmGeqaaV51hzeiaa6DyWc98fzDiuPatzyy"
    IMAGE_FILE_CID = "bafybeihejpcpwovcfn74dkwhhhdidfug7cmfk5kdihjlmgzj6y7345mll4"
    TEXT_FILE_PATH = Path(TEST_DATA_DIR, "hello.txt")
    IMAGE_FILE_PATH = Path(TEST_DATA_DIR, "image.jpg")

    @classmethod
    def setUpClass(cls):
        # start_ipfs_if_needed()

        if any(
            not os.path.exists(path)
            for path in [cls.TEXT_FILE_PATH, cls.IMAGE_FILE_PATH]
        ):
            subprocess.run(
                ["python3", f"{Path(TEST_DATA_DIR, 'create_upload_data.py')}"]
            )
