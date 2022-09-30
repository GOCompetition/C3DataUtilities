from setuptools import setup
# from setuptools import find_packages

setup(
    name="C3DataUtilities",
    version="0.1.0",
    description="GO Competition Challenge 3 utilities for checking problem data and evaluating solutions",
    author="Jesse Holzer",
    author_email="jesse.holzer@pnnl.gov",
    # packages=find_packages(),
    packages=[
        "datautilities"
        ],
    package_dir={
        "datautilities": "datautilities"
        },
    install_requires=[
        "scipy",
        "numpy",
        "pandas",
        "pydantic",
        "networkx",
        "psutil",
        "GO-3-data-model",
        ]
)
