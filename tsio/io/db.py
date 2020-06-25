# Copyright (C) 2016-2018 Lanx Capital Investimentos LTDA.
#
# This file is part of Time Series I/O (tsio).
#
# Time Series I/O (tsio) is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# Time Series I/O (tsio) is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Time Series I/O (tsio). If not, see <https://www.gnu.org/licenses/>.
"""
DBIO class for reading/writing TimeSeries from/in MongoDB collections.
"""
import warnings
import datetime
import json
import numpy as np
import pandas as pd
import pymongo
from pymongo.errors import BulkWriteError
from tsio.constants import COMPONENTS, TS_NAME, TS_VALUES, LAST_USE, RESERVED_KEYS, OR_VALUES, \
    AND_VALUES, FIELD
from tsio.io.mongo_operators import AND, OR, SET, IN, ID
from tsio.tools import to_list
from tsio.timeseries import TimeSeries
from tsio.timeseriescollection import TimeSeriesCollection


def convert_to_ts_collection(ts):
    """ Convert a time series list-like object into :py:class:`TimeSeriesCollection`

    Parameters
    ----------
    ts: :py:class:`TimeSeries`, :py:class:`TimeSeriesCollection`, str, list (str, :py:class:`TimeSeries`)

    Returns
    -------
    :py:class:`TimeSeriesCollection`
        Object built with the passed time series list-like.
    """
    if isinstance(ts, TimeSeries):
        result = TimeSeriesCollection()
        result.add(ts)
        return result
    elif isinstance(ts, str):
        result = TimeSeriesCollection()
        result.add(ts)
        return result
    elif isinstance(ts, TimeSeriesCollection):
        return ts
    elif isinstance(ts, list):
        result = TimeSeriesCollection()
        for i in ts:
            result.add(i)
        return result


def ts_to_dict(ts):
    """ Convert :py:class:`TimeSeries` to dict, for writing in the database.

    Parameters
    ----------
    ts: object convertible to :py:class:`TimeSeriesCollection`
        A time series.

    Returns
    -------
    dict
        Dictionary ready to be written in MongoDB.
    """
    json_list = list()
    ts_collection = convert_to_ts_collection(ts)
    for ts in ts_collection:
        entry = ts_attributes_to_dict(ts)
        entry[TS_NAME] = ts.ts_name
        entry[TS_VALUES] = ts_values_to_dict(ts)
        json_list.append(entry)
    return json_list


def ts_attributes_to_dict(ts):
    """ Convert a :py:class:`TimeSeries` ``ts_attributes`` element into a dict.

    Parameters
    ----------
    ts: :py:class:`TimeSeries`
        Time series.

    Returns
    -------
    dict
        Dictionary ready to be written in MongoDB.
    """
    attributes = ts.ts_attributes.copy()
    components = attributes.get(COMPONENTS, None)
    if components:
        components = components.copy()
        attributes[COMPONENTS] = dict()
        for key, value in components.items():
            if isinstance(value, TimeSeries):
                attributes[COMPONENTS][key] = value.ts_name
            elif isinstance(value, str):
                pass
            else:
                raise ValueError('{} has a component that is neither a TimeSeries nor a string'.format(ts.ts_name))
    return attributes


def ts_values_to_dict(ts):
    """ Convert a :py:class:`TimeSeries` ``ts_values`` element into a dict.

    Parameters
    ----------
    ts: :py:class:`TimeSeries`
        Time series.

    Returns
    -------
    dict
        Dictionary ready to be written in MongoDB.
    """
    values = ts.ts_values.copy()
    values = values.to_json()
    values = json.loads(values)
    return values


def instantiate_components(ts, components, ts_collection):
    """ Convert inplace the string values in the 'Components' dict of a time series into time series objects.

    Also stores these components in a given time series collection.

    Parameters
    ----------
    ts: :py:class:`TimeSeries`
        Time series.
    components: list(str)
        List of component names to instantiate (keys of the 'Components' dict).
    ts_collection: :py:class:`TimeSeriesCollection`
        A time series collection to store the instantiated components.
    """
    if isinstance(ts, TimeSeries):
        if components:
            if isinstance(components, list):
                ts_components = ts.get_attribute(COMPONENTS)
                if ts_components:
                    for key, value in ts_components.items():
                        if key in components:
                            new_ts = TimeSeries(value)
                            ts_components[key] = new_ts
                            ts_collection.add(new_ts)
            elif components is True:
                ts_components = ts.get_attribute(COMPONENTS)
                if ts_components:
                    for key, value in ts_components.items():
                        new_ts = TimeSeries(value)
                        ts_components[key] = new_ts
                        ts_collection.add(new_ts)


class DBIO:
    """ Class for reading/writing time series in MongoDB.

    Parameters
    ----------
    host_address: str
        Address of the MongoDB daemon.
    db_name: str
        MongoDB database name.
    collection_name: str
        MongoDB collection.
    """
    def __init__(self, host_address, db_name, collection_name):
        self.host_address = host_address
        self.db_name = db_name
        self.collection_name = collection_name
        self.db = pymongo.MongoClient(self.host_address)[self.db_name][self.collection_name]

    def read_attributes(self, ts_collection, components=True, depth=np.inf, attributes=None):
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
        """
        if isinstance(components, list):
            components = [key.upper() for key in components]
        if attributes and attributes is not True:
            attr_specs = dict()
            attr_specs[TS_NAME] = 1
            for attr in attributes:
                try:
                    attr = attr.upper()
                except:
                    pass
                attr_specs[attr] = 1
        else:
            attr_specs = {TS_VALUES: 0}

        temp_ts_collection = convert_to_ts_collection(ts_collection)
        counter = 0
        all_names_list = list()

        while counter < depth:
            ts_collection = temp_ts_collection
            names_list = ts_collection.ts_names()
            if not names_list:
                break
            query_bulk_result = list(self.db.find({TS_NAME: {IN: names_list}}, attr_specs))
            all_names_list += names_list
            temp_ts_collection = TimeSeriesCollection()
            counter += 1
            for result in query_bulk_result:
                ts = ts_collection.get(result[TS_NAME])
                if isinstance(ts, TimeSeries):
                    del result[TS_NAME]
                    del result[ID]
                    ts.update_attributes(result)
                    if counter < depth:
                        instantiate_components(ts, components, temp_ts_collection)

        # Now updating LAST_USE attribute for the requested TimeSeries
        self.db.update_many({TS_NAME: {IN: all_names_list}},
                            {SET: {LAST_USE: datetime.datetime.utcnow()}})

    def read_values(self, ts_collection, components=True, depth=np.inf):
        """ Read time series values from the database.

        Parameters
        ----------
        ts_collection: type convertible to :py:class:`TimeSeriesCollection`
            Time series to be read.
        components: list(str), optional
            Optional collection of component names to be read and instantiated. Default is all components.
        depth: int, optional
            Depth of component instantiation. ``depth = 1`` means no components are instantiated. Default is infinity.
        """
        if isinstance(components, list):
            components = [key.upper() for key in components]

        temp_ts_collection = convert_to_ts_collection(ts_collection)
        counter = 0
        all_names_list = list()

        while counter < depth:
            ts_collection = temp_ts_collection
            names_list = ts_collection.ts_names()
            if not names_list:
                break
            query_bulk_result = list(self.db.find({TS_NAME: {IN: names_list}}, {TS_NAME: 1, TS_VALUES: 1}))
            all_names_list += names_list
            temp_ts_collection = TimeSeriesCollection()
            counter += 1
            for result in query_bulk_result:
                if result and TS_VALUES in result:
                    ts = ts_collection.get(result[TS_NAME])
                    if isinstance(ts, TimeSeries):
                        new_values = pd.Series(result[TS_VALUES])
                        new_values.index = pd.to_datetime(new_values.index, unit='ms', errors='coerce')
                        ts.update_values(new_values)
                        if counter < depth:
                            instantiate_components(ts, components, temp_ts_collection)

    def read(self, ts_collection, components=True, depth=np.inf):
        """ Read time series attributes and values from the database.

        Parameters
        ----------
        ts_collection: type convertible to :py:class:`TimeSeriesCollection`
            Time series to be read.
        components: list(str), optional
            Optional collection of component names to be read and instantiated. Default is all components.
        depth: int, optional
            Depth of component instantiation. ``depth = 1`` means no components are instantiated. Default is infinity.
        """
        if isinstance(components, list):
            components = [key.upper() for key in components]

        temp_ts_collection = convert_to_ts_collection(ts_collection)
        counter = 0
        all_names_list = list()
        while counter < depth:
            ts_collection = temp_ts_collection
            names_list = ts_collection.ts_names()
            if not names_list:
                break
            query_bulk_result = list(self.db.find({TS_NAME: {IN: names_list}}))
            all_names_list += names_list
            temp_ts_collection = TimeSeriesCollection()
            counter += 1
            new_values_dict = dict()
            for result in query_bulk_result:
                ts = ts_collection.get(result[TS_NAME])
                if isinstance(ts, TimeSeries):
                    new_values_dict[TS_VALUES] = result[TS_VALUES]
                    del result[TS_VALUES]
                    del result[ID]
                    del result[TS_NAME]
                    ts.update_attributes(result)
                    new_values = pd.Series(new_values_dict[TS_VALUES])
                    new_values.index = pd.to_datetime(new_values.index, unit='ms', errors='coerce')
                    ts.update_values(new_values)
                    if counter < depth:
                        instantiate_components(ts, components, temp_ts_collection)

        # Now updating LAST_USE attribute for the requested TimeSeries
        self.db.update_many({TS_NAME: {IN: all_names_list}},
                            {SET: {LAST_USE: datetime.datetime.utcnow()}})

    def write_attributes(self, ts_collection, components=True, depth=np.inf):
        """ Write time series attributes to the database.

        Parameters
        ----------
        ts_collection: type convertible to :py:class:`TimeSeriesCollection`
            Time series to be written.
        components: list(str), optional
            Optional collection of component names to be written. Default is all components.
        depth: int, optional
            Depth of component writing. ``depth = 1`` means no components are written. Default is infinity.
        """
        if isinstance(components, list):
            components = [key.upper() for key in components]
        temp_ts_collection = convert_to_ts_collection(ts_collection)
        counter = 0
        full_ts_collection = TimeSeriesCollection()
        while counter < depth:
            ts_collection = temp_ts_collection
            names_list = ts_collection.ts_names()
            if not names_list:
                break
            full_ts_collection.add_list(ts_collection)
            counter += 1
            temp_ts_collection = TimeSeriesCollection()
            for result in names_list:
                ts = ts_collection.get(result)
                if isinstance(ts, TimeSeries) and counter < depth:
                    instantiate_components(ts, components, temp_ts_collection)

        documents = ts_to_dict(full_ts_collection)
        if documents:
            bulkop = self.db.initialize_ordered_bulk_op()
            for document in documents:
                for key in document:  # Some fine tuning in encoding. e.g. MongoDB does not accept numpy.int64.
                    try:
                        if np.issubdtype(document[key], np.signedinteger):
                            document[key] = document[key].item()
                    except:
                        pass
                try:
                    # Remove values from the document, we are only updating the attributes
                    del document[TS_VALUES]
                except:
                    pass

                bulkop.find({TS_NAME: document[TS_NAME]}).upsert().update({SET: document})

            try:
                return bulkop.execute()
            except BulkWriteError as bwe:
                print(bwe.details)
                werrors = bwe.details['writeErrors']
                input(werrors)
                raise

    def write(self, ts_collection, components=True, depth=np.inf):
        """ Write time series attributes and values to the database.

        Parameters
        ----------
        ts_collection: type convertible to :py:class:`TimeSeriesCollection`
            Time series to be written.
        components: list(str), optional
            Optional collection of component names to be written. Default is all components.
        depth: int, optional
            Depth of component writing. ``depth = 1`` means no components are written. Default is infinity.
        """
        if isinstance(components, list):
            components = [key.upper() for key in components]

        temp_ts_collection = convert_to_ts_collection(ts_collection)
        to_updating_collection_names = temp_ts_collection.ts_names()[:]

        if len(to_updating_collection_names) >= 1000:
            new_ts_collection = TimeSeriesCollection(temp_ts_collection)
            temp_ts_collection.remove_list(to_updating_collection_names[998:])
            new_ts_collection.remove_list(to_updating_collection_names[:998])
            self.write(new_ts_collection, components, depth)

        counter = 0
        full_ts_collection = TimeSeriesCollection()

        while counter < depth:
            ts_collection = temp_ts_collection
            names_list = ts_collection.ts_names()
            if not names_list:
                break
            full_ts_collection.add_list(ts_collection)
            counter += 1
            temp_ts_collection = TimeSeriesCollection()
            for result in names_list:
                ts = ts_collection.get(result)
                if isinstance(ts, TimeSeries) and counter < depth:
                    instantiate_components(ts, components, temp_ts_collection)

        documents = ts_to_dict(full_ts_collection)
        if documents:
            bulkop = self.db.initialize_ordered_bulk_op()
            for document in documents:
                for key in document:  # Some fine tuning in encoding. e.g. MongoDB does not accept numpy.int64.
                    try:
                        if np.issubdtype(document[key], np.signedinteger):
                            document[key] = document[key].item()
                    except:
                        pass
                    if pd.isnull(document[key]):
                        document[key] = None
                bulkop.find({TS_NAME: document[TS_NAME]}).upsert().update({SET: document})

            try:
                retval = bulkop.execute()
                return retval
            except BulkWriteError as bwe:
                warnings.warn(bwe.details)
                raise bwe

    def remove(self, ts_collection, components=False, depth=np.inf, confirm=True):
        """ Remove time series from the database.

        Parameters
        ----------
        ts_collection: type convertible to :py:class:`TimeSeriesCollection`
            Time series to be removed.
        components: list(str), optional
            Optional collection of component names to be removed. Default is no components.
        depth: int, optional
            Depth of component removal. ``depth = 1`` means no components are removed. Default is 1.
        confirm: bool, optional
            Confirm before removing. Default is True.
        """
        if isinstance(components, list):
            components = [key.upper() for key in components]
        ts_collection = convert_to_ts_collection(ts_collection)
        counter = 0
        full_ts_collection = TimeSeriesCollection()
        while counter < depth:
            names_list = ts_collection.ts_names()
            if not names_list:
                break
            full_ts_collection.add_list(ts_collection)
            counter += 1
            ts_collection = TimeSeriesCollection()
            for result in names_list:
                ts = full_ts_collection.get(result)
                if isinstance(ts, TimeSeries):
                    instantiate_components(ts, components, ts_collection)

        names_to_delete = full_ts_collection.ts_names()
        if confirm:
            while True:
                ans = input('Are you sure you want to delete {0} TimeSeries from the {1} database? \n '
                            '[(y) (n) (l)]'.format(len(names_to_delete), self.collection_name))
                ans = ans.lower()
                if ans == 'l':
                    print(names_to_delete)
                elif ans == 'n':
                    print("Aborting 'remove' operation.")
                    return
                elif ans == 'y':
                    break
        if names_to_delete:
            return list(self.db.remove({TS_NAME: {IN: names_to_delete}}))

    def attribute_names(self, ts_names=None):
        """ Return set of attribute names in the database.

        Parameters
        ----------
        ts_names: list(str), optional
            Optional list of time series names to be used for searching attributes. Default is None (use the entire
            database).

        Returns
        -------
        list(str)
            All the attribute names in `ts_names` or in the database.
        """
        all_attributes = set()

        if not ts_names:
            all_docs = self.db.find()
        else:
            all_docs = self.db.find({TS_NAME: {IN: ts_names}}, {TS_VALUES: 0})

        for doc in all_docs:
            all_attributes.update(doc.keys())
        all_attributes = sorted(list(all_attributes))
        all_attributes = [x for x in all_attributes if x not in RESERVED_KEYS]
        return all_attributes

    def read_all_attribute_values(self, attributes=None):
        """ Return set of attribute values in the database.

        Parameters
        ----------
        attributes: list(str), optional
            Attribute names whose values are to be retrieved. Default is None (use all attribute names in the database).

        Returns
        -------
        list(str)
            All the attribute values of ``attributes`` or of all the attribute names in the database.
        """
        if attributes is None:
            attributes = self.attribute_names()
        try:
            attributes.remove(TS_VALUES)
        except:
            pass
        try:
            attributes.remove(COMPONENTS)
        except:
            pass
        all_values = []
        for attribute in attributes:
            all_values.extend(self.db.distinct(attribute))
        all_values = sorted(all_values)
        return all_values

    def in_db(self, ts):
        """ Check if a time series is in the database.

        Parameters
        ----------
        ts: :py:class:`TimeSeries`

        Returns
        -------
        bool
            Whether there is a time series with the same name in the database.
        """
        found_entry = self.db.find({TS_NAME: ts.ts_name}, {ID: 1}).count()
        if found_entry > 0:
            return True
        else:
            return False

    def select(self, **kwargs):
        """ Get time series names matching attribute specifications.

        Parameters
        ----------
        kwargs: dict, optional
            Dictionary of ``{attribute_name: attribute_value}`` pairs to match.

        Note
        ----
        * Use ``MODE={"OR", "AND"}`` to choose whether to match attributes with "AND" or "OR". Default is "AND".
        * Use ``AVAILABLE_DATES=list(date-like)`` to return only names of time series that have values at a set of
        dates.
        * Use ``ALL_FIELDS=True`` to choose whether to return time series with the "FIELD" attribute. The default
        behaviour is to not return these time series.

        Returns
        -------
        list(str)
            Names of time series matching the passed specifications.
        """
        # Loads entire DB, all timeseries (only with names and attributes) and selects by attributes given in arguments.
        # EXCLUSIVE = 'NO' means it will keep timeseries that do not have one of the attributes. MODE= 'AND'
        # means it will keep only the timeseries with attributes matching all those given.
        kwargs = {str(key).upper(): to_list(value) for key, value in kwargs.items()}

        mode = kwargs.pop("MODE", "AND")
        all_fields = kwargs.pop("ALL_FIELDS", False)
        # available_dates = kwargs.pop("AVAILABLE_DATES", None)
        available_dates = kwargs.pop("AVAILABLE", None)

        if FIELD not in kwargs and not all_fields:
            kwargs[FIELD] = [None]

        if mode.upper() in OR_VALUES:
            filtered_collection = self.db.find({OR: [{i: {IN: list(v)}} for i, v in kwargs.items()]},
                                               {TS_NAME: 1})
        elif mode.upper() in AND_VALUES:
            filtered_collection = self.db.find({AND: [{i: {IN: list(v)}} for i, v in kwargs.items()]},
                                               {TS_NAME: 1})
        else:
            filtered_collection = self.db.find({}, {TS_NAME: 1})

        new_collection = TimeSeriesCollection()
        for doc in filtered_collection:
            new_collection.add(doc[TS_NAME])

        if available_dates is not None:
            available_date = list(map(pd.to_datetime, available_dates))
            self.read_values(new_collection)
            new_collection = TimeSeriesCollection([ts for ts in new_collection if
                                                   bool(set(available_date) & set(ts.ts_values.index))])

        return new_collection

    def search(self, **kwargs):
        """ This method is not yet implemented.
        """
        # TODO: Implement this method.
        raise NotImplementedError("The 'search' method is not yet implemented. Use the 'select' to get all TimeSeries "
                                  "in the DataBase and search the resulting collection.")

    def ensure_index(self, attributes):
        """ Create database index for an attribute.

        Useful to improve performance of attribute matching with the ``select`` method.

        Parameters
        ----------
        attributes: list(str)
            Attribute names for index creation.
        """
        report = dict()
        for attribute in attributes:
            report[attribute] = self.db.create_index(attribute)
        return report
