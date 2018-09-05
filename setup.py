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
      author="Lanx Capital & Vinícius Calasans",
      author_email="calasans.vinicius@gmail.com",
      description="A library for reading and writing time series with a MongoDB database.",
      license="GPL",
      keywords="MongoDB timeseries time series",
      url="",
      packages=['tsio'],
      python_requires='>3.0',
      install_requires=['numpy>=1.14.2',
                        'pandas>=0.22.0',
                        'pymongo>=3.6.1'],
      long_description=read('README'),
      )