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
from tsio.constants import COMPONENTS, TS_NAME, TS_VALUES, LAST_USE, RESERVED_KEYS, OR, AND, FIELD
from tsio.tools import to_list
from tsio.timeseries import TimeSeries
from tsio.timeseriescollection import TimeSeriesCollection


def convert_to_ts_collection(ts):
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


def ts_to_dict(arg):
    json_list = list()
    ts_collection = convert_to_ts_collection(arg)
    for ts in ts_collection:
        entry = ts_attributes_to_dict(ts)
        entry[TS_NAME] = ts.ts_name
        entry[TS_VALUES] = ts_values_to_dict(ts)
        json_list.append(entry)
    return json_list


def ts_attributes_to_dict(ts):
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


def ts_values_to_dict(timeseries):
    """
    :param timeseries:
    :return:
    """
    values = timeseries.ts_values.copy()
    values = values.to_json()
    values = json.loads(values)
    return values


def instantiate_components(ts, components, ts_collection):
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
    def __init__(self, host_address, db_name, collection_name):
        self.host_address = host_address
        self.db_name = db_name
        self.collection_name = collection_name
        self.db = pymongo.MongoClient(self.host_address)[self.db_name][self.collection_name]

    def read_attributes(self, ts_collection, components=True, depth=np.inf, attributes=None):
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
            query_bulk_result = list(self.db.find({TS_NAME: {"$in": names_list}}, attr_specs))
            all_names_list += names_list
            temp_ts_collection = TimeSeriesCollection()
            counter += 1
            for result in query_bulk_result:
                ts = ts_collection.get(result[TS_NAME])
                if isinstance(ts, TimeSeries):
                    del result[TS_NAME]
                    del result['_id']
                    ts.update_attributes(result)
                    if counter < depth:
                        instantiate_components(ts, components, temp_ts_collection)

        # Now updating LAST_USE attribute for the requested TimeSeries
        self.db.update_many({TS_NAME: {"$in": all_names_list}},
                            {'$set': {LAST_USE: datetime.datetime.utcnow()}})

    def read_values(self, ts_collection, components=True, depth=np.inf):
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
            query_bulk_result = list(self.db.find({TS_NAME: {"$in": names_list}}, {TS_NAME: 1, TS_VALUES: 1}))
            all_names_list += names_list
            temp_ts_collection = TimeSeriesCollection()
            counter += 1
            for result in query_bulk_result:
                if result and TS_VALUES in result:
                    ts = ts_collection.get(result[TS_NAME])
                    if isinstance(ts, TimeSeries):
                        new_values = pd.Series(result[TS_VALUES])
                        new_values.index = pd.to_datetime(new_values.index.values, unit='ms', errors='coerce')
                        ts.update_values(new_values)
                        if counter < depth:
                            instantiate_components(ts, components, temp_ts_collection)

    def read(self, ts_collection, components=True, depth=np.inf):
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
            query_bulk_result = list(self.db.find({TS_NAME: {"$in": names_list}}))
            all_names_list += names_list
            temp_ts_collection = TimeSeriesCollection()
            counter += 1
            new_values_dict = dict()
            for result in query_bulk_result:
                ts = ts_collection.get(result[TS_NAME])
                if isinstance(ts, TimeSeries):
                    new_values_dict[TS_VALUES] = result[TS_VALUES]
                    del result[TS_VALUES]
                    del result['_id']
                    del result[TS_NAME]
                    ts.update_attributes(result)
                    new_values = pd.Series(new_values_dict[TS_VALUES])
                    new_values.index = pd.to_datetime(new_values.index.values, unit='ms', errors='coerce')
                    ts.update_values(new_values)
                    if counter < depth:
                        instantiate_components(ts, components, temp_ts_collection)

        # Now updating LAST_USE attribute for the requested TimeSeries
        self.db.update_many({TS_NAME: {"$in": all_names_list}},
                            {'$set': {LAST_USE: datetime.datetime.utcnow()}})

    def write_attributes(self, ts_collection, components=True, depth=np.inf):
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
                        if np.issubdtype(document[key], int):
                            document[key] = np.asscalar(document[key])
                    except:
                        pass
                try:
                    # Remove values from the document, we are only updating the attributes
                    del document[TS_VALUES]
                except:
                    pass

                bulkop.find({TS_NAME: document[TS_NAME]}).upsert().update({'$set': document})

            try:
                return bulkop.execute()
            except BulkWriteError as bwe:
                print(bwe.details)
                werrors = bwe.details['writeErrors']
                input(werrors)
                raise

    def write(self, ts_collection, components=True, depth=np.inf):
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
                        if np.issubdtype(document[key], int):
                            document[key] = np.asscalar(document[key])
                    except:
                        pass
                    if pd.isnull(document[key]):
                        document[key] = None
                bulkop.find({TS_NAME: document[TS_NAME]}).upsert().update({'$set': document})

            try:
                retval = bulkop.execute()
                return retval
            except BulkWriteError as bwe:
                warnings.warn(bwe.details)
                raise bwe

    def remove(self, ts_collection, components=False, depth=np.inf, confirm=True):
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
            return list(self.db.remove({TS_NAME: {"$in": names_to_delete}}))

    def attribute_names(self, ts_names=None):
        all_attributes = set()

        if not ts_names:
            all_docs = self.db.find()
        else:
            all_docs = self.db.find({TS_NAME: {"$in": ts_names}}, {TS_VALUES: 0})

        for doc in all_docs:
            all_attributes.update(doc.keys())
        all_attributes = sorted(list(all_attributes))
        all_attributes = [x for x in all_attributes if x not in RESERVED_KEYS]
        return all_attributes

    def read_all_attribute_values(self, attributes=None):
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
        found_entry = self.db.find({TS_NAME: ts.ts_name}, {"_id": 1}).count()
        if found_entry > 0:
            return True
        else:
            return False

    def select(self, mode=AND, available_dates=None, all_fields=False, **kwargs):
        # Loads entire DB, all timeseries (only with names and attributes) and selects by attributes given in arguments.
        # EXCLUSIVE = 'NO' means it will keep timeseries that do not have one of the attributes. MODE= 'AND'
        # means it will keep only the timeseries with attributes matching all those given.
        kwargs = {str(key).upper(): to_list(value) for key, value in kwargs.items()}
        if FIELD not in kwargs and not all_fields:
            kwargs[FIELD] = [None]
        if mode.upper() == OR:
            filtered_collection = self.db.find({'$or': [{i: {'$in': list(v)}} for i, v in kwargs.items()]},
                                               {TS_NAME: 1})
        elif mode.upper() == AND:
            filtered_collection = self.db.find({'$and': [{i: {'$in': list(v)}} for i, v in kwargs.items()]},
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
        # TODO: Implement this method.
        raise NotImplementedError("The 'search' method is not yet implemented. Use the 'select' to get all TimeSeries "
                                  "in the DataBase and search the resulting collection.")

    def ensure_index(self, attributes):
        report = dict()
        for attribute in attributes:
            report[attribute] = self.db.create_index(attribute)
        return report
