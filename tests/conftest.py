# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import pytest
from snecs.component import Component, register_component


@pytest.fixture
def component_a():
    @register_component
    class AComponent(Component):
        pass

    return AComponent


@pytest.fixture
def component_b():
    @register_component
    class BComponent(Component):
        pass

    return BComponent
