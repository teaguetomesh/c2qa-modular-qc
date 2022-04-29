import io
from setuptools import find_packages, setup

name = "arquin"

description = "A compiler for distributed quantum architectures"

# README file as long_description.
long_description = io.open("README.md", encoding="utf-8").read()


# Read in requirements
requirements = open("requirements.txt").readlines()
requirements = [r.strip() for r in requirements]

arquin_packages = ["arquin"] + ["arquin." + package for package in find_packages(where="arquin")]

setup(
    name=name,
    url="",
    author="Wei Tang and Teague Tomesh",
    author_email="ttomesh@princeton.edu",
    python_requires=(">=3.7.0"),
    install_requires=requirements,
    extras_require={},
    license="N/A",
    description=description,
    long_description=long_description,
    packages=arquin_packages,
    package_data={"arquin": ["py.typed"]},
)
