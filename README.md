# Time Series I/O

This project implements a simple Time Series object and interfaces for reading and writing these objects with MongoDB.
It also provides a generalized reading interface. This 'interface' is a class that receives specific objects upon its
instantiation. These objects are then used for reading Time Series data from external sources.

## Requirements
- A MongoDB instance

## Installation

```sh
pip install git+https://github.com/LANXDEV/tsio/
```

## Dependencies
- [NumPy](https://www.numpy.org): 1.14.2 or higher
- [pandas](https://pandas.pydata.org/): 0.22.0 or higher
- [PyMongo](https://api.mongodb.com/python/current/): 3.6.1 or higher


## Authors
* **Lanx Capital** - [LanxDEV](https://github.com/LANXDEV)
* **Vinícius Calasans** - [vcalasans](https://github.com/vcalasans)


## License

This project is licensed under the GNU GPL v3. See [License](LICENSE) for details.
