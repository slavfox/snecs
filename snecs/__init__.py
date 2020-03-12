# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""
snecs - the straightforward, nimble ECS for Python.

Remind me to stick a proper docstring here.
"""
from snecs.component import Component
from snecs.filters import compile_filter
from snecs.world import EntityID, World

__all__ = ["World", "EntityID", "compile_filter", "Component"]

__version_info__ = ("0", "0", "0")
__version__ = ".".join(__version_info__)
