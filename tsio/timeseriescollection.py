"""
A TimeSeriesCollection is is an 'Ordered Set' of objects with a 'ts_name' property.
Based on recipe of an ordered set (https://github.com/LuminosoInsight/ordered-set).

Copyright (c) 2018 Luminoso Technologies, Inc.

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import collections
from tsio.timeseries import TimeSeries

SLICE_ALL = slice(None)


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


class TimeSeriesCollection(collections.MutableSet):
    """ Custom ``OrderedSet`` for ``TimeSeries`` objects.

    This container remembers the order in which its members were added, so that every entry has a numeric index that
    can be looked up.
    """
    def __init__(self, iterable=None):
        self.items = []
        self.map = {}
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        """
        Get the item at a given index.
        If `index` is a slice, you will get back that slice of items. If it's
        the slice [:], exactly the same object is returned. (If you want an
        independent copy of an OrderedSet, use `OrderedSet.copy()`.)
        If `index` is an iterable, you'll get the OrderedSet of items
        corresponding to those indices. This is similar to NumPy's
        "fancy indexing".
        """
        if index == SLICE_ALL:
            return self
        elif hasattr(index, '__index__') or isinstance(index, slice):
            result = self.items[index]
            if isinstance(result, list):
                return TimeSeriesCollection(result)
            else:
                return result
        elif is_iterable(index):
            return TimeSeriesCollection([self.items[i] for i in index])
        else:
            raise TypeError("Don't know how to index a TimeSeriesCollection by %r" %
                            index)

    def __getstate__(self):
        if len(self) == 0:
            # The state can't be an empty list.
            # We need to return a truthy value, or else __setstate__ won't be run.
            return None
        else:
            return list(self)

    def __setstate__(self, state):
        if state == (None,):
            self.__init__([])
        else:
            self.__init__(state)

    def __contains__(self, key):
        try:
            key = key.ts_name
        except AttributeError:
            pass
        return key in self.map

    def __iter__(self):
        return iter(self.items)

    def __reversed__(self):
        return reversed(self.items)

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, TimeSeriesCollection):
            return len(self) == len(other) and self.items == other.items
        try:
            other_as_set = set(other)
        except TypeError:
            # If `other` can't be converted into a set, it's not equal.
            return False
        else:
            return set(self) == other_as_set

    def __str__(self):
        # returns all names of TimeSeries in self.items
        s = ""
        for ts in self.items:
            s += ts.ts_name + "\n"
        return s

    def copy(self):
        """
        Returns
        -------
        TimeSeriesCollection
            A copy of this object.
        """
        return TimeSeriesCollection(self)

    def add(self, ts):
        """ Add `ts` and return its index.

        Parameters
        ----------
        ts: :py:class:`TimeSeries`
            A TimeSeries to add.

        Returns
        -------
        int, None
            Index of the added TimeSeries.

        Note
        ----
        If a TimeSeries with the same ``ts_name`` is already in the container, the method does not modify the
        TimeSeriesCollection and returns the index associated with the previously existing TimeSeries.
        """
        # ts may be a string with a name or a any object with a .ts_name attribute
        if is_iterable(ts):
            return [self.add(i) for i in ts]
        else:
            try:
                # If the argument can by whatever means retrieve a ts_name attribute, then just add it to the list
                object_name = ts.ts_name
                object_to_add = ts
            except AttributeError:
                # If the argument has no ts_name attribute, we generate a TimeSeries from it
                object_name = ts
                object_to_add = TimeSeries(ts)
            if object_name not in self.map:
                self.map[object_name] = len(self.items)
                self.items.append(object_to_add)
            return self.map[object_name]
    append = add

    def add_list(self, iterable):
        """ Add iterable of elements.

        Parameters
        ----------
        iterable: list of str, :py:class:`TimeSeries`
            Elements to add.
        """
        for ts in iterable:
            self.add(ts)

    def update(self, sequence):
        """ Update `self` with the given iterable.

        Parameters
        ----------
        sequence: iterable of :py:class:`TimeSeries`
            Elements to add.

        Returns
        -------
        int
            Index of the last inserted element.
        """
        item_index = None
        try:
            for item in sequence:
                item_index = self.add(item)
        except TypeError:
            raise ValueError('Argument needs to be an iterable, got %s' % type(sequence))
        return item_index

    def index(self, key):
        """
        Parameters
        ----------
        key: iterable of str or :py:obj:`TimeSeries`
            Element to be looked for.

        Returns
        -------
        int, list of int
            Index(es) of the given entry(ies).
        """
        if is_iterable(key):
            return [self.index(subkey) for subkey in key]
        try:
            key = key.ts_name
        except AttributeError:
            pass
        return self.map[key]

    def pop(self):
        """Pops the last-added element.

        Returns
        -------
        :py:class:`TimeSeries`
            The popped TimeSeries.
        """
        if not self.items:
            raise KeyError('Set is empty')

        elem = self.items[-1]
        del self.items[-1]
        del self.map[elem.ts_name]
        return elem

    def discard(self, ts):
        """ Discard an element.  Does not raise an exception if absent.

        Parameters
        ----------
        ts: :py:class:`TimeSeries`, str
            Element to be discarded.
        """
        try:
            object_to_remove_name = ts.ts_name
            object_to_remove = ts
        except AttributeError:
            object_to_remove_name = ts
            object_to_remove = TimeSeries(ts)
        if object_to_remove in self:
            i = self.map[object_to_remove_name]
            del self.items[i]
            del self.map[object_to_remove_name]
            for k, v in self.map.items():
                if v >= i:
                    self.map[k] = v - 1

    def remove(self, ts):
        return self.discard(ts)

    def remove_list(self, iterable):
        """ Discard an iterable of elements.

        Parameters
        ----------
        iterable: iterable of str, :py:class:`TimeSeries`
            Elements to be discarded.
        """
        for ts in iterable:
            self.remove(ts)

    def clear(self):
        """ Remove all items.
        """
        del self.items[:]
        self.map.clear()

    def ts_names(self):
        """
        Returns
        -------
        list of str
            Names of the contained TimeSeries.
        """
        # returns list with names of all timeseries in the collection
        return [ts.ts_name for ts in self.items]

    def ts_attributes(self):
        """
         Returns
         -------
         list of dict
            ``ts_attributes`` of the contained TimeSeries.
         """
        return [ts.ts_attributes for ts in self.items]

    def ts_values(self):
        """
         Returns
         -------
         list of pandas.Series
             List of ``ts_values`` of the contained TimeSeries.
         """
        return [ts.ts_values for ts in self.items]

    def get(self, name):
        """
        Parameters
        ----------
        name: str
            Name of the element.

        Returns
        -------
        :py:class:`TimeSeries`
            Reference to an element in the container.
        """
        #  return reference to element with given name
        try:
            return self.items[self.map[name]]
        except KeyError:
            raise KeyError("This TimeSeriesCollection doesn't have an element with this name!!!: {}".format(name))

    def get_attributes(self, field):
        """
        Parameters
        ----------
        field: str
            The field whose values are to be retrieved.

        Returns
        -------
        list of objects
            attribute values of the contained TimeSeries.
        """
        return [ts.get_attribute(field) for ts in self.items]
