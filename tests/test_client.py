## Standard Library Imports
from unittest.mock import Mock, mock_open, patch
import io
# import subprocess
import numpy as np

## Third Party Imports
from pystac import Item
from bs4 import BeautifulSoup
import pandas as pd
from PIL import Image

## Local Imports
from ipfs_stac.client import Web3, Asset
from .base import SetUp

LOCAL_GATEWAY = "http://127.0.0.1:8080"

class TestClient(SetUp):
    def setUp(self):
        self.client = Web3(local_gateway=LOCAL_GATEWAY)

    def test_getFromCID(self):
        data = self.client.getFromCID(self.TEST_CID)
        self.assertEqual(data, "Hello World!")

    @patch('os.system')
    def test_startDaemon(self, mock_system):
        # Your client class instantiation here
        client = Web3(stac_endpoint='fake_endpoint')

        # Call the function
        client.startDaemon()

        # Assert that the correct command was called
        mock_system.assert_called_once_with("ipfs daemon")
    
    @patch('requests.get')
    @patch('ipfs_stac.client.Web3.getFromCID')
    def test_getCSVDataframeFromCID(self, mock_getFromCID, mock_get):
        # Simulating the HTML content
        html_content = '<a href="http://example.tech/link1"></a><a href="link2"></a>'
        soup = BeautifulSoup(html_content, "html.parser")
        endpoint = f"{soup.find_all('a')[0].get('href').replace('.tech', '.io')}{soup.find_all('a')[-1].get('href')}"
        # Simulating the CSV response
        csv_response = Mock()
        csv_response.text = 'column1,column2\nvalue1,value2'
        mock_get.return_value = csv_response
        # Simulating the HTML content returned from CID
        mock_getFromCID.return_value = html_content

        # Your client class instantiation here
        client = Web3(stac_endpoint='fake_endpoint')

        # Call the function
        cid = 'fake_cid'
        df = client.getCSVDataframeFromCID(cid)

        # Assert that the correct dataframe was returned
        expected_df = pd.read_csv(io.StringIO(csv_response.text))
        pd.testing.assert_frame_equal(df, expected_df)

        # Additional assertions to check that the correct functions were called
        mock_getFromCID.assert_called_once_with(cid)
        mock_get.assert_called_once_with(endpoint)


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


    @patch('fsspec.open')
    def test_writeCID(self, mock_fsspec_open): #TODO remove mocks?
        # Your client class instantiation here
        client = Web3(stac_endpoint='fake_endpoint')

        # Dummy CID and file path
        cid = "fake_cid"
        filePath = "path/to/yourfile.txt"

        # Create a mock file object
        mock_file = mock_open()
        contents = b"file contents"

        # Mock the fsspec open method
        mock_fsspec_open.return_value.__enter__.return_value.read.return_value = contents

        with patch("builtins.open", mock_file):
            # Call the function
            client.writeCID(cid, filePath)

            # Assert that the file was opened with correct path and mode
            mock_file.assert_called_once_with(filePath, "wb")

            # Assert that the contents were written to the file
            mock_file().write.assert_called_once_with(contents)


class TestAsset(SetUp):
    def setUp(self):
        self.asset = Asset(self.TEST_CID, LOCAL_GATEWAY)
    
    def test_str_representation(self):
        self.assertEqual(str(self.asset), self.TEST_CID)

    def test_fetch(self):
        result = self.asset.fetch()
        content = result.read().decode('utf-8')
        self.assertEqual(content, "Hello World!")

    # def test_pin(self):
    #     # Remove the asset from the pinned objects
    #     subprocess.run(f"ipfs pin rm {self.TEST_CID}", shell=True)

    #     self.asset.pin()

    #     # Check if the CID exists in the pinned objects
    #     result = subprocess.run(f"ipfs pin ls | grep {self.TEST_CID}", shell=True)
    #     self.assertEqual(result.returncode, 0)

    @patch('fsspec.open')
    def test_fetchNPArray(self, mock_fsspec_open): #TODO Add an image to the test data folder and remove mock.

        # Create an example image
        image = Image.new("RGB", (50, 50))
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        image_bytes.seek(0)

        # Mock the fsspec open method
        mock_fsspec_open.return_value.__enter__.return_value.read.return_value = image_bytes.read()

        result = self.asset.fetchNPArray()
        self.assertEqual(result.shape, (50, 50, 3))
        self.assertTrue(isinstance(result, np.ndarray))