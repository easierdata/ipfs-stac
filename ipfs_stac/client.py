# Standard Library Imports
from io import BytesIO, StringIO
import os
import subprocess
import time
from typing import List
import warnings

# Third Party Imports
import fsspec
import requests
import pandas as pd
from bs4 import BeautifulSoup
from pystac_client import Client
from pystac import Item
import numpy as np
import rasterio
from yaspin import yaspin


# Global Variables
ENV_VAR_NAME = "IPFS_GATEWAY"
REMOTE_GATEWAYS = [
    "https://ipfs.io",
    "https://cloudflare-ipfs.com",
    "https://dweb.link",
]


def ensure_data_fetched(func):
    def wrapper(self, *args, **kwargs):
        if self.data is None:
            print("Data for asset has not been fetched yet. Fetching now...")
            self.fetch()
        return func(self, *args, **kwargs)

    return wrapper


class Web3:
    def __init__(
        self,
        local_gateway="127.0.0.1",
        api_port=5001,
        gateway_port=8080,
        stac_endpoint=None,
    ) -> None:
        """
        web3 client constructor

        :param str local_gateway: Local gateway endpoint without port.
        :param str stac_endpoint: STAC browser endpoint
        """
        self.local_gateway = local_gateway
        self.stac_endpoint = stac_endpoint
        self._process = None

        if api_port is None:
            raise ValueError("api_port must be set")

        if gateway_port is None:
            raise ValueError("gateway_port must be set")

        self.api_port = api_port
        self.gateway_port = gateway_port

        if self.local_gateway:
            self.startDaemon()

        # Check if the remote gateway env variable already exists
        if ENV_VAR_NAME in os.environ:
            os.environ[ENV_VAR_NAME] += (
                os.pathsep + f"http://{self.local_gateway}:{self.gateway_port}"
            )
        else:
            os.environ[ENV_VAR_NAME] = (
                f"http://{self.local_gateway}:{self.gateway_port}"
            )

    def startDaemon(self) -> None:
        """
        Starts Kubo CLI Daemon if not already running
        """

        def is_process_running(process_name):
            import psutil

            # Iterate over all running processes
            for proc in psutil.process_iter(["name"]):
                try:
                    # Check if process name contains the given name string.
                    if process_name.lower() in proc.info["name"].lower():
                        return True
                except ( psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            return False

        def shutdown_process():
            if self._process:
                self._process.terminate()  # or self._process.kill() if terminate is not enough
                self._process = None

        try:
            # Check if 'ipfs daemon' is already running
            if not is_process_running("ipfs"):
                import subprocess
                import atexit

                self._process = subprocess.Popen(["ipfs", "daemon"])
                atexit.register(shutdown_process)  # Register the shutdown function

            heartbeat_response = requests.post(
                f"http://{self.local_gateway}:{self.api_port}/api/v0/id"
            )
            if heartbeat_response.status_code != 200:
                warnings.warn(
                    "IPFS Daemon is running but still can't connect. Check your IPFS configuration."
                )
        except requests.exceptions.ConnectionError:
            raise Exception("Failed to start IPFS daemon")

    def getFromCID(self, cid: str) -> bytes:
        """
        Retrieves raw data from CID

        :param str cid: CID to retrieve
        """
        try:
            fs = fsspec.filesystem("ipfs")
            progress = 0

            with yaspin(
                text=f"Fetching {cid.split('/')[-1]} - {progress}/{fs.size(f'ipfs://{cid}')} bytes",
                color="yellow",
            ) as spinner:
                with fsspec.open(f"ipfs://{cid}", "rb") as contents:
                    file_data = bytearray()

                    while True:
                        chunk = contents.read()
                        progress += len(chunk)
                        if not chunk:
                            break
                        file_data.extend(chunk)
                        spinner.text = f"Fetching {cid.split('/')[-1]} - {progress}/{fs.size(f'ipfs://{cid}')} bytes"
                    # file = contents.read()

                if file_data:
                    spinner.ok("✅ ")
                else:
                    spinner.fail("💥 ")
                
                return bytes(file_data)
            # with fsspec.open(f"ipfs://{cid}", "rb") as contents:
            #     data = contents.read()
            #     return data
        except FileNotFoundError as e:
            print(f"Could not file with CID: {cid}. Are you sure it exists?")
            raise e

    def searchSTACByBox(
        self, bbox: List["str"], collections: List["str"]
    ):  # TODO add return type
        """
        Search STAC catalog by bounding box and return array of items

        :param bbox array: Array of coordinates for bounding box
        :param collections array: Array of collection names
        """
        catalog = Client.open(self.stac_endpoint)
        search = catalog.search(
            collections=collections,
            bbox=bbox,
        )

        all = search.item_collection()

        return all

    def searchSTACByBoxIndex(
        self, bbox: List["str"], collections: List["str"], index: int
    ):
        """
        Search STAC catalog by bounding box and return singular item

        :param bbox array: Array of coordinates for bounding box
        :param collections array: Array of collection names
        :param index int: Index of item to return
        """
        catalog = Client.open(self.stac_endpoint)
        search = catalog.search(
            collections=collections,
            bbox=bbox,
        )

        all = search.item_collection()

        return all[index]

    def getAssetFromItem(
        self, item: Item, asset_name: str, fetch_data=False
    ) -> "Asset":
        """
        Returns asset object from item

        :param item: STAC catalog item
        """
        try:
            item_dict = item.to_dict()
            cid = item_dict["assets"][f"{asset_name}"]["alternate"]["IPFS"][
                "href"
            ].split("/")[-1]
            return Asset(cid, self.local_gateway, self.api_port, fetch_data=fetch_data)
        except Exception as e:
            print(f"Error with getting asset: {e}")

    def getAssetsFromItem(self, item: Item, assets: List[str]) -> List["Asset"]:
        """
        Returns array of asset objects from item

        :param item: STAC catalog item
        :param asset array: Names of asset to return (strings)
        """
        try:
            assetArray = []

            for i in assets:
                assetArray.append(self.getAssetFromItem(item, i, fetch_data=False))

            return assetArray
        except Exception as e:
            print(f"Error with getting assets: {e}")

    def writeCID(self, cid: str, filePath: str) -> None:
        """
        Write CID contents to local file system (WIP)

        :param CID str: CID to retrieve
        :param filePath str: Directory to write contents to
        """
        try:
            with fsspec.open(f"ipfs://{cid}", "rb") as contents:
                # Write data to local file path
                with open(filePath, "wb") as copy:
                    copy.write(contents.read())
        except Exception as e:
            print(f"Error with CID write: {e}")

    # Use overrideDefault decorator to force local gateway usage
    def uploadToIPFS(self, file_path: str = None, bytes_data=None) -> str:
        """
        Upload file to IPFS by local node

        :param str file_path: The absolute/relative path to file
        :param bytes bytes_data: The bytes data to upload
        """
        if file_path:
            files = {"file": open(file_path, "rb")}
            response = requests.post(
                f"http://{self.local_gateway}:{self.api_port}/api/v0/add", files=files
            )
        elif bytes_data:
            files = {"file": ("file", bytes_data)}
            response = requests.post(
                f"http://{self.local_gateway}:{self.api_port}/api/v0/add", files=files
            )
        else:
            raise ValueError("Either file_path or bytes_data must be provided.")

        data = response.json()
        return data["Hash"]  # CID

    def pinned_list(self) -> List[str]:
        """
        Returns array of pinned CIDs
        """

        response = requests.post(
            f"http://{self.local_gateway}:{self.api_port}/api/v0/pin/ls",
        )

        if response.status_code == 200:
            if response.json() != {}:
                return list(response.json()["Keys"].keys())
            else:
                return []
        else:
            print("Error fetching pinned CIDs")

    def getCSVDataframeFromCID(self, cid: str) -> pd.DataFrame:
        """
        Parse CSV CID to pandas dataframe

        :param str cid: CID to retrieve
        """
        try:
            data = self.getFromCID(cid)

            # Parse for contents endpoint
            soup = BeautifulSoup(data, "html.parser")
            endpoint = f"{soup.find_all('a')[0].get('href').replace('.tech', '.io')}{soup.find_all('a')[-1].get('href')}"

            response = requests.get(endpoint)
            csv_data = StringIO(response.text)
            df = pd.read_csv(csv_data)

            return df
        except Exception as e:
            print(f"Error with dataframe retrieval: {e}")


class Asset:
    def __init__(
        self, cid: str, local_gateway: str, api_port, fetch_data=False
    ) -> None:
        """
        Constructor for asset object

        :param cid str: The CID associated with the object
        :param local_gateway str: Local gateway endpoint
        """
        self.cid = cid
        self.local_gateway = local_gateway
        self.api_port = api_port
        self.data: bytes = None
        self.is_pinned = False
        if fetch_data:
            if not self._is_pinned_to_local_node():
                self.fetch()

    def __str__(self) -> str:
        return self.cid

    def _is_pinned_to_local_node(self) -> bool:
        """
        Check if CID is pinned to local node
        """
        resp = requests.post(
            f"http://{self.local_gateway}:{self.api_port}/api/v0/pin/ls?arg=/ipfs/{self.cid}",
        )
        if (resp.json().get("Keys")) and self.cid in resp.json()["Keys"]:
            self.is_pinned = True
            return True
        elif resp.json()["Type"] == "error":
            self.is_pinned = False
            return False
        else:
            print("Error checking if CID is pinned")
            print(resp.json())
            self.is_pinned = False
            return False

    def fetch(self) -> None:
        try:
            fs = fsspec.filesystem("ipfs")
            progress = 0

            with yaspin(
                text=f"Fetching {self.cid.split('/')[-1]} - {progress}/{fs.size(f'ipfs://{self.cid}')} bytes",
                color="yellow",
            ) as spinner:
                with fsspec.open(f"ipfs://{self.cid}", "rb") as contents:
                    file_data = bytearray()

                    while True:
                        chunk = contents.read()
                        progress += len(chunk)
                        if not chunk:
                            break
                        file_data.extend(chunk)
                        spinner.text = f"Fetching {self.cid.split('/')[-1]} - {progress}/{fs.size(f'ipfs://{self.cid}')} bytes"
                    # file = contents.read()

                self.data = bytes(file_data)
                if self.data:
                    spinner.ok("✅ ")
                else:
                    spinner.fail("💥 ")
        except Exception as e:
            print(f"Error with CID fetch: {e}")

    # Pin to local kubo node
    @ensure_data_fetched
    def pin(self) -> str:
        response = requests.post(
            f"http://{self.local_gateway}:{self.api_port}/api/v0/pin/add?arg={self.cid}",
        )

        if response.status_code == 200:
            print("Data pinned successfully")
            self.is_pinned = True

        else:
            print("Error pinning data")
            self.is_pinned = False

    # Returns asset as np array if image
    @ensure_data_fetched
    def to_np_ndarray(self, dtype: np.dtype = np.float32) -> np.ndarray:
        with rasterio.open(self.data) as dataset:
            return dataset.read(1).astype(dtype)
