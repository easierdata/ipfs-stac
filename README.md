# IPFS-STAC

`ipfs-stac` is a Python library that provides functionality for querying and interacting with STAC catalogs enriched with IPFS. The library supports seamless operations between leveraging STAC APIs enriched with IPFS metadata and interfacing with IPFS itself given a node.

## Features
- Query/search STAC APIs
- Fetch content via CIDs
- Start/stop local IPFS Daemon 
- Retrieve asset names
- Retrieve catalogs and item collections
- Upload content to IPFS
- Parse IPFS data into DataFrames
- Transform assets to NumPy arrays
- Pin IPFS CIDs
- Host IPFS content on the mutable file system (MFS)

---
### Language Support

The client currently supports Python versions 3+

### Installation

The client can be installed through pip

```shell
$ pip install ipfs-stac
```
---
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

### Query STAC API By Bounding Box

```py
easier = client.Web3(local_gateway="127.0.0.1", stac="<my_stac_server>/api/v1/pgstac/")
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

### The Asset Object

```py
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
---

## Documentation

### `class Web3`

#### `__init__(local_gateway: str = "localhost", api_port: int = 5001, gateway_port: int = 8080, stac_endpoint: str = "")`

**Description**:  
Initializes a Web3 client.

**Parameters**:  
- `local_gateway` (str): Local gateway endpoint without port.  
- `api_port` (int): Kubo RPC API port.  
- `gateway_port` (int): Gateway port.  
- `stac_endpoint` (str): STAC API endpoint.

**Attributes**
- `local_gateway` (str): Local gateway endpoint without port.  
- `api_port` (int): Kubo RPC API port.  
- `gateway_port` (int): Gateway port.  
- `stac_endpoint` (str): STAC API endpoint.
- `daemon_status`: Points to IPFS daemon subprocess
- `client` (Client): Instance of pystac client configured to STAC API
- `collections` (List[str]): list of collection ids

---

#### `_get_collections_ids() -> List[str]`

**Description**:  
Fetches the collection IDs from the STAC endpoint.

**Returns**:  
- `List[str]`: A list of collection IDs.

---

#### `getCollections() -> Sequence[Collection]`

**Description**:  
Returns a list of collections from the STAC endpoint.

**Returns**:  
- `Sequence[Collection]`: List of collections.

---

#### `startDaemon() -> None`

**Description**:  
Starts the IPFS daemon process.

**Raises**:  
- `Exception`: If the IPFS daemon fails to start.

---

#### `shutdown_process() -> None`

**Description**:  
Shuts down the IPFS daemon process.

---

#### `getFromCID(cid: str) -> Union[bytes, None]`

**Description**:  
Retrieves raw data from a specified CID.

**Parameters**:  
- `cid` (str): The CID to retrieve.

**Returns**:  
- `Union[bytes, None]`: The retrieved data or `None`.

---

#### `searchSTACByBox(bbox: List[float], collections: List[str]) -> ItemCollection`

**Description**:  
Searches the STAC catalog by bounding box and returns an array of items.

**Parameters**:  
- `bbox` (List[float]): Array of coordinates for the bounding box.  
- `collections` (List[str]): Array of collection names.

**Returns**:  
- `ItemCollection`: A collection of matching STAC items.

---

#### `searchSTAC(**kwargs) -> ItemCollection`

**Description**:  
Searches the STAC catalog for items using the pystac-client search method.

**Parameters**:  
- `**kwargs`: Keyword arguments for the search method.

**Returns**:  
- `ItemCollection`: A collection of matching STAC items.

---

#### `getAssetNames(stac_obj: Union[CollectionClient, ItemCollection, Item]) -> Union[List[str], None]`

**Description**:  
Fetches a list of unique asset names from a given STAC object.

**Parameters**:  
- `stac_obj` (Union[CollectionClient, ItemCollection, Item]): STAC object to retrieve asset names from.

**Returns**:  
- `Union[List[str], None]`: A sorted list of unique asset names or `None`.

---

#### `getAssetFromItem(item: Item, asset_name: str, fetch_data: bool = False) -> Union["Asset", None]`

**Description**:  
Returns an asset object from a specified STAC item.

**Parameters**:  
- `item` (Item): The STAC item.  
- `asset_name` (str): The name of the asset to retrieve.  
- `fetch_data` (bool): Whether to fetch data from the CID.

**Returns**:  
- `Union["Asset", None]`: Instance of asset object or `None`.

---

#### `uploadToIPFS(content: Union[str, Path, bytes], file_name: Optional[str] = None, pin_content: bool = False, mfs_path: Optional[str] = None, chunker: Optional[str] = None) -> None`

**Description**:  
Uploads content to IPFS.

**Parameters**:  
- `content` (Union[str, Path, bytes]): The file path or bytes data to upload.  
- `file_name` (Optional[str]): The file name.  
- `pin_content` (bool): Whether to pin the content locally.  
- `mfs_path` (Optional[str]): Path to add reference in MFS.  
- `chunker` (Optional[str]): Chunking algorithm.

**Raises**:  
- `ValueError`: If params are wrong
- `FileNotFoundError`: If the specified file path does not exist.

---

#### `pinned_list(pin_type: str = recursive, names: bool) -> Union[List[str], None]`

**Description**:  
Fetch pinned CIDs from local node

**Parameters**:  
- `pin_type` (str): The type of pinned keys to list. Can be "direct", "indirect", "recursive", or "all". Defaults to "recursive".  
- `names` (bool): Include pin names in the output. Defaults to False.  

**Returns**:  
- `List[str]`: List of pinned CIDs, if `names` is true, it will return an object instead.

---

### `class Asset`

#### `__init__(cid: str, local_gateway: str, api_port: int, fetch_data: bool = False, name: Optional[str] = None)`

**Description**:  
Initializes an Asset object associated with a CID.

**Parameters**:  
- `cid` (str): The CID associated with the object.  
- `local_gateway` (str): Local gateway endpoint.  
- `api_port` (int): API port for the local IPFS node.  
- `fetch_data` (bool, optional): Whether to fetch data immediately upon instantiation. Defaults to `False`.  
- `name` (Optional[str], optional): Optional name for the asset. Defaults to `None`.

**Attributes**
- `cid` (str): The CID associated with the object.  
- `local_gateway` (str): Local gateway endpoint.  
- `api_port` (int): API port for the local IPFS node.  
- `data` (Optional[bytes]): raw bytes of asset 
- `is_pinned` (bool): Whether the asset is pinned to the configured node/

---

#### `_is_pinned_to_local_node() -> bool`

**Description**:  
Checks if the CID is pinned to the local node.

**Returns**:  
- `bool`: `True` if the CID is pinned, `False` otherwise.

---

#### `fetch() -> None`

**Description**:  
Fetches the data associated with the CID using the `fetchCID` method.

**Raises**:  
- Exception: If there is an error fetching the data.

---

#### `pin() -> None`

**Description**:  
Pins the CID to the configured IPFS node

---

#### `addToMFS(filename: str, mfs_path: str) -> None`

**Description**:  
Adds the CID to the Mutable File System (MFS) in IPFS.

**Parameters**:  
- `filename` (str): The name of the file to be added. If not provided, the asset's name will be used.  
- `mfs_path` (str): The path within the MFS where the file should be added.

---

#### `to_np_ndarray(dtype: Union[np.dtype, type] = np.float32) -> np.ndarray`

**Description**:  
Converts the asset's data into a NumPy ndarray if the data represents an image.

**Parameters**:  
- `dtype` (Union[np.dtype, type], optional): The data type for the ndarray. Defaults to `np.float32`.

**Returns**:  
- `np.ndarray`: The asset's data as a NumPy array.

**Raises**:  
- `ValueError`: If the data has not been fetched.

---

# Attributions

This project was made possible by the following

* [ipfsspec](https://github.com/fsspec/ipfsspec)
* [pystac-client](https://github.com/stac-utils/pystac-client)