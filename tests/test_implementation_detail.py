"""
Tests for random stuff that isn't exactly part of the snecs spec, but would
be a regression if it changed.

You'll get what I mean by reading through them.
"""
from typing import Type, TypeVar

import pytest
from snecs._detail import InvariantDict

K = TypeVar("K")
V = TypeVar("V")


@pytest.fixture  # type: ignore[misc]
def invariantdict_subclass() -> Type[InvariantDict[K, V]]:
    class MyInvariantDict(InvariantDict[K, V]):
        def value_for(self, key: K) -> int:  # type: ignore[override]
            return len(self)

    return MyInvariantDict


def test_invariant_dict_first_mro_entry_is_dict() -> None:
    assert InvariantDict.__mro__[1] == dict


def test_invariant_dict_rejects_assignment(
    invariantdict_subclass: Type[InvariantDict[str, str]],
) -> None:
    d = invariantdict_subclass()
    with pytest.raises(TypeError, match=r".*does not support.*assignment"):
        d["key"] = "value"


def test_invariant_dict_rejects_update(
    invariantdict_subclass: Type[InvariantDict[str, str]]
) -> None:
    d = invariantdict_subclass()
    with pytest.raises(TypeError, match=r".*does not support \.update\(\).*"):
        d.update({"key": "value"})  # type: ignore[misc]


def test_invariant_dict_rejects_setdefault(
    invariantdict_subclass: Type[InvariantDict[str, str]]
) -> None:
    d = invariantdict_subclass()
    with pytest.raises(
        TypeError, match=r".*does not support \.setdefault\(\).*"
    ):
        d.setdefault("key", "value")


def test_invariant_dict_rejects_del(
    invariantdict_subclass: Type[InvariantDict[str, str]]
) -> None:
    d = invariantdict_subclass()
    d.add("key")
    with pytest.raises(TypeError, match=r".*does not support key removal.*"):
        del d["key"]


def test_invariant_dict_rejects_pop(
    invariantdict_subclass: Type[InvariantDict[str, str]]
) -> None:
    d = invariantdict_subclass()
    d.add("key")
    with pytest.raises(TypeError, match=r".*does not support \.pop\(\).*"):
        d.pop("key")


def test_invariant_dict_rejects_popitem(
    invariantdict_subclass: Type[InvariantDict[str, str]]
) -> None:
    d = invariantdict_subclass()
    d.add("key")
    with pytest.raises(TypeError, match=r".*does not support \.popitem\(\).*"):
        d.popitem()


def test_invariant_dict_rejects_two_arg_fromkeys(
    invariantdict_subclass: Type[InvariantDict[str, int]]
) -> None:
    with pytest.raises(
        TypeError, match=r".*does not support two-argument fromkeys\(\).*"
    ):
        invariantdict_subclass.fromkeys(["a", "b", "c"], 1)


def test_invariant_dict_fromkeys(
    invariantdict_subclass: Type[InvariantDict[str, str]]
) -> None:
    d = invariantdict_subclass.fromkeys(["a", "b", "c"])
    assert d == {"a": 0, "b": 1, "c": 2}
