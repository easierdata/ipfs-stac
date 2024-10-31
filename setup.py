from setuptools import find_packages, setup

setup(
    name="ipfs_stac",
    packages=find_packages(include=["ipfs_stac"]),
    package_data={"ipfs_stac": ["config.json"]},
    version="0.2.0",
    description="The EASIER Data Initiative Python IPFS-STAC Client",
    author="The EASIER Data Initiative",
    license="MIT",
    install_requires=[
        "ipfsspec",
        "fsspec",
        "requests",
        "pandas",
        "beautifulsoup4",
        "pystac-client",
        "Pillow",
        "numpy",
        "rasterio",
        "yaspin",
        "psutil",
    ],
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    test_suite="tests",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    project_urls={
        "Twitter": "https://twitter.com/easierdataorg",
        "GitHub": "https://github.com/easierdata/ipfs-stac",
    },
)
