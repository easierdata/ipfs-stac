
# Standard Library Imports
import io

# Third Party Imports
from ipfs_stac.client import Web3, Asset
import numpy as np

# Local Imports
from .base import SetUp

LOCAL_GATEWAY = "127.0.0.1"
API_PORT = 5001
STAC_ENDPOINT = "http://ec2-54-172-212-55.compute-1.amazonaws.com/api/v1/pgstac/"
GATEWAY_PORT = 8080

class TestIntegration(SetUp):
    def setUp(self):
        self.client = Web3(local_gateway=LOCAL_GATEWAY, stac_endpoint=STAC_ENDPOINT, gateway_port=GATEWAY_PORT)
        # Colosseum, Rome, Italy
        self.bbox = [12.490827, 41.889249, 12.494162, 41.891876]

    def test_asset_creation(self):
        # Colosseum, Rome, Italy
        item = self.client.searchSTACByBox(self.bbox, ["landsat-c2l1"])[0]
        assert(item.id == "LC09_L1TP_191031_20220202_20220202_02_T1")

        red_band_asset = self.client.getAssetFromItem(item, "red")
        assert(type(red_band_asset) == Asset)
        assert(red_band_asset.data == None)
        assert(type(red_band_asset.cid) == str)

    def test_asset_to_np_ndArray(self):
        item = self.client.searchSTACByBox(self.bbox, "landsat-c2l1")[0]
        assert(item.id == "LC09_L1TP_191031_20220202_20220202_02_T1")

        red_band_asset = self.client.getAssetFromItem(item, "red", True)
        assert(type(red_band_asset) == Asset)
        assert(red_band_asset.data)
        assert(type(red_band_asset.data) == bytes)

        red_band_ndarray = red_band_asset.to_np_ndarray()
        assert(type(red_band_ndarray) == np.ndarray)
        assert(red_band_ndarray.shape == (8031, 7931))
        assert(red_band_ndarray.dtype == np.float32)
        assert(red_band_ndarray[0,0] == 0)

    def test_asset_ndvi_calc(self):
        item = self.client.searchSTACByBox(self.bbox, "landsat-c2l1")[0]
        nir_band_asset = self.client.getAssetFromItem(item, "nir08", True)
        nir_band_np = nir_band_asset.to_np_ndarray()
        red_band_asset = self.client.getAssetFromItem(item, "red", True)
        red_band_np = red_band_asset.to_np_ndarray()

        eps = 0.0001 # Avoid divide by zero errors
        ndvi = (nir_band_np - red_band_np) / (nir_band_np + red_band_np + eps)
        assert(type(ndvi) == np.ndarray)
        assert(ndvi.shape == (8031, 7931))
        assert(ndvi.dtype == np.float32)