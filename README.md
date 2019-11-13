# Time Series I/O

This project implements a simple Time Series object and an interface for reading and writing these objects with MongoDB.
It also provides a generalized reading interface. This 'interface' is a class that receives specific reader objects upon
its instantiation. These objects are then used for reading Time Series data from external sources.

## Requirements
- A running MongoDB instance

See also the Dependencies section below.

## Installation

```sh
pip install git+https://github.com/LANXDEV/tsio/
```

## Dependencies
- [NumPy](https://www.numpy.org): 1.17.0 or higher
- [pandas](https://pandas.pydata.org/): 0.25.0 or higher
- [PyMongo](https://api.mongodb.com/python/current/): 3.9.0 or higher


## Authors
* **Vinícius Calasans** - [vcalasans](https://github.com/vcalasans)


## License

This project is licensed under the GNU GPL v3. See [License](LICENSE) for details.
