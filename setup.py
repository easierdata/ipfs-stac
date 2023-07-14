from setuptools import find_packages, setup

setup(
    name='easier_python_client',
    packages=find_packages(include=['easier_python_client']),
    version='0.1.4',
    description='The EASIER Data Initiative Python IPFS Client',
    author='The EASIER Data Initiative',
    license='MIT',
    install_requires=['ipfsspec', 'fsspec', 'requests', 'pandas', 'beautifulsoup4', 'pystac-client'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    test_suite='tests',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown'
)