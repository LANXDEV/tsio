# Time Series I/O

This project implements a simple Time Series object and an interface for reading and writing these objects with MongoDB.
It also provides a generalized reading interface. This 'interface' is a class that receives specific reader objects upon
its instantiation. These objects are then used for reading Time Series data from external sources.

Check the project's [Documentation](https://lanxdev.github.io/tsio/index).

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


## Acknowledgements

Time Series I/O has been developed at [Lanx Capital Investimentos](https://www.lanxcapital.com/) since 2016, providing
a base for our internal frameworks. It wouldn't be possible without the support and insight provided by our team of
analysts:

- Tulio Ribeiro
- Eduardo Thiele
- Pedro Coelho
- Humberto Nardiello


## License

This project is licensed under the GNU LGPL v3. See [Copying](COPYING) and [Copying.Lesser](COPYING.LESSER) for details.
