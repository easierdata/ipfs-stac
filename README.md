# The EASIER Data Initiative's Python Client

### Features

* Simple CID Data Retrieval
* CID CSV To Dataframe Object
* Querying EASIER STAC API by Bounding Box
  * Single Band Retrieval
  * Multi Band Retrieval

### Installation

The client can be installed through pip

```bash
$ pip install ipfs-stac
```

### Language Support

The client currently supports Python versions 3+

## Usage

### Create a client object

```python
from ipfs_stac import client

# Create a new client object
easier = client.web3(local_gateway="", stac_endpoint="")

# If you want to force using a local node, specify the endpoint in the local_gateway argument
easier = client.web3(local_gateway="http://127.0.0.1:8000", stac_endpoint="")
```

### Fetch a CID from IPFS

```python
# Simple hello world example
data = easier.getFromCID("QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx")
print(data)

"""
hello worlds
"""
```

### Get CID CSV Data to Pandas Dataframe

```python
df = easier.getCSVDataframeFromCID("bafybeifw6kcodgxnamtuvhkxgaf4ep2rwscjae3gnzxb3zj5c6zyea2nri")
print(f"Data frame length: {len(df)}")

"""
Data frame length: 3510
"""
```

### Query STAC API By Bounding Box

```python
easier = client.web3(local_gateway="", stac="<YOUR STAC ENDPOINT GOES HERE>")
"""
Retrieve all items from STAC catalog that are in bounding box with searchSTACByBox method (2 arguments)
1. Coordinates of bounding box
2. Name(s) of STAC collections)
"""
items = easier.searchSTACByBox([-76.964657, 38.978967, -76.928008, 39.002783], ["<STAC COLLECTION GOES HERE>"])

"""
The searchSTACByBoxIndex by method takes 3 arguments
1. Coordinates for the bounding box
2. Name of the STAC collection to query
3. Index of the item you want to retrieve
"""
item = easier.searchSTACByBoxIndex([-76.964657, 38.978967, -76.928008, 39.002783], ["<STAC COLLECTION GOES HERE>"], 0)
band = easier.getAssetFromItem(item, 'ASSET NAME GOES HERE') # Returns asset object

# Optionally, you can fetch multiple assets by the getBandsFromItem Method
bands = easier.getAssetsFromItem(item, ["blue", "red"]) # Returns array of assets
```

### The asset object

```python
# This snippet extends the previous under "Query STAC API By Bounding Box"

# The asset object, when printed, will return the CID
print(band) # QmNddx9BvBsQMXgwp6a83D2wiLrmovgCpRKVYKSJoWNNbx

# You can fetch the asset bytes through the fetch method
data = band.fetch()

# Alternatively, you can fetch the asset as an np array
asset_array = band.fetchNPArray()
```

# Attributions

This project was made possible by the following

* [ipfsspec](https://github.com/fsspec/ipfsspec)
* [pystac-client](https://github.com/stac-utils/pystac-client)
