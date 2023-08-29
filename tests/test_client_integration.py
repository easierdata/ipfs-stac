
from ipfs_stac.client import Web3, Asset
from .base import SetUp
import io
LOCAL_GATEWAY = "127.0.0.1"
API_PORT = 5001
STAC_ENDPOINT = "http://ec2-54-172-212-55.compute-1.amazonaws.com/api/v1/pgstac/"

class TestIntegration(SetUp):
    def setUp(self):
        self.client = Web3(local_gateway=LOCAL_GATEWAY, stac_endpoint=STAC_ENDPOINT)

    def test_asset_creation(self):
        # Colosseum, Rome, Italy
        bbox = [12.490827, 41.889249, 12.494162, 41.891876]
        item = self.client.searchSTACByBox(bbox, "landsat-c2l1")[0]
        assert(item.id == "LC09_L1TP_191031_20220202_20220202_02_T1")

        red_band_asset = self.client.getAssetFromItem(item, "red")
        assert(type(red_band_asset) == Asset)
        assert(red_band_asset.data)
        assert(type(red_band_asset.data) == io.BytesIO)