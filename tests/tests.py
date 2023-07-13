from easier_python_client import client

def testDataframe():
    easier = client.web3("", "")
    df = easier.getCSVDataframeFromCID("bafybeifw6kcodgxnamtuvhkxgaf4ep2rwscjae3gnzxb3zj5c6zyea2nri")
    print(f"Data frame length: {len(df)}")
    print(f"Data frame columns: {df.columns}")

testDataframe()