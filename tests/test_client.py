from ipfs_stac.client import Web3
from pystac import Item
from unittest.mock import Mock, patch
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


    @patch('pystac_client.client.Client.open')
    def test_searchSTACByBox(self, mock_open):
        # Set up fake STAC catalog response
        mock_catalog = Mock()
        mock_search = Mock()
        mock_catalog.search.return_value = mock_search
        mock_search.item_collection.return_value = [Mock(id='item1'), Mock(id='item2')]

        # Connect the mock catalog to Client.open
        mock_open.return_value = mock_catalog

        # Your client class instantiation here
        client = Web3(stac_endpoint='fake_endpoint')

        # Call the function
        bbox = [10, 20, 30, 40]
        collections = ['collection1', 'collection2']
        result = client.searchSTACByBox(bbox, collections)

        # Assert that the correct items were returned
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, 'item1')
        self.assertEqual(result[1].id, 'item2')

        mock_open.assert_called_once_with('fake_endpoint')
        mock_catalog.search.assert_called_once_with(collections=collections, bbox=bbox)
        mock_search.item_collection.assert_called_once()


    @patch('pystac_client.client.Client.open')
    def test_searchSTACByBoxIndex(self, mock_open):
        # Set up fake STAC catalog response
        mock_catalog = Mock()
        mock_search = Mock()
        mock_catalog.search.return_value = mock_search
        mock_search.item_collection.return_value = [Mock(id='item1'), Mock(id='item2')]

        # Connect the mock catalog to Client.open
        mock_open.return_value = mock_catalog

        # Your client class instantiation here
        client = Web3(stac_endpoint='fake_endpoint')

        # Call the function
        bbox = [10, 20, 30, 40]
        collections = ['collection1', 'collection2']
        index = 1
        result = client.searchSTACByBoxIndex(bbox, collections, index)

        # Assert that the correct item was returned
        self.assertEqual(result.id, 'item2')

        mock_open.assert_called_once_with('fake_endpoint')
        mock_catalog.search.assert_called_once_with(collections=collections, bbox=bbox)
        mock_search.item_collection.assert_called_once()


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
        self.assertEqual(str(asset), "cid")


    def test_getAssetsFromItem(self):
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
                    "alternate": {"IPFS": {"href": "/path/to/cid1"}}
                },
                "asset2": {
                    "href": "/path/to/another-href",
                    "alternate": {"IPFS": {"href": "/path/to/cid2"}}
                }
            }
        }
        item = Item.from_dict(item_dict)
        asset_names = ["asset1", "asset2"]
        assetArray = self.client.getAssetsFromItem(item, asset_names)

        self.assertEqual(len(assetArray), 2)
        self.assertEqual(str(assetArray[0]), "cid1")
        self.assertEqual(str(assetArray[1]), "cid2")


