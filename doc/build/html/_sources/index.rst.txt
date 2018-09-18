
Time Series I/O Documentation
=============================


Description
-----------

This is the documentation page of the Time Series I/O project. For installation instructions, see the `project's
GitHub page <https://github.com/LANXDEV/tsio>`_.

This project is a Python library implementing a basic Time Series object model and tools for reading/writing Time Series
objects using a MongoDB instance.


Contents
--------
.. toctree::
    :maxdepth: 1

    tsio/tsio.timeseries
    tsio/tsio.timeseriescollection
    tsio/tsio.io.db
    tsio/tsio.io.gen


Examples
--------

Creating a simple TimeSeries object::

   import pandas as pd
   from tsio import TimeSeries
   ts = TimeSeries("Example Time Series")
   ts.set_attribute("Example_Attribute", "Example_Attribute_Value")
   example_values = pd.Series(index=list(map(pd.to_datetime, ['2018-01-01', '2018-01-02', '2018-01-03'])),
                              data=[1, 2, 3],
                              )
   ts.update_values(example_values)
   print(ts)


Indices and Tables:
-------------------
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
