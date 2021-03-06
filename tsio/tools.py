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
Miscellaneous tools.
"""
import os
from datetime import datetime
import numpy as np
import pandas as pd


def create_folder(address):
    while not os.path.exists(address):
        # Making a path to store the result files if it does not exist already
        try:
            os.makedirs(address)
        except:
            print('create_folder: is trying to create folders ({}), but not successful.. Retrying.'.format(address))


def is_iterable(obj):
    """
    Are we being asked to look up a list of things, instead of a single thing?
    We check for the `__iter__` attribute so that this can cover types that
    don't have to be known by this module, such as NumPy arrays.
    Strings, however, should be considered as atomic values to look up, not
    iterables. The same goes for tuples, since they are immutable and therefore
    valid entries.
    We don't need to check for the Python 2 `unicode` type, because it doesn't
    have an `__iter__` attribute anyway.
    """
    return hasattr(obj, '__iter__') and not isinstance(obj, str) and not isinstance(obj, tuple)


def isnull(arg):
    """Check if argument is 'reasonably null'.

    'reasonably null' includes: None, empty string, empty list, list with empty strings, np.nan, pd.NaT, etc.

    Parameters
    ----------
    arg

    Returns
    -------
    bool

    """
    if isinstance(arg, pd.DataFrame) or isinstance(arg, pd.Series):
        return arg.empty
    null_list = [False, None, [None], '', []]
    null_list += [i * ' ' for i in range(0, 30)]
    try:
        if arg in null_list:
            return True
    except:
        pass
    try:
        result = pd.isnull(arg)
        if is_iterable(result):
            return result.all()
        else:
            return result
    except:
        pass
    try:
        result = np.isnan(arg)
        if is_iterable(result):
            return result.all()
        else:
            return result
    except:
        pass
    return False


def isvectorizable(obj):
    """Check if object is numpy.vectorize-vectorizable.

    Parameters
    ----------
    obj

    Returns
    -------
    bool

    """
    return hasattr(obj, '__iter__') and \
        not isinstance(obj, (str, datetime, np.datetime64)) and \
        not hasattr(obj, "dayOfMonth")  # In case of QuantLib date types.


def to_list(arg):
    """Make the object iterable in a 'reasonable way'.

    'reasonable' means:
        If the object is a string, tuple or dict, return [object].
        If the object has no __iter__ method, return [object].
        If the object has an __iter__ method, return object (unchanged).

    Parameters
    ----------
    arg: object
        The argument to be transformed into an iterable.

    Returns
    -------
    iterable object

    """
    if hasattr(arg, '__iter__') and not isinstance(arg, str) and not isinstance(arg, tuple) and not isinstance(arg,
                                                                                                               dict):
        return arg
    else:
        return [arg]


def to_upper_list(arg):
    """Convert a string or list of strings in upper-case list of strings.

    Parameters
    ----------
    arg: str or list-like of str.

    Returns
    -------
    list

    """
    if isinstance(arg, str):
        return [arg.upper()]
    else:
        return [x.upper() for x in arg]


def to_lower_list(arg):
    """Convert a string or list of strings in lower-case list of strings.

    Parameters
    ----------
    arg: str or list-like of str.

    Returns
    -------
    list

    """
    if isinstance(arg, str):
        return [arg.lower()]
    else:
        return [x.lower() for x in arg]


def to_datetime(arg):
    """Converts a QuantLib.Date instance to datetime.datetime instance.

    Parameters
    ----------
    arg: date-like

    Returns
    -------
    datetime.datetime

    """
    if isvectorizable(arg):
        try:
            # Works if all elements in arg are QuantLib.Date objects.
            return [datetime(day=arg_n.dayOfMonth(), month=arg_n.month(), year=arg_n.year()) for arg_n in arg]
        except AttributeError:
            return pd.to_datetime(arg)
    else:
        # arg is not vectorizable.
        if isinstance(arg, datetime):
            return arg
        else:
            try:
                # Works if arg is a ql.Date object.
                return datetime(day=arg.dayOfMonth(), month=arg.month(), year=arg.year())
            except AttributeError:
                return pd.to_datetime(arg)


def at_index(df, index, last_available=True, fill_value=np.nan):
    """Get value of Series at date if possible, otherwise get last available data.

    Parameters
    ----------
    df: pandas.Series
        The Series to filter the index.
    index: type of index elements in `df`.
        The requested index to fetch from `df`.
    last_available: bool, optional
        Whether to use last available information if there is missing data in `df`.
    fill_value: scalar or numpy.nan, optional
        If last_available is False or there is no data in df before 'date', returns this default value.

    Returns
    -------
    scalar

    """
    index_as_list = to_list(index)
    if last_available:
        result = df.reindex(index_as_list, method='pad', fill_value=fill_value).values
    else:
        result = df.reindex(index_as_list, fill_value=fill_value)[index_as_list].values
    if not isvectorizable(index):
        return result[0]
    return result


def filter_series(df, initial_date=None, final_date=None):
    """Filter (inplace) a Series/DataFrame DatetimeIndex to keep only dates that are between two dates.

    Parameters
    ----------
    df: pandas.Series, pandas.DataFrame
    initial_date: datetime.datetime, optional
    final_date: datetime.datetime, optional

    """

    if initial_date is None and final_date is not None:
        final_date = pd.to_datetime(final_date)
        df.drop(df[(df.index > final_date)].index, inplace=True)
    elif final_date is None and initial_date is not None:
        initial_date = pd.to_datetime(initial_date)
        df.drop(df[(df.index < initial_date)].index, inplace=True)
    elif final_date is None and initial_date is None:
        pass
    elif initial_date == final_date:
        initial_date = pd.to_datetime(initial_date)
        df.drop(df[(df.index != initial_date)].index, inplace=True)
    else:
        initial_date = pd.to_datetime(initial_date)
        final_date = pd.to_datetime(final_date)
        df.drop(df[(df.index < initial_date) | (df.index > final_date)].index, inplace=True)

