import tempfile
from ipfs_stac.client import Web3
from .base import SetUp


class TestClient(SetUp):
    def setUp(self):
        self.client = Web3(local_gateway="http://127.0.0.1:5001")

    def test_getFromCID(self):
        data = self.client.getFromCID(self.TEST_CID)
        self.assertEqual(data, "Hello World!")

    def test_uploadToIPFS(self):
        test_file = tempfile.mkstemp()[1]
        with open(test_file, "w") as f:
            f.write("Foobar")

        cid = self.client.uploadToIPFS(test_file)
        data = self.client.getFromCID(cid)
        self.assertEqual(data, "Foobar")
