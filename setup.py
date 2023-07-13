from setuptools import find_packages, setup

setup(
    name='easier_python_client',
    packages=find_packages(include=['easier_python_client']),
    version='0.1.0',
    description='The EASIER Data Initiative Python IPFS Client',
    author='The EASIER Data Initiative',
    license='MIT',
    install_requires=[],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    test_suite='tests'
)