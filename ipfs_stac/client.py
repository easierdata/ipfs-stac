import json
import fsspec
import requests
import pandas as pd
import io
from bs4 import BeautifulSoup
from pystac_client import Client
from array import array

class web3():
    local_gateway = ""
    stac = ""

    def __init__(self, local_gateway=None, stac=None):
        self.local_gateway = local_gateway
        self.stac = stac
        self.forceLocalNode()

    # Function to retrieve raw text from CIDs
    def getFromCID(self, cid: str):
        try:
            with fsspec.open(f"ipfs://{cid}", "r") as contents:
                data = contents.read()
                return data
        except Exception as e: 
            print(f"Error with CID retrieval: {e}")

    # Function to parse CID to pandas dataframe
    def getCSVDataframeFromCID(self, cid: str):
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

    # Search catalog by bounding box
    def searchSTACByBox(self, bbox: array, collections: array, index: int):
        catalog = Client.open(self.stac)
        search = catalog.search(
            collections=collections,
            bbox=bbox,
        )

        all = search.item_collection()

        return all[index]

    def getBandFromItem(self, item, band: str):
        try:
            item_dict = item.to_dict()
            cid = item_dict["assets"][f"{band}"]["alternate"]["IPFS"]["href"].split('/')[-1]
            
            return band_Obj(str(cid), self.local_gateway)
        except Exception as e: 
            print(f"Error with getting band: {e}")

    def getBandsFromItem(self, item, bands):
        try:
            bandsArray = []

            for band in bands:
                bandsArray.append(self.getBandFromItem(item, band))

            return bandsArray
        except Exception as e: 
            print(f"Error with getting band: {e}")

    # Write contents from CID to local disk - needs fixing
    def writeCID(self, cid: str, filePath: str):
        try:
            with fsspec.open(f"ipfs://{cid}", "rb") as contents:
                # Write data to local file path
                with open(filePath, "wb") as copy:
                    copy.write(contents.read())
        except Exception as e: 
            print(f"Error with CID write: {e}")

    # This function needs to be refactored slightly -> currently overwrites .env file which is unideal if user has other variables configured
    def forceLocalNode(self):
        if self.local_gateway == "": 
            with open('.env', 'w') as file:
                # Write new content to the file
                file.write('IPFSSPEC_GATEWAYS="http://127.0.0.1:8080,https://ipfs.io,https://gateway.pinata.cloud,https://cloudflare-ipfs.com",https://dweb.link"')
        else:
            with open('.env', 'w') as file:
                # Write new content to the file
                file.write(f'IPFSSPEC_GATEWAYS="{self.local_gateway}"')

class band_Obj():
    cid = ""
    local_gateway = ""

    def __init__(self, cid: str, local_gateway: str):
        self.cid = cid
        self.local_gateway = local_gateway

    # Return cid when printed
    def __str__(self):
        return self.cid
    
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