## Standard Library Imports
from pathlib import Path
from unittest.mock import Mock, mock_open, patch, MagicMock
from io import BytesIO
import subprocess
import numpy as np
import requests
import time

## Third Party Imports
from pystac import Item
from PIL import Image

## Local Imports
from ipfs_stac.client import Web3, Asset

from .base import SetUp, import_configuration

# import configuration settings from config.json file
props = import_configuration()

LOCAL_GATEWAY = str(props["ipfs_gateway_ip"])
STAC_ENDPOINT = str(props["stac_endpoint"])
API_PORT = int(props["ipfs_api_port"])
GATEWAY_PORT = int(props["ipfs_gateway_port"])
SAMPLE_STAC_ENDPOINT_URL = "https://landsatlook.usgs.gov/stac-server/"


class TestWeb3(SetUp):
    def setUp(self) -> None:
        self.client = Web3(
            local_gateway=LOCAL_GATEWAY,
            stac_endpoint=STAC_ENDPOINT,
            gateway_port=GATEWAY_PORT,
        )

    def test_init(self):
        self.assertEqual(self.client.local_gateway, LOCAL_GATEWAY)
        self.assertEqual(self.client.stac_endpoint, STAC_ENDPOINT)

    def test_getFromCID_text(self):
        data = self.client.getFromCID(self.TEXT_FILE_CID)
        assert data is not None
        data_str = data.decode("utf-8")
        self.assertEqual(data_str, "Hello World!")

    def test_getFromCID_image(self):
        data = self.client.getFromCID(self.IMAGE_FILE_CID)
        assert data is not None
        image = Image.open(BytesIO(data))
        # xkcd comic
        self.assertEqual(image.size, (50, 50))

    def test_getFromCID_invalid_CID(self):
        with self.assertRaises(FileNotFoundError):
            self.client.getFromCID("invalid_CID")

    # @unittest.skip("Skipping this test case. More work needed")
    @patch("pystac_client.client.Client.open")
    def test_searchSTACByBox(self, mock_open):
        # Set up fake STAC catalog response
        mock_catalog = Mock()
        mock_search = Mock()
        mock_catalog.search.return_value = mock_search
        mock_search.item_collection.return_value = [Mock(id="item1"), Mock(id="item2")]

        mock_collections = [Mock(id="collection1"), Mock(id="collection2")]
        mock_catalog.get_collections.return_value = mock_collections

        # Connect the mock catalog to Client.open
        mock_open.return_value = mock_catalog

        # Your client class instantiation here
        client = Web3(stac_endpoint=SAMPLE_STAC_ENDPOINT_URL)

        # Call the function
        bbox = [10.0, 20.0, 30.0, 40.0]
        collections = ["collection1", "collection2"]
        result = client.searchSTACByBox(bbox, collections)

        # Assert that the correct items were returned
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, "item1")
        self.assertEqual(result[1].id, "item2")

        mock_catalog.search.assert_called_once_with(collections=collections, bbox=bbox)
        mock_search.item_collection.assert_called_once()
        mock_catalog.get_collections.assert_called_once()

    @patch("pystac_client.client.Client.open")
    def test_searchSTACByBoxIndex(self, mock_open):
        # Set up fake STAC catalog response
        mock_catalog = Mock()
        mock_search = Mock()
        mock_catalog.search.return_value = mock_search
        mock_search.item_collection.return_value = [Mock(id="item1"), Mock(id="item2")]

        mock_collections = [Mock(id="collection1"), Mock(id="collection2")]
        mock_catalog.get_collections.return_value = mock_collections

        # Connect the mock catalog to Client.open
        mock_open.return_value = mock_catalog

        # Your client class instantiation here
        client = Web3(stac_endpoint=SAMPLE_STAC_ENDPOINT_URL)

        # Call the function
        bbox = [10.0, 20.0, 30.0, 40.0]
        collections = ["collection1", "collection2"]
        index = 1
        result = client.searchSTACByBoxIndex(bbox, collections, index)

        # Assert that the correct item was returned
        self.assertEqual(result.id, "item2")

        mock_catalog.search.assert_called_once_with(collections=collections, bbox=bbox)
        mock_search.item_collection.assert_called_once()

    def test_getAssetFromItem(self):
        item_dict = {
            "stac_version": "1.0.0",
            "type": "Feature",
            "id": "test_item",
            "bbox": [],
            "geometry": {},
            "properties": {"datetime": "2021-01-01T00:00:00Z"},
            "collection": "simple-collection",
            "links": [],
            "assets": {
                "asset1": {
                    "href": "/path/to/top-level-href",
                    "alternate": {"IPFS": {"href": "/path/to/cid"}},
                }
            },
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
            "properties": {"datetime": "2021-01-01T00:00:00Z"},
            "collection": "simple-collection",
            "links": [],
            "assets": {
                "asset1": {
                    "href": "/path/to/top-level-href",
                    "alternate": {"IPFS": {"href": "/path/to/cid1"}},
                },
                "asset2": {
                    "href": "/path/to/another-href",
                    "alternate": {"IPFS": {"href": "/path/to/cid2"}},
                },
            },
        }
        item = Item.from_dict(item_dict)
        asset_names = ["asset1", "asset2"]
        assetArray = self.client.getAssetsFromItem(item, asset_names)
        assert assetArray is not None
        self.assertEqual(len(assetArray), 2)
        self.assertEqual(str(assetArray[0]), "cid1")
        self.assertEqual(str(assetArray[1]), "cid2")

    @patch("fsspec.open")
    def test_writeCID(self, mock_fsspec_open):  # TODO remove mocks?
        # Your client class instantiation here
        client = Web3(stac_endpoint=SAMPLE_STAC_ENDPOINT_URL)

        # Dummy CID and file path
        cid = "fake_cid"
        filePath = Path("tests/data/yourfile.txt").resolve()

        # Delete the file if it exists
        if filePath.exists():
            filePath.unlink()
        # Create a mock file object
        mock_file = mock_open()
        contents = b"file contents"

        # Mock the fsspec open method
        mock_fsspec_open.return_value.__enter__.return_value.read.return_value = (
            contents
        )

        with patch("builtins.open", mock_file):
            # Call the function
            client.writeCID(cid, filePath)

            # Assert that the file was opened with correct path and mode
            # mock_file.assert_called_once_with(filePath.as_posix(), "wb")
            # Assert that the contents were written to the file
            # mock_file().write.assert_called_once_with(contents)

            # Check if the content in the file is the same as the content we expect by not using the mock.write method
            with Path.open(filePath, "rb") as f:
                data = f.read()
                self.assertEqual(data, contents)
            if filePath.exists():
                filePath.unlink()

    def test_uploadToIPFS_file_path(self):
        cid = self.client.uploadToIPFS(content=self.TEXT_FILE_PATH)
        assert cid is not None
        data = self.client.getFromCID(cid)
        assert data is not None
        data_str = data.decode("utf-8")
        self.assertEqual(data_str, "Hello World!")

    def test_uploadToIPFS_bytes(self):
        with Path.open(self.TEXT_FILE_PATH, "rb") as f:
            bytes = f.read()
        cid = self.client.uploadToIPFS(content=bytes)
        assert cid is not None
        data = self.client.getFromCID(cid)
        assert data is not None
        data_str = data.decode("utf-8")
        self.assertEqual(data_str, "Hello World!")

    def test_uploadedCID_correct(self):
        cid = self.client.uploadToIPFS(content=self.TEXT_FILE_PATH)
        self.assertEqual(cid, self.TEXT_FILE_CID)
        pinned_list = self.client.pinned_list()
        assert pinned_list is not None
        self.assertIn(self.TEXT_FILE_CID, pinned_list)

    def test_pinned_list(self):
        subprocess.run(f"ipfs pin rm {self.TEXT_FILE_CID}", shell=True)
        self.client.uploadToIPFS(content=self.TEXT_FILE_PATH, pin_content=True)
        pinned_list = self.client.pinned_list()
        assert pinned_list is not None
        self.assertIn(self.TEXT_FILE_CID, pinned_list)

    @patch("psutil.process_iter")
    @patch("subprocess.Popen")
    @patch("requests.post")
    def test_startDaemon(self, mock_post, mock_popen, mock_process_iter):
        # Mock process_iter to simulate no running process
        mock_process_iter.return_value = []
        mock_post.return_value.status_code = 200

        self.client.startDaemon()

        mock_popen.assert_called_once_with(["ipfs", "daemon"])
        mock_post.assert_called_once_with(
            f"http://{self.client.local_gateway}:{self.client.api_port}/api/v0/id",
            timeout=10,
        )

    @patch("subprocess.Popen")
    @patch("requests.post")
    @patch("psutil.process_iter")
    @patch("atexit.register")
    def test_startDaemon_already_running(
        self, mock_atexit, mock_process_iter, mock_post, mock_popen
    ):
        # Simulate IPFS daemon already running
        mock_process_iter.return_value = [MagicMock(info={"name": "ipfs"})]
        mock_post.return_value.status_code = 200

        self.client.startDaemon()

        mock_popen.assert_not_called()
        mock_post.assert_called_once_with(
            f"http://{self.client.local_gateway}:{self.client.api_port}/api/v0/id",
            timeout=10,
        )
        mock_atexit.assert_not_called()

    @patch("subprocess.Popen")
    @patch("requests.post")
    @patch("psutil.process_iter")
    @patch("atexit.register")
    def test_startDaemon_not_running(
        self, mock_atexit, mock_process_iter, mock_post, mock_popen
    ):
        # Simulate IPFS daemon not running
        mock_process_iter.return_value = []
        mock_post.return_value.status_code = 200

        self.client.startDaemon()

        mock_popen.assert_called_once_with(["ipfs", "daemon"])
        mock_post.assert_called_once_with(
            f"http://{self.client.local_gateway}:{self.client.api_port}/api/v0/id",
            timeout=10,
        )
        mock_atexit.assert_called_once()

    @patch("subprocess.Popen")
    @patch("requests.post")
    @patch("psutil.process_iter")
    @patch("atexit.register")
    def test_startDaemon_fail_to_start(
        self, mock_atexit, mock_process_iter, mock_post, mock_popen
    ):
        # Simulate IPFS daemon not running and failing to start
        mock_process_iter.return_value = []
        mock_post.side_effect = requests.exceptions.ConnectionError

        with self.assertRaises(Exception) as context:
            self.client.startDaemon()

        self.assertTrue("Failed to start IPFS daemon" in str(context.exception))
        mock_popen.assert_called_once_with(["ipfs", "daemon"])
        mock_atexit.assert_called_once()

    @patch("subprocess.Popen")
    @patch("requests.post")
    @patch("psutil.process_iter")
    @patch("atexit.register")
    def test_startDaemon_shutdown_process(
        self, mock_atexit, mock_process_iter, mock_post, mock_popen
    ):
        # Simulate IPFS daemon not running
        mock_process_iter.return_value = []
        mock_post.return_value.status_code = 200

        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        self.client.startDaemon()

        mock_popen.assert_called_once_with(["ipfs", "daemon"])
        mock_post.assert_called_once_with(
            f"http://{self.client.local_gateway}:{self.client.api_port}/api/v0/id",
            timeout=10,
        )
        mock_atexit.assert_called_once_with(self.client.shutdown_process)

        # Simulate shutdown
        assert self.client.daemon_status is not None
        self.client.daemon_status.terminate()
        self.client.daemon_status.kill()
        self.client.shutdown_process()
        self.assertIsNone(self.client.daemon_status)

    @patch("psutil.process_iter")
    @patch("subprocess.Popen")
    @patch("requests.post")
    def test_shutdown_process(self, mock_post, mock_popen, mock_process_iter):
        mock_process_iter.return_value = []
        mock_post.return_value.status_code = 200

        self.client.startDaemon()

        with patch.object(self.client.daemon_status, "terminate") as mock_terminate:
            self.client.shutdown_process()
            mock_terminate.assert_called_once()
            self.assertIsNone(self.client.daemon_status)

    @patch("psutil.process_iter")
    @patch("subprocess.Popen")
    def test_shutdown_process_none(self, mock_subprocess, mock_psutil):
        self.client.startDaemon()
        self.client.shutdown_process()
        self.assertIsNone(self.client.daemon_status)

    @patch("psutil.process_iter")
    @patch("subprocess.Popen")
    def test_shutdown_process_active(self, mock_subprocess, mock_psutil):
        mock_process = MagicMock()
        self.client.daemon_status = mock_process
        self.client.shutdown_process()
        mock_process.terminate.assert_called_once()
        self.assertIsNone(self.client.daemon_status)

    @patch("psutil.process_iter")
    @patch("subprocess.Popen")
    def test_shutdown_process_exception(self, mock_subprocess, mock_psutil):
        mock_process = MagicMock()
        mock_process.terminate.side_effect = Exception("Terminate failed")
        self.client.daemon_status = mock_process
        with self.assertRaises(Exception):
            self.client.shutdown_process()
        mock_process.kill.assert_not_called()
        self.assertIsNotNone(self.client.daemon_status)


class TestAsset(SetUp):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.daemon_status = cls.start_ipfs_daemon()

    @classmethod
    def tearDownClass(cls):
        if cls.daemon_status:
            print("Terminating IPFS daemon")
            cls.daemon_status.terminate()
            cls.daemon_status.kill()
            cls.daemon_status = None
        super().tearDownClass()

    @staticmethod
    def start_ipfs_daemon():
        print("Starting IPFS daemon")
        return subprocess.Popen(["ipfs", "daemon"])

    def setUp(self):
        self.text_asset = Asset(
            self.TEXT_FILE_CID, LOCAL_GATEWAY, API_PORT, fetch_data=True
        )
        self.text_asset_no_fetch = Asset(
            self.TEXT_FILE_CID, LOCAL_GATEWAY, API_PORT, fetch_data=False
        )
        self.image_asset = Asset(
            self.IMAGE_FILE_CID, LOCAL_GATEWAY, API_PORT, fetch_data=True
        )

    def test_init(self):
        self.assertEqual(self.text_asset.cid, self.TEXT_FILE_CID)
        self.assertEqual(self.text_asset.local_gateway, LOCAL_GATEWAY)

    def test_str_representation(self):
        self.assertEqual(str(self.text_asset), self.TEXT_FILE_CID)

    def test_fetch(self):
        assert self.text_asset_no_fetch.data is None
        self.text_asset_no_fetch.fetch()
        assert self.text_asset_no_fetch.data is not None
        content = self.text_asset_no_fetch.data.decode("utf-8")
        self.assertEqual(content, "Hello World!")

    def test_pin(self):
        # Remove the asset from the pinned objects
        subprocess.run(f"ipfs pin rm {self.TEXT_FILE_CID}", shell=True)

        self.text_asset.pin()

        # Check if the CID exists in the pinned objects
        result = subprocess.run(f"ipfs pin ls {self.TEXT_FILE_CID}", shell=True)
        self.assertEqual(result.returncode, 0)

    def test_to_np_ndarray(self):
        np_array = self.image_asset.to_np_ndarray()
        self.assertIsInstance(np_array, np.ndarray)
        self.assertEqual(np_array.shape, (50, 50))
