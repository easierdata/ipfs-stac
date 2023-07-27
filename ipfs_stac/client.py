import json
import fsspec
import requests
import pandas as pd
import io
from bs4 import BeautifulSoup
from pystac_client import Client
from array import array
from PIL import Image
import numpy as np

class web3():
    local_gateway = ""
    stac_endpoint = ""

    def __init__(self, local_gateway=None, stac_endpoint=None):
        """
        web3 client constructor

        :param str local_gateway: Local gateway endpoint, if left blank, will not force local gateway usage
        :param str stac_endpoint: STAC browser endpoint
        """
        self.local_gateway = local_gateway
        self.stac_endpoint = stac_endpoint
        self.forceLocalNode()

    def getFromCID(self, cid: str):
        """
        Retrieves raw data from CID

        :param str cid: CID to retrieve 
        """
        try:
            with fsspec.open(f"ipfs://{cid}", "r") as contents:
                data = contents.read()
                return data
        except Exception as e: 
            print(f"Error with CID retrieval: {e}")

    def getCSVDataframeFromCID(self, cid: str):
        """
        Parse CSV CID to pandas dataframe

        :param str cid: CID to retrieve 
        """
        try:
            data = self.getFromCID(cid)

            # Parse for contents endpoint
            soup = BeautifulSoup(data, 'html.parser')
            endpoint = f"{soup.find_all('a')[0].get('href').replace('.tech', '.io')}{soup.find_all('a')[-1].get('href')}"

            response = requests.get(endpoint)
            csv_data = io.StringIO(response.text)
            df = pd.read_csv(csv_data)

            return df
        except Exception as e: 
            print(f"Error with dataframe retrieval: {e}")

    def searchSTACByBox(self, bbox: array, collections: array):
        """
        Search STAC catalog by bounding box and return array of items

        :param bbox array: Array of coordinates for bounding box
        :param collections array: Array of collection names (strings)
        """
        catalog = Client.open(self.stac_endpoint)
        search = catalog.search(
            collections=collections,
            bbox=bbox,
        )

        all = search.item_collection()

        return all

    def searchSTACByBoxIndex(self, bbox: array, collections: array, index: int):
        """
        Search STAC catalog by bounding box and return singular item

        :param bbox array: Array of coordinates for bounding box
        :param collections array: Array of collection names (strings)
        :param index int: Index of item to return
        """
        catalog = Client.open(self.stac_endpoint)
        search = catalog.search(
            collections=collections,
            bbox=bbox,
        )

        all = search.item_collection()

        return all[index]

    def getAssetFromItem(self, item, asset: str):
        """
        Returns asset object from item

        :param item: STAC catalog item
        :param asset str: Name of asset to return
        """
        try:
            item_dict = item.to_dict()
            cid = item_dict["assets"][f"{asset}"]["alternate"]["IPFS"]["href"].split('/')[-1]
            
            return asset(str(cid), self.local_gateway)
        except Exception as e: 
            print(f"Error with getting asset: {e}")

    def getAssetsFromItem(self, item, assets):
        """
        Returns array of asset objects from item

        :param item: STAC catalog item
        :param asset array: Names of asset to return (strings)
        """
        try:
            assetArray = []

            for i in assets:
                assetArray.append(self.getAssetFromItem(item, i))

            return assetArray
        except Exception as e: 
            print(f"Error with getting assets: {e}")

    def writeCID(self, cid: str, filePath: str):
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

    def forceLocalNode(self):
        """
        Forces the use of local node through env file
        This function needs to be refactored slightly -> currently overwrites .env file which is unideal if user has other variables configured
        """
        if self.local_gateway == "": 
            with open('.env', 'w') as file:
                # Write new content to the file
                file.write('IPFSSPEC_GATEWAYS="http://127.0.0.1:8080,https://ipfs.io,https://gateway.pinata.cloud,https://cloudflare-ipfs.com",https://dweb.link"')
        else:
            with open('.env', 'w') as file:
                # Write new content to the file
                file.write(f'IPFSSPEC_GATEWAYS="{self.local_gateway}"')

    def uploadToIPFS(self, file_path) -> str:
        """
        Upload file to IPFS by local node

        :param str file_path: The absolute/relative path to file
        :rtype: str
        """
        files = {
            "file": open(file_path, "rb")
        }

        response = requests.post(f"{self.local_gateway}/api/v0/add", files=files)
        data = response.json()
        return data["Hash"] # CID

class asset():
    cid = ""
    local_gateway = ""

    def __init__(self, cid: str, local_gateway: str):
        """
        Constructor for asset object

        :param cid str: The CID associated with the object
        :param local_gateway str: Local gateway endpoint
        """
        self.cid = cid
        self.local_gateway = local_gateway

    # Return cid when printed
    def __str__(self):
        return self.cid
    
    # Returns asset bytes
    def fetch(self):
        try:
            print(f"Fetching {self.cid.split('/')[-1]}")

            with fsspec.open(f"ipfs://{self.cid}", "rb") as contents:
                file = contents.read()
            
            data = io.BytesIO(file)

            return data 
        except Exception as e: 
            print(f"Error with CID fetch: {e}")
    
    # Pin to local kubo node
    def pin(self):
        response = requests.post(f"{self.local_gateway}/api/v0/pin/add", headers={
            "Content-Type": "application/json"
        }, json={
            "arg": self.cid
        })

        if response.status_code == 200:
            print("Data pinned successfully")
        else:
            print("Error pinning data")

    # Returns asset as np array if image
    def fetchNPArray(self):
        try:
            print(f"Fetching {self.cid.split('/')[-1]}")

            with fsspec.open(f"ipfs://{self.cid}", "rb") as contents:
                file = contents.read()
            
            data = io.BytesIO(file)

            im = Image.open(data)

            return np.array(im)
        except Exception as e: 
            print(f"Error with CID fetch: {e}")