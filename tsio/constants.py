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
Definition of constants for TimeSeries and DB reading/writing classes.
TODO: Implement a good way to override these constants (e.g.: with a config file).
"""
COMPONENTS = "COMPONENTS"  # The key used to access the 'Components' dict of a TimeSeries object.
TS_NAME = 'TS_NAME'  # Attribute (in a MongoDB document) representing the ts_name if a TimeSeries.
TS_VALUES = 'VALUE'  # Attribute (in a MongoDB document) representing the ts_values of the TimeSeries.
LAST_USE = 'LAST_USE'  # Attribute for the last use date of a TimeSeries.
LAST_ATTRIBUTE_UPDATE = 'LAST_ATTRIBUTE_UPDATE'  # Attribute containing datetime of the last ts_attributes update.
LAST_VALUE_UPDATE = "LAST_VALUE_UPDATE"  # Attribute containing datetime the last ts_values update.
RESERVED_KEYS = ['TS_NAME', '_id']  # Keys that should not be kept when converting a MongoDB document into
# TimeSeries.
FIELD = 'FIELD'  # Optional attribute containing the field of a TimeSeries (e.g.: 'quote', 'call_schedule',
# 'amount_outstanding'). This is only used in tsio.io.dbio.DBIO.select method.
AND = ['AND', 'E']  # Represents the 'and' specification for the tsio.io.dbio.DBIO.select method.
OR = ['OR', 'OU']  # Represents the 'or' specification for the tsio.io.dbio.DBIO.select method.
