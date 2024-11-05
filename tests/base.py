from typing import Dict, Union
from unittest import TestCase
import requests
import subprocess
import json
import warnings
from pathlib import Path


# Default config properties and params. DO NOT MODIFY.
# These are the default values for the configuration file. Modify these values in the `config.json` file.
CONFIG_FILE_NAME = "config.json"
# IPFS_GATEWAY_ADDR = "127.0.0.1"
# IPFS_API_PORT = 5001
# IPFS_GATEWAY_PORT = 8080
# STAC_ENDPOINT = "https://stac.easierdata.info"

# Set default configuration dictionary
DEFAULT_CONFIG = {
    "ipfs_gateway_ip": "127.0.0.1",
    "ipfs_api_port": 5001,
    "ipfs_gateway_port": 8080,
    "stac_endpoint": "https://stac.easierdata.info",
}


def get_tests_dir() -> str:
    # Path.cwd()
    return Path(Path.cwd(), "tests").as_posix()


# Get the path to the test directory
TEST_DIR = get_tests_dir()
TEST_DATA_DIR = Path(TEST_DIR, "data")
# cwd = Path(os.getcwd())
# cwd = Path(cwd.parent, "tests")


def start_ipfs_if_needed() -> Union[subprocess.Popen[bytes], None]:
    config = import_configuration()
    try:
        heartbeat_response = requests.post(
            f'http://{config["ipfs_gateway_ip"]}:{config["ipfs_api_port"]}/api/v0/id',
            timeout=10,
        )

        if heartbeat_response.status_code != 200:
            warnings.warn(
                "IPFS Daemon is running but still can't connect. Check your IPFS configuration."
            )
    except requests.exceptions.ConnectionError:
        print("IPFS Daemon is not running. Starting IPFS Daemon via the CLI.")
        # time.sleep(2)
        return subprocess.Popen(["ipfs", "daemon"])

    except Exception as exc:
        print(f"Error starting IPFS daemon: {exc}")
        raise Exception("Failed to start IPFS daemon")


def import_configuration() -> Dict[str, Union[str, int]]:
    """
    Import configuration settings from the config.json file.
    If the file does not exist, create it with default settings.
    """

    try:
        with Path.open(Path(TEST_DIR, CONFIG_FILE_NAME), "r", encoding="utf-8") as f:
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


def save_config(config_dict: Dict) -> None:
    # create file if it does not exist
    Path.touch(Path(TEST_DIR, CONFIG_FILE_NAME), exist_ok=True)
    json.dump(config_dict, Path.open(Path(TEST_DIR, CONFIG_FILE_NAME), "w"))


class SetUp(TestCase):
    TEXT_FILE_CID = "bafkreid7qoywk77r7rj3slobqfekdvs57qwuwh5d2z3sqsw52iabe3mqne"
    IMAGE_FILE_CID = "bafkreidrnczwqiniksp663cpixwajboci2bgjdgsyswlonftkdy2ygtf5m"
    TEXT_FILE_PATH = Path(TEST_DATA_DIR, "hello.txt")
    IMAGE_FILE_PATH = Path(TEST_DATA_DIR, "image.jpg")

    @classmethod
    def setUpClass(cls):

        if any(
            not Path.exists(path) for path in [cls.TEXT_FILE_PATH, cls.IMAGE_FILE_PATH]
        ):
            subprocess.run(
                ["python3", f"{Path(TEST_DATA_DIR, 'create_upload_data.py')}"]
            )
