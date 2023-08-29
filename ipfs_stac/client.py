# Standard Library Imports
from io import BytesIO, StringIO
import os
import subprocess
import time
from typing import List

# Third Party Imports
import fsspec
import requests
import pandas as pd
from bs4 import BeautifulSoup
from pystac_client import Client
from pystac import Item
import numpy as np
import rasterio


def ensure_data_fetched(func):
    def wrapper(self, *args, **kwargs):
        if self.data is None:
            print("Data for asset has not been fetched yet. Fetching now...")
            self.fetch()
        return func(self, *args, **kwargs)
    return wrapper

class Web3:
    def __init__(self, local_gateway=None, api_port=5001, stac_endpoint=None, remote_gateways=None) -> None:
        """
        web3 client constructor

        :param str local_gateway: Local gateway endpoint without port.
        :param str stac_endpoint: STAC browser endpoint
        """
        self.local_gateway = local_gateway
        self.stac_endpoint = stac_endpoint

        if api_port is None:
            raise ValueError("api_port must be set")
        self.api_port = api_port

        if self.local_gateway:
            self.startDaemon()

        # Remote_gateways is of type List[str]
        if remote_gateways:
            os.environ["IPFSSPEC_GATEWAYS"] = f'IPFSSPEC_GATEWAYS="http://{self.local_gateway}:{self.api_port},https://ipfs.io,https://gateway.pinata.cloud,https://cloudflare-ipfs.com,https://dweb.link",{remote_gateways.join(",")}'
        
        # self.forceLocalNode() #TODO Try to use environment variables instead of writing to .env file
        # os.environ["IPFSSPEC_GATEWAYS"] = """

    def forceLocalNode(self) -> None:
        """
        Forces the use of local node through env file
        This function needs to be refactored slightly -> currently overwrites .env file which is unideal if user has other variables configured
        """
        if self.local_gateway is None:
            os.environ["IPFSSPEC_GATEWAYS"] = f'IPFSSPEC_GATEWAYS="http://{self.local_gateway}:{self.api_port},https://ipfs.io,https://gateway.pinata.cloud,https://cloudflare-ipfs.com,https://dweb.link"'
        else:
            os.environ["IPFSSPEC_GATEWAYS"] = f'IPFSSPEC_GATEWAYS="{self.local_gateway}"'

    #TODO: Use this function to try to start the daemon in the background if the user provides a local gateway and it is not running.
    # If the daemon is already running, this function will not do anything. If we cannot access the IPFS node even after trying to start it,
    # we should log a warning and continue with an external gateway.
    def startDaemon(self) -> None: 
        """
        Starts Kubo CLI Daemon
        """
        try:
            requests.get(f"http://{self.local_gateway}:{self.api_port}/")
        except requests.exceptions.ConnectionError:
            subprocess.Popen(["ipfs", "daemon"])

            time.sleep(5)

            try:
                requests.get(f"http://{self.local_gateway}:{self.api_port}/")
            except requests.exceptions.ConnectionError:
                raise Exception("Failed to start IPFS daemon")

    def getFromCID(self, cid: str) -> str:
        """
        Retrieves raw data from CID

        :param str cid: CID to retrieve
        """
        try:
            with fsspec.open(f"ipfs://{cid}", "r") as contents:
                data = contents.read()
                return data
        except FileNotFoundError as e:
            print(f"Could not file with CID: {cid}. Are you sure it exists?")
            raise e

    def searchSTACByBox(self, bbox: List["str"], collections: List["str"]): #TODO add return type
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

    def searchSTACByBoxIndex(self, bbox: List["str"], collections: List["str"], index: int):
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

    def getAssetFromItem(self, item: Item, asset_name: str, fetch_data=True) -> 'Asset':
        """
        Returns asset object from item

        :param item: STAC catalog item
        """
        try:
            item_dict = item.to_dict()
            cid = item_dict["assets"][f"{asset_name}"]["alternate"]["IPFS"]["href"].split(
                "/"
            )[-1]
            return Asset(cid, self.local_gateway, self.api_port, fetch_data=fetch_data)
        except Exception as e:
            print(f"Error with getting asset: {e}")

    def getAssetsFromItem(self, item: Item, assets: List[str]) -> List['Asset']:
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
    def uploadToIPFS(self, file_path: str) -> str:
        """
        Upload file to IPFS by local node

        :param str file_path: The absolute/relative path to file
        """
        files = {"file": open(file_path, "rb")}
        response = requests.post(f"http://{self.local_gateway}:{self.api_port}/api/v0/add", files=files)
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
    def __init__(self, cid: str, local_gateway: str, api_port, fetch_data=True) -> None:
        """
        Constructor for asset object

        :param cid str: The CID associated with the object
        :param local_gateway str: Local gateway endpoint
        """
        self.cid = cid
        self.local_gateway = local_gateway
        self.api_port = api_port
        self.data = None
        if fetch_data:
            self.fetch()

    def __str__(self) -> str:
        return self.cid

    def fetch(self) -> None:
        try:
            print(f"Fetching {self.cid.split('/')[-1]}")

            with fsspec.open(f"ipfs://{self.cid}", "rb") as contents:
                file = contents.read()
            self.data = BytesIO(file)

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
            
        else:
            print("Error pinning data")

    # Returns asset as np array if image
    @ensure_data_fetched
    def to_np_ndarray(self, dtype: np.dtype = np.float32) -> np.ndarray:
        with rasterio.open(self.data) as dataset:
            return dataset.read(1).astype(dtype)
        

