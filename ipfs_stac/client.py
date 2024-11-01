# Standard Library Imports
import os
import json
from io import StringIO, BytesIO
from pathlib import Path
from typing import List
import warnings
from typing import Union
import subprocess
import atexit

# Third Party Imports
import fsspec
import requests
import pandas as pd
from bs4 import BeautifulSoup
from pystac_client import Client
from pystac import Collection, Item, ItemCollection
import numpy as np
import rasterio
from yaspin import yaspin
import psutil


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


def fetchCID(cid: str) -> bytes:
    """
    Fetches data from CID

    :param str cid: CID to retrieve
    """
    try:
        fs = fsspec.filesystem("ipfs")
        progress = 0

        with yaspin(
            text=f"Fetching {cid.split('/')[-1]} - {progress / 1048576:.2f}/{fs.size(f'ipfs://{cid}') / 1048576:.2f} MB",
            color=None,
        ) as spinner:
            with fs.open(f"ipfs://{cid}", "rb") as contents:
                file_data = bytearray()

                while True:
                    chunk = contents.read()
                    progress += len(chunk)
                    if not chunk:
                        break
                    spinner.text = f"Fetching {cid.split('/')[-1]} - {progress / 1048576:.2f}/{fs.size(f'ipfs://{cid}') / 1048576:.2f} MB"
                    file_data += chunk
            if file_data:
                spinner.ok("✅ ")
            else:
                spinner.fail("💥 ")

            return bytes(file_data)
    except FileNotFoundError as e:
        print(f"Could not file with CID: {cid}. Are you sure it exists?")
        raise e


class Web3:
    def __init__(
        self,
        local_gateway="localhost",
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
        self.daemon_status = None
        self.client: Client = Client.open(self.stac_endpoint)
        self.collections = self._get_collections_ids()
        self.config = None

        if api_port is None:
            raise ValueError("api_port must be set")

        if gateway_port is None:
            raise ValueError("gateway_port must be set")

        self.api_port = api_port
        self.gateway_port = gateway_port

        if self.local_gateway:
            self.startDaemon()

        # Add the env var if it doesn't exist or overwrite existing one.
        os.environ[ENV_VAR_NAME] = f"http://{self.local_gateway}:{self.gateway_port}"

        # Load configuration at instantiation
        # config_path = os.path.join(os.path.dirname(__file__), "config.json")
        # with open(config_path, "r") as f:
        #     self.config = json.load(f)

    def overwrite_config(self, path=None) -> None:
        """
        *only use if you know what you're doing*
        Overwrite configuration file with configuration in memory

        :param str path: Path to configuration file (optional)
        """

        # Get user's home directory
        home = os.path.expanduser("~")
        if path:
            config_path = path
        else:
            config_path = os.path.join(home, ".ipfs", "config")

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f)

    def _get_collections_ids(self) -> List[str]:
        """
        Get the collection ids from the stac endpoint
        """
        return [collection.id for collection in self.client.get_collections()]

    def get_collections(self) -> List["Collection"]:
        """
        Returns list of collections from STAC endpoint
        """
        return list(self.client.get_collections())

    def _is_process_running(self) -> bool:
        """Check if IPFS daemon process is running

        Returns:
            bool: True if process is running, False otherwise
        """
        process_name = "ipfs"
        for proc in psutil.process_iter(["name"]):
            try:
                if process_name.lower() in proc.info["name"].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def shutdown_process(self):
        """Shutdown the IPFS daemon process"""
        if self.daemon_status:
            print("Shutdown process is running...")

            self.daemon_status.terminate()
            self.daemon_status.wait(timeout=3)

            # If process is still running, kill it
            if self._is_process_running():
                self.daemon_status.kill()

            # If process is still running, exit with error
            elif self._is_process_running():
                import sys

                sys.exit("Failed to shutdown IPFS daemon")

            self.daemon_status = None

    def startDaemon(self):
        """Start the IPFS daemon process

        Raises:
            Exception: If the IPFS daemon fails to start
        """
        try:
            if not self._is_process_running():
                self.daemon_status = subprocess.Popen(["ipfs", "daemon"])
                atexit.register(self.shutdown_process)

            heartbeat_response = requests.post(
                f"http://{self.local_gateway}:{self.api_port}/api/v0/id",
                timeout=10,
            )
            if heartbeat_response.status_code != 200:
                warnings.warn(
                    "IPFS Daemon is running but still can't connect. Check your IPFS configuration."
                )
        except Exception as exc:
            print(f"Error starting IPFS daemon: {exc}")
            raise Exception("Failed to start IPFS daemon")

    def getFromCID(self, cid: str) -> bytes:
        """
        Retrieves raw data from CID

        :param str cid: CID to retrieve
        """
        try:
            return fetchCID(cid)
        except FileNotFoundError as e:
            print(f"Could not file with CID: {cid}. Are you sure it exists?")
            raise e

    def searchSTACByBox(
        self, bbox: List["str"], collections: List["str"]
    ) -> ItemCollection:
        """
        Search STAC catalog by bounding box and return array of items

        :param bbox array: Array of coordinates for bounding box
        :param collections array: Array of collection names
        """
        catalog = Client.open(self.stac_endpoint)
        search_results = catalog.search(
            collections=collections,
            bbox=bbox,
        )

        return search_results.item_collection()

    def searchSTAC(self, **kwargs) -> ItemCollection:
        """
        Search STAC catalog for items using the search method from pystac-client.

        Note: No request is sent to the API until a method is called to iterate
        through the resulting STAC Items, either :meth:`ItemSearch.item_collections`,
        :meth:`ItemSearch.items`, or :meth:`ItemSearch.items_as_dicts`.

        :param kwargs: Keyword arguments for the search method.
        :return: list of pystac.Item objects
        """
        try:
            search_results = self.client.search(**kwargs)
            return search_results.item_collection()

        except Exception as e:
            # Print the error message and the keyword argument that caused the error.
            if isinstance(e, TypeError):
                print(f"Error: {e}")
                print(f"Search method docstring: {self.client.search.__doc__}")
            else:
                print(f"Error: {e}")

    def searchSTACByBoxIndex(
        self, bbox: List["str"], collections: List["str"], index: int
    ) -> Item:
        """
        Search STAC catalog by bounding box and return singular item

        :param bbox array: Array of coordinates for bounding box
        :param collections array: Array of collection names
        :param index int: Index of item to return
        """
        catalog = Client.open(self.stac_endpoint)
        search_results = catalog.search(
            collections=collections,
            bbox=bbox,
        )

        return search_results.item_collection()[index]

    def getAssetNames(self, stac_obj: Union[Collection, Item] = None) -> List[str]:
        """
        Returns list of asset names from collection or item

        :param stac_obj: STAC collection or item
        """

        if stac_obj is None:
            raise ValueError("STAC Object (Collection or item) must be provided")

        if not isinstance(stac_obj, Collection) and not isinstance(stac_obj, Item):
            raise ValueError("STAC Object must be a Collection or Item")

        if type(stac_obj) is Collection:
            try:
                asset_names = set()
                items = stac_obj.get_all_items()

                for i in items:
                    names = list(i.get_assets().keys())
                    asset_names.update(names)

                return list(asset_names)
            except Exception as e:
                print(f"Error with getting asset names: {e}")
        elif type(stac_obj) is Item:
            try:
                return list(stac_obj.get_assets().keys())
            except Exception as e:
                print(f"Error with getting asset names: {e}")

    def getAssetFromItem(
        self, item: Item, asset_name: str, fetch_data=False
    ) -> "Asset":
        """Returns asset object from item

        Args:
            item (Item): STAC catalog item
            asset_name (str): Name of asset to return
            fetch_data (bool, optional): Fetch data from CID. Defaults to False.

        Returns:
            Asset: Asset object
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
    def uploadToIPFS(
        self,
        file_path: str = None,
        bytes_data: bytes = None,
        file_name: str = None,
        pin_content: bool = False,
        mfs_path: str = None,
        chunker: str = None,
    ) -> str:
        """
        Uploads a file or bytes data to IPFS.

        Args:
            file_path (str, optional): The path to the file to be uploaded. Defaults to None.
            bytes_data (bytes, optional): The bytes data to be uploaded. Defaults to None.
            file_name (str, optional): The name of the file. Defaults to None.
            pin_content (bool, optional): Pin locally to protect added files from garbage collection. Defaults to False.
            mfs_path (str, optional): Add reference to Files API (MFS) at the provided path. Defaults to None.
            chunker (str, optional): Chunking algorithm, size-[bytes], rabin-[min]-[avg]-[max] or buzhash. Defaults to None.

        Raises:
            ValueError: If neither `file_path` nor `bytes_data` is provided.
            ValueError: If `bytes_data` is not of type bytes.
            FileNotFoundError: If the file path provided does not exist.

        Returns:
            str: The CID (Content Identifier) of the uploaded content.
        """

        # Setting param options
        param_options = f"cid-version=1&pin={pin_content}"
        if mfs_path is not None:
            param_options = f"{param_options}&to-files={mfs_path}"
        if chunker is not None:
            param_options = f"{param_options}&chunker={chunker}"

        # Define empty payload dictionary
        components = {"content": None, "name": None}

        # Check if user provided a file path or bytes data
        if bytes_data is not None:
            if isinstance(bytes_data, bytes):
                components["content"] = bytes_data
            else:
                raise ValueError(
                    f"{type(bytes_data)} is not a valid type. `bytes_data` must be of type bytes."
                )
        elif file_path is not None:
            if Path(file_path).exists():
                with open(file_path, "rb") as f:
                    components["content"] = f.read()
            else:
                raise FileNotFoundError(
                    f"The file path provided does not exist. Please check {file_path}"
                )
        else:
            raise ValueError("Either file_path or bytes_data must be provided.")

        # Check if user provided a filename
        if file_name:
            components["name"] = file_name
        elif file_path:
            components["name"] = Path(file_path).name

        # put the components together as a file payload
        if components["name"] is not None:
            file_payload = {"file": (components["name"], components["content"])}
        else:
            file_payload = {"file": components["content"]}

        try:
            response = requests.post(
                f"http://{self.local_gateway}:{self.api_port}/api/v0/add?{param_options}",
                files=file_payload,
                timeout=10,
            )
            response.raise_for_status()  # Raise an exception for HTTP errors

            data = response.json()
            return data["Hash"]  # CID

        except requests.exceptions.Timeout:
            print("The request timed out")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")

    def pinned_list(
        self, pin_type: str = "recursive", names: bool = False
    ) -> List[str]:
        """Fetch pinned CIDs from local node

        Args:
            pin_type (str, optional): The type of pinned keys to list. Can be "direct", "indirect", "recursive", or "all". Defaults to "recursive".
            names (bool, optional): Include pin names in the output. Defaults to False.

        Returns:
            List[str]: List of pinned CIDs. If `names` is True, returns list of json objects.
        """
        # Setting param options
        param_options = f"type={pin_type}&names={names}"
        response = requests.post(
            f"http://{self.local_gateway}:{self.api_port}/api/v0/pin/ls?{param_options}",
            timeout=10,
        )

        if response.status_code == 200:
            if response.json() != {}:
                if names:
                    return list(response.json())
                else:
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

            response = requests.get(endpoint, timeout=10)
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
            self.fetch()

    def __str__(self) -> str:
        return self.cid

    def _is_pinned_to_local_node(self) -> bool:
        """
        Check if CID is pinned to local node
        """
        resp = requests.post(
            f"http://{self.local_gateway}:{self.api_port}/api/v0/pin/ls?arg=/ipfs/{self.cid}",
            timeout=10,
        )
        if (resp.json().get("Keys")) and self.cid in resp.json()["Keys"]:
            self.is_pinned = True
            return True
        elif resp.json()["Type"] == "error":
            return False
        else:
            print("Error checking if CID is pinned")
            print(resp.json())
            return False

    def fetch(self) -> None:
        try:
            self.data = fetchCID(self.cid)
        except Exception as e:
            print(f"Error with CID fetch: {e}")

    # Pin to local kubo node
    # @ensure_data_fetched
    def pin(self) -> str:
        self._is_pinned_to_local_node()
        if self.is_pinned:
            print("Content is already pinned")
        else:
            response = requests.post(
                f"http://{self.local_gateway}:{self.api_port}/api/v0/pin/add?arg={self.cid}",
                timeout=10,
            )

            if response.status_code == 200:
                print("Data pinned successfully")
                self.is_pinned = True

            else:
                print("Error pinning data")

    # Returns asset as np array if image
    @ensure_data_fetched
    def to_np_ndarray(self, dtype: np.dtype = np.float32) -> np.ndarray:
        with rasterio.open(BytesIO(self.data)) as dataset:
            return dataset.read(1).astype(dtype)
