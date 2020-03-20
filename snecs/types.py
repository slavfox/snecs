# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""
Type aliases to facilitate easier typing of snecs-dependent code.
"""
from snecs._detail import EntityID
from snecs._filters import Expr as FilterExpressionType
from snecs.query import BaseQuery as QueryType
from snecs.query import CompiledQuery as CompiledQueryType

__all__ = [
    "EntityID",
    "FilterExpressionType",
    "QueryType",
    "CompiledQueryType",
]
