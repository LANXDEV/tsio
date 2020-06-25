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
Mongo Operators constants
"""
# mongodb Operators
ID = "_id"

# Comparison
SET = "$set"
EQUAL_TO = "$eq"  # Matches values that are equal to a specified value.
GREATER_THAN = "$gt"  # Matches values that are greater than a specified value.
GREATER_OR_EQUAL_THAN = "$gte"  # Matches values that are greater than or equal to a specified value.
IN = "$in"  # Matches any of the values specified in an array.
LESSER_THAN = "$lt"  # Matches values that are less than a specified value.
LESSER_OR_EQUAL_THAN = "$lte"  # Matches values that are less than or equal to a specified value.
NOT_EQUAL_TO = "$ne"  # Matches all values that are not equal to a specified value.
NIN = "$nin"  # Matches none of the values specified in an array.

# Logical
AND = "$and"
# Joins query clauses with a logical AND returns all documents that match the conditions of both clauses.
NOT = "$not"
# Inverts the effect of a query expression and returns documents that do not match the query expression.
NOR = "$nor"
# Joins query clauses with a logical NOR returns all documents that fail to match both clauses.
OR = "$or"
# Joins query clauses with a logical OR returns all documents that match the conditions of either clause.
