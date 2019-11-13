import os
from setuptools import setup


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name='tsio',
      version='0.0.1',
      author="Vinícius Calasans",
      author_email="calasans.vinicius@gmail.com",
      description="A library for reading and writing time series with a MongoDB database.",
      license="LGPL",
      keywords="MongoDB timeseries time series",
      url="https://github.com/LANXDEV/tsio",
      packages=['tsio'],
      python_requires='>3.7',
      install_requires=['numpy>=1.17.0',
                        'pandas>=0.25.0',
                        'pymongo>=3.9.0'],
      long_description=read('README.md'),
      )
