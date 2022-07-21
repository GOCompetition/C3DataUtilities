from setuptools import setup

setup(
    name="C3DataUtilities",
    version="0.1.0",
    description="GO Competition Challenge 3 utilities for checking problem data and evaluating solutions",
    author="Jesse Holzer",
    author_email="jesse.holzer@pnnl.gov",
    packages=[
        "data_utilities"
    ],
    install_requires=[
        "scipy",
        "numpy",
        "pandas",
        "pydantic",
        "datamodel"
    ]
)
