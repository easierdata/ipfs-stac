from ipfs_stac.client import Web3
from pystac import Item

from .base import SetUp


class TestClient(SetUp):
    def setUp(self):
        self.client = Web3(local_gateway="http://127.0.0.1:8080")

    def test_getFromCID(self):
        data = self.client.getFromCID(self.TEST_CID)
        self.assertEqual(data, "Hello World!")

    # def test_uploadToIPFS(self):
    #     test_file = self.TEST_FILE
    #     cid = self.client.uploadToIPFS(test_file)
    #     data = self.client.getFromCID(cid)
    #     self.assertEqual(data, "Foobar")


    def test_getAssetFromItem(self):
        item_dict = {
            "stac_version": "1.0.0",
            "type": "Feature",
            "id": "test_item",
            "bbox": [],
            "geometry": {},
            "properties": {
                "datetime": "2021-01-01T00:00:00Z"
            },
            "collection": "simple-collection",
            "links": [],
            "assets": {
                "asset1": {
                    "href": "/path/to/top-level-href",
                    "alternate": {
                        "IPFS": {
                            "href": "/path/to/cid"
                        }
                    }
                }
            }
        }
        item = Item.from_dict(item_dict)
        asset = self.client.getAssetFromItem(item, "asset1")
        self.assertEqual(str(asset), "cid")  # or any other assertions as needed

