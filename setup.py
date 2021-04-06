from setuptools import setup, find_packages


setup(

    name="bbsed",
    version="0.0.1",
    url="https://github.com/slacknate/bbsed",
    description="A tool for editing BBCF sprites.",
    packages=find_packages(include=["bbsed", "bbsed.*"]),
    install_requires=["PyQt5==5.15.4", "libhip==0.0.1", "libhpl==0.0.1", "libpac==0.0.1"]
)
