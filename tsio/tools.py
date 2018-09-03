"""
Miscellaneous independent tools.
"""
from datetime import datetime
import numpy as np
import pandas as pd


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
    index = to_list(index)
    if last_available:
        return df.reindex(index, method='pad', fill_value=fill_value).values()
    return df.reindex(index, fill_value=fill_value)[index].values()
