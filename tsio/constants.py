"""
Definition of some constants, used in the TimeSeries and the DB reading/writing classes.
TODO: Implement a good way to override these constants.
"""
COMPONENTS = "COMPONENTS"  # The key used to access the 'Components' dict of a TimeSeries object.
TS_NAME = 'TS_NAME'  # Attribute (in a MongoDB document) representing the ts_name if a TimeSeries.
TS_VALUES = 'VALUE'  # Attribute (in a MongoDB document) representing the ts_values of the TimeSeries.
IDENTIFIER = 'IDENTIFIER'
TYPE = 'TYPE'
LAST_USE = 'LAST_USE'  # Attribute for the last use date of a TimeSeries.
LAST_ATTRIBUTE_UPDATE = 'LAST_ATTRIBUTE_UPDATE'  # Attribute containing the last ts_attributes update datetime.
LAST_VALUE_UPDATE = "LAST_VALUE_UPDATE"  # Attribute containing the last ts_values update datetime.
RESERVED_KEYS = ['TS_NAME', '_id']  # Some keys that should not be kept when converting a MongoDB document into
# TimeSeries.
FIELD = 'FIELD'  # The attribute containing the field of a TimeSeries (e.g.: 'quote', 'call_schedule',
# 'amount_outstanding').
AND = 'AND'  # Represents the 'and' specification for the tsio.io.DBIO.select method.
OR = 'OR'  # Represents the 'or' specification for the tsio.io.DBIO.select method.
