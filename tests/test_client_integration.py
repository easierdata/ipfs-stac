# Standard Library Imports
# import io

# Third Party Imports
from ipfs_stac.client import Web3, Asset
import numpy as np

# Local Imports
from .base import SetUp, import_configuration

# import configuration settings from config.json file
props = import_configuration()

LOCAL_GATEWAY = str(props["ipfs_gateway_ip"])
API_PORT = int(props["ipfs_api_port"])
STAC_ENDPOINT = str(props["stac_endpoint"])
GATEWAY_PORT = int(props["ipfs_gateway_port"])


class TestIntegration(SetUp):
    def setUp(self) -> None:
        self.client = Web3(
            local_gateway=LOCAL_GATEWAY,
            stac_endpoint=STAC_ENDPOINT,
            gateway_port=GATEWAY_PORT,
            api_port=API_PORT,
        )
        # Colosseum, Rome, Italy
        self.bbox = [12.490827, 41.889249, 12.494162, 41.891876]

    def test_asset_creation(self) -> None:
        # Colosseum, Rome, Italy
        item = self.client.searchSTACByBox(self.bbox, ["landsat-c2l1"])[0]
        assert item.id == "LC09_L1TP_191031_20220202_20220202_02_T1"

        red_band_asset = self.client.getAssetFromItem(item, "red", fetch_data=True)
        assert isinstance(red_band_asset, Asset)
        assert red_band_asset.data
        assert isinstance(red_band_asset.cid, str)

    def test_asset_to_np_ndArray(self) -> None:
        collection_list = ["landsat-c2l1"]
        item = self.client.searchSTACByBox(self.bbox, collection_list)[0]
        assert item.id == "LC09_L1TP_191031_20220202_20220202_02_T1"

        red_band_asset = self.client.getAssetFromItem(item, "red", fetch_data=True)
        assert isinstance(red_band_asset, Asset)
        assert red_band_asset.data
        assert isinstance(red_band_asset.data, bytes)

        red_band_ndarray = red_band_asset.to_np_ndarray()
        assert isinstance(red_band_ndarray, np.ndarray)
        assert red_band_ndarray.shape == (8031, 7931)
        assert red_band_ndarray.dtype == np.float32
        assert red_band_ndarray[0, 0] == 0

    def test_asset_ndvi_calc(self) -> None:
        collection_list = ["landsat-c2l1"]
        item = self.client.searchSTACByBox(self.bbox, collection_list)[0]
        nir_band_asset = self.client.getAssetFromItem(item, "nir08", True)
        assert nir_band_asset is not None
        nir_band_np = nir_band_asset.to_np_ndarray()
        red_band_asset = self.client.getAssetFromItem(item, "red", True)
        assert red_band_asset is not None
        red_band_np = red_band_asset.to_np_ndarray()

        eps = 0.0001  # Avoid divide by zero errors
        ndvi = (nir_band_np - red_band_np) / (nir_band_np + red_band_np + eps)
        assert type(ndvi) == np.ndarray
        assert ndvi.shape == (8031, 7931)
        assert ndvi.dtype == np.float32
