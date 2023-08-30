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

# Create a new client object without a local node (uses remote gateways)
easier = client.Web3(stac_endpoint="<my_stac_server>/api/v1/pgstac/")

# If you want to use your local IPFS node (preferred), specify the endpoint in the local_gateway argument
easier = client.Web3(local_gateway="127.0.0.1", stac_endpoint="<my_stac_server>/api/v1/pgstac/")
```

### Fetch a CID from IPFS

```py
# Simple hello world example
data = easier.getFromCID("QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx")
print(data)

"""
hello worlds
"""
```

### Get CID CSV Data to Pandas Dataframe

```py
df = easier.getCSVDataframeFromCID("bafybeifw6kcodgxnamtuvhkxgaf4ep2rwscjae3gnzxb3zj5c6zyea2nri")
print(f"Data frame length: {len(df)}")

"""
Data frame length: 3510
"""
```

### Query STAC API By Bounding Box

```python
easier = client.Web3(local_gateway="", stac="<YOUR STAC ENDPOINT GOES HERE>")
"""
Retrieve all items from STAC catalog that are in bounding box with searchSTACByBox method (2 arguments)
1. Coordinates of bounding box
2. Name(s) of STAC collections)
"""
# Use any collection name you want. This is just an example
items = easier.searchSTACByBox([-76.964657, 38.978967, -76.928008, 39.002783], "landsat-c2l1") 

"""
The searchSTACByBoxIndex by method takes 3 arguments
1. Coordinates for the bounding box
2. Name of the STAC collection to query
3. Index of the item you want to retrieve
"""
item = easier.searchSTACByBoxIndex([-76.964657, 38.978967, -76.928008, 39.002783], "landsat-c2l1", 0)
# In this example, 'nir08' is the name of the band (asset) we want to retrieve from a landsat item
band = easier.getAssetFromItem(item, 'nir08')

# Optionally, you can fetch multiple assets by the getAssetsFromItem Method
bands = easier.getAssetsFromItem(item, ["blue", "red"]) # Returns array of assets
```

### The asset object

```python
# This snippet extends the previous under "Query STAC API By Bounding Box"

# The asset object, when printed, will return the CID
print(band) # QmNddx9BvBsQMXgwp6a83D2wiLrmovgCpRKVYKSJoWNNbx

# The asset content (bytes) can be found in asset.data. If this is None, you can call the fetch method to retrieve the data.
band.fetch()
print(band.data) # b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x...

# Alternatively, you can also transform the asset data in different formats such as a numpy array
band_np = band.to_np_ndarray()
print(band_np) # [[0. 0. 0. ... 0. 0. 0.]
               #  [0. 0. 0. ... 0. 0. 0.]
               #  [0. 0. 0. ... 0. 0. 0.]
               #  ...
               #  [0. 0. 0. ... 0. 0. 0.]
               #  [0. 0. 0. ... 0. 0. 0.]
               #  [0. 0. 0. ... 0. 0. 0.]]
```

# Attributions

This project was made possible by the following

* [ipfsspec](https://github.com/fsspec/ipfsspec)
* [pystac-client](https://github.com/stac-utils/pystac-client)
