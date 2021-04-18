import os

from setuptools import setup, find_packages

VERSION = None

with open(os.path.join("bbsed", "version.py"), "r") as version_fp:
    exec(version_fp.read())

if VERSION is None:
    raise ValueError("Unable to read bbsed version!")


setup(

    name="bbsed",
    version=VERSION,
    url="https://github.com/slacknate/bbsed",
    description="A tool for editing BBCF sprites.",
    packages=find_packages(include=["bbsed", "bbsed.*"]),
    install_requires=["PyQt5==5.15.4", "psutil==5.8.0", "libhip==0.0.1", "libhpl==0.0.1", "libpac==0.0.1"]
)
