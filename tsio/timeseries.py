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

# You should have received a copy of the GNU Lesser General Public License
# along with Time Series I/O (tsio). If not, see <https://www.gnu.org/licenses/>.
"""
TimeSeries class, a basic data-holder.
"""
import copy
from pprint import pformat
import numpy as np
import pandas as pd
from tsio.constants import COMPONENTS
from tsio.tools import at_index, to_datetime

_components = COMPONENTS.lower()


class TimeSeries:
    """Object representing a time series.

    Parameters
    ----------
    timeseries: str, :py:class:`TimeSeries`
        A name or a TimeSeries object.

    Attributes
    ----------
    ts_name: str
        The name of the time series.

    ts_attributes: dict
        A dictionary of ``{str: attribute_value}``. ``attribute_value`` can be any object that is serializable by
        PyMongo's ``json_util`` tool.

    ts_values: pandas.Series
        Series containing the (``datetime``, ``scalar``) pairs of the time series.

    Note
    ----
    | **Names:**
    | The ``ts_name`` attribute serves as the unique identifier for the time series in the
    | database and in time series `containers` (:py:class:`TimeSeriesCollection`).
    | Keeping different ``TimeSeries`` with the same name is not supported.
    |
    | `Suggested name patterns:`
    | ``"(name)(field)"``: For time series that have a field (e.g. "price", "quote", "rating").
    | ``"name"``: For time series that have no fields.
    |
    | **Components:**
    | The attribute key ``"COMPONENTS"`` in ``ts_attributes`` is treated specially.
    | The value of this attribute must be a dict of  ``{component_type: component}``,
    | where ``component_type`` is the type of the component (e.g.: ``"QUOTE"``,
    | ``"CALL_SCHEDULE"``, ``"DIVIDEND_SCHEDULE"``), and ``component`` is the name
    | of a ``TimeSeries`` (e.g.: ``"(TS_NAME)(QUOTE)"``, ``"(TS_NAME)(CALL_SCHEDULE)"``,
    | ``"(TS_NAME)(DIVIDEND_SCHEDULE)"``).
    |
    | When reading a ``TimeSeries`` from the database, the library knows that it should
    | also read the components as ``TimeSeries`` objects. This is useful to store instruments
    | that need many different ``TimeSeries`` in order to be well-defined.
    | For example, a callable bond needs at least a ``quote`` and ``call_schedule``
    | time series to be well defined.
    |
    | The library doesn't enforce any of the above naming conventions, except
    | the special treatment of the ``"COMPONENTS"`` attribute.
    """
    def __init__(self, timeseries):
        if isinstance(timeseries, str):
            # initialize TimeSeries from a string.
            self.ts_name = timeseries
            self.ts_attributes = dict()
            # The attribute ts_values is not initialized here to improve performance. It is created on demand by
            # the __getattr__ method below.
        elif isinstance(timeseries, TimeSeries):
            # initialize TimeSeries from other TimeSeries - Copies by reference.
            self.ts_name = timeseries.ts_name
            self.ts_attributes = timeseries.ts_attributes
            self.ts_values = timeseries.ts_values
        else:
            raise ValueError('Could not create instance of TimeSeries with arguments: '
                             'time_series_arg={0}'.format(timeseries))

    def __eq__(self, other):
        # TimeSeries are compared using their names.
        try:
            return self.ts_name == other.ts_name
        except AttributeError:
            return False

    def __hash__(self):
        # TimeSeries are hashed through their names.
        return hash(self.ts_name)

    def __call__(self, *args, **kwargs):
        if args or kwargs:
            return self.get_values(*args, **kwargs)
        return self.ts_values

    def __getattr__(self, attr):
        if attr == 'ts_values':
            # If a request for ts_values attribute finishes in __getattr__, it means that ts_values is not an
            # attribute of the TimeSeries (i.e. the TimeSeries was initialized from a string).
            # Just create an empty ts_values then.
            self.ts_values = pd.Series()
            return self.ts_values
        if attr == _components:
            try:
                return self.ts_attributes[COMPONENTS]
            except KeyError:
                raise AttributeError("The TimeSeries {0} has no attribute '{1}'.".format(self.ts_name, attr))
        try:
            attr = attr.upper()
            return self.ts_attributes[COMPONENTS][attr]
        except KeyError:
            raise AttributeError("The TimeSeries {0} has no attribute '{1}'.".format(self.ts_name, attr))

    def __deepcopy__(self, memo):
        new_timeseries = TimeSeries(self.ts_name)
        new_timeseries.ts_attributes = copy.deepcopy(self.ts_attributes)
        new_timeseries.ts_values = copy.deepcopy(self.ts_values)
        return new_timeseries

    def __repr__(self):
        return "{} <TimeSeries>".format(self.ts_name)

    def __str__(self):
        return '='*20 + '\n' \
               + self.ts_name + '\n' \
               + '-'*20 + '\n' + \
               'ts_attributes:' + 2*'\n' \
               + str(pformat(self.ts_attributes)) + 2*'\n' \
               + '-'*20 + '\n' \
               + 'ts_values:' + 2*'\n' \
               + str(self.ts_values) + 2*'\n' \
               + '-' * 20 + '\n' \
               + '=' * 20 + '\n'

    def empty(self):
        """
        Returns
        -------
        bool
            True if both `ts_attributes` and `ts_values` are empty, False otherwise.
        """
        if not self.ts_attributes and self.ts_values.empty:
            return True
        else:
            return False

    def set_attribute(self, attribute_name, attribute_value):
        """Sets ``self.ts_attributes[attribute_name]`` to `attribute_value`.

        Parameters
        ----------
        attribute_name: str
            Name of the attribute to be set.
        attribute_value: object
            Value to set the attribute.
        """
        attribute_name = attribute_name.upper()
        self.ts_attributes[attribute_name] = attribute_value

    def set_attributes(self, attribute_dict):
        """Sets attributes of the TimeSeries according to data in `attribute_dict`.

        Parameters
        ----------
        attribute_dict: dict
            Attribute names (keys) and attribute values (values) to be set.
        """
        attribute_dict = {key.upper(): value for key, value in attribute_dict.items()}
        self.ts_attributes = attribute_dict

    def update_attributes(self, arg_attributes):
        """Updates `self.ts_attributes` with data in `arg_attributes`.

        Parameters
        ----------
        arg_attributes: dict
            Attribute names (keys) and attribute values (values) to be set.
        """
        arg_attributes = {key.upper(): value for key, value in arg_attributes.items()}
        self.ts_attributes.update(arg_attributes)

    def update_values(self, arg_values):
        """Updates ``self.ts_values`` with data in `arg_values`.

        Parameters
        ----------
        arg_values: pandas.Series, dict
            New dates and values.
        """
        if isinstance(arg_values, dict):
            arg_values = pd.Series(arg_values)
        arg_values.index = pd.to_datetime(arg_values.index)
        result = pd.concat([arg_values, self.ts_values])
        self.ts_values = result[~result.index.duplicated(keep='first')]
        self.ts_values.index = pd.to_datetime(self.ts_values.index)
        self.ts_values = self.ts_values.sort_index()
        self.ts_values = self.ts_values.dropna()

    '''
    Methods to get a TimeSeries object's attributes.
    '''
    def get_attribute(self, attribute_name, default=None):
        """
        Parameters
        ----------
        attribute_name: str
            Name of desired attribute.
        default: None
            The return value if `attribute_name` is not in ``self.ts_attributes``.

        Returns
        -------
        attribute_value: object
            Value of ``self.ts_attributes[attribute_name]`` if existing, otherwise `default`.
        """

        attribute_name = attribute_name.upper()
        return self.ts_attributes.get(attribute_name, default)

    def get_values(self, index, last_available=True, fill_value=np.nan):
        """
        Parameters
        ----------
        index: date-like
            Requested date(s).
        last_available: bool
            Whether to use last available data if `date` is missing in the quotes time series.
        fill_value: scalar
            Default value in case `date` can't be found.

        Returns
        -------
        scalar
            Value corresponding to `date`.
        """
        index = to_datetime(index)
        return at_index(df=self.ts_values, index=index, last_available=last_available, fill_value=fill_value)
