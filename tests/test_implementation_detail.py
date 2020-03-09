"""
Tests for random stuff that isn't exactly part of the snecs spec, but would
be a regression if it changed.

You'll get what I mean by reading through them.
"""
from snecs._detail import InvariantDict


def test_invariant_dict_first_mro_entry_is_dict():
    assert InvariantDict.__mro__[1] == dict
