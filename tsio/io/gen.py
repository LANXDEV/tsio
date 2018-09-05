"""
GenIO class - Generalized reading class for TimeSeries.
"""
import numpy as np
from tsio.timeseriescollection import TimeSeriesCollection
from tsio.io.db import DBIO, convert_to_ts_collection, instantiate_components


def generate_source_map(ts, external_interfaces):
    """ Map reading sources with time series.

    Parameters
    ----------
    ts: :py:class:`TimeSeries`
        A time series.
    external_interfaces: list(objects)
        Instances of external reading classes.

    Returns
    -------
    dict
        Dictionary with ``{source_index: time_series_collection}`` pairs.
    """
    source_map = dict()
    ts_collection = convert_to_ts_collection(ts)
    for ts in ts_collection:
        for i, external_interface in enumerate(external_interfaces):
            if external_interface.is_member(ts):
                try:
                    source_map[i].add(ts)
                except KeyError:
                    source_map[i] = TimeSeriesCollection([ts])
                break
    return source_map


def flatten(ts, components=True, depth=np.inf):
    """ Create a :py:class:`TimeSeriesCollection` with passed time series and their components.

    Parameters
    ----------
    ts: type convertible to :py:obj:`TimeSeriesCollection`
        Time series collection whose components are to be "flattened".
    components: list(str), optional
        Components to include in the final time series collection. Default is all components.
    depth: int, optional
        Depth of components to include in the final time series collection. Default is infinity.

    Returns
    -------
    :py:obj:`TimeSeriesCollection`
        Flattened time series collection.
    """
    if isinstance(components, list):
        components = [key.upper() for key in components]
    flattened = TimeSeriesCollection()
    temp_ts_collection = convert_to_ts_collection(ts)
    counter = 0
    while counter < depth:
        ts_collection = temp_ts_collection
        if not ts_collection:
            break
        flattened.add_list(ts_collection)
        temp_ts_collection = TimeSeriesCollection()
        counter += 1
        for ts in ts_collection:
            instantiate_components(ts, components, temp_ts_collection)
    return flattened


class GenIO(DBIO):
    """ Generalized reading interface, for reading time series from the database and also external sources.

    The "write" methods behave just like in the :py:class:`DBIO` class. The "read" methods first read from the
    database, the use the external reading interfaces to read from external sources. The external interfaces are
    responsible for resolving whether a time series should be read with it or not with a is_member method.
    (see TODO(example)).

    Note
    ----
    Each external reading class should have methods with the below signatures:

    * ``bool is_member(ts)``: Check whether a time series should be read with this class.
    * ``read_attributes(ts_collection, attributes)``: Read from source the attributes of a time series collection.
    * ``read_values(ts_collection)``: Read from source the values of a time series collection.
    * ``read(ts_collection)``: Read from source the attributes and values of a time series collection.

    Parameters
    ----------
    host_address: str
        Address of the MongoDB daemon.
    db_name: str
        MongoDB database name.
    collection_name: str
        MongoDB collection.
    external_interfaces: list(obj)
        Instances of external reading classes.

    """
    def __init__(self, host_address, db_name, collection_name, external_interfaces=None):
        super().__init__(host_address=host_address, db_name=db_name, collection_name=collection_name)
        if not external_interfaces:
            self.external_interfaces = []
        else:
            self.external_interfaces = external_interfaces
        self.interfaces_map = {i: interface for i, interface in enumerate(self.external_interfaces)}

    def read_attributes(self, ts_collection, components=True, depth=np.inf, attributes=None, use_external=True,
                        **kwargs):
        """ Read time series attributes from the database.

        Parameters
        ----------
        ts_collection: type convertible to :py:class:`TimeSeriesCollection`
            Time series to be read.
        components: list(str), optional
            Optional collection of component names to be read and instantiated. Default is all components.
        depth: int, optional
            Depth of component instantiation. ``depth = 1`` means no components are instantiated. Default is infinity.
        attributes: list(str), optional
            Optional collection of attribute names to be read. Default is all attributes.
        use_external: bool, optional
            Whether to use the external reading classes. Default is True.
        """
        ts = convert_to_ts_collection(ts_collection)
        super().read_attributes(ts_collection=ts, components=components, depth=depth, attributes=attributes)
        if use_external:
            flat_ts_list = flatten(ts)
            source_map = generate_source_map(flat_ts_list, self.external_interfaces)
            for interface_code, ts_list in source_map.items():
                self.interfaces_map[interface_code].read_attributes(ts_collection=ts_list, attributes=attributes,
                                                                    **kwargs)

    def read_values(self, ts_collection, components=True, depth=np.inf, use_external=True, **kwargs):
        """ Read time series values from the database.

        Parameters
        ----------
        ts_collection: type convertible to :py:class:`TimeSeriesCollection`
            Time series to be read.
        components: list(str), optional
            Optional collection of component names to be read and instantiated. Default is all components.
        depth: int, optional
            Depth of component instantiation. ``depth = 1`` means no components are instantiated. Default is infinity.
        use_external: bool, optional
            Whether to use the external reading classes. Default is True.
        kwargs: dict
            Additional parameters to be passed to the external reading classes methods.
        """
        ts = convert_to_ts_collection(ts_collection)
        super().read(ts_collection=ts, components=components, depth=depth)
        if use_external:
            flat_ts_list = flatten(ts)
            source_map = generate_source_map(flat_ts_list, self.external_interfaces)
            for interface_code, ts_list in source_map.items():
                self.interfaces_map[interface_code].read_values(ts_collection=ts_list, **kwargs)

    def read(self, ts_collection, components=True, depth=np.inf, use_external=True, **kwargs):
        """ Read time series attributes and values from the database.

        Parameters
        ----------
        ts_collection: type convertible to :py:class:`TimeSeriesCollection`
            Time series to be read.
        components: list(str), optional
            Optional collection of component names to be read and instantiated. Default is all components.
        depth: int, optional
            Depth of component instantiation. ``depth = 1`` means no components are instantiated. Default is infinity.
        use_external: bool, optional
            Whether to use the external reading classes. Default is True.
        kwargs: dict
            Additional parameters to be passed to the external reading classes methods.
        """
        ts = convert_to_ts_collection(ts_collection)
        super().read(ts_collection=ts, components=components, depth=depth)
        if use_external:
            flat_ts_list = flatten(ts)
            source_map = generate_source_map(flat_ts_list, self.external_interfaces)
            for interface_code, ts_list in source_map.items():
                self.interfaces_map[interface_code].read(ts_collection=ts_list, **kwargs)
