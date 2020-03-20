# Copyright (c) 2020 Slavfox
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""
Non-public implementation details for internal snecs use.

If you thought “that just sounds like an euphemism for ‘dirty hacks’” to
yourself, well... you're absolutely correct.

The names defined here are not part of the public API, and subject to change.
"""
from typing import TYPE_CHECKING, Any, Mapping, TypeVar, Union
from abc import ABC, abstractmethod

__all__ = ["EntityID", "InvariantDict", "Bitmask", "ZERO"]


if TYPE_CHECKING:
    from typing import Iterable, NoReturn, Iterator, Optional

    class EntityID(int):
        """
        A ``NewType(int)`` that only allows incrementation.
        """

        __slots__ = ()

        if TYPE_CHECKING:

            def __add__(self, other: "int") -> "EntityID":
                ...

            def __iadd__(self, other: "int") -> "EntityID":
                ...

    class _Dict:
        """Dict, but ignored by mypy."""

        # Here's the problem:
        # I want InvariantDict to keep the native dict performance, so it has
        # to inherit from dict. At the same time, calling most normal dict
        # methods on an InvariantDict is not valid, and I'd like the type
        # system to reflect this.
        # Ideally, I'd like to mark InvariantDict as a subtype of Mapping,
        # but not Dict.
        # This is why, for Mypy, we make `_Dict` is a no-op class, but for the
        # interpreter, it's literally just the builtin `dict.


else:
    _Dict = dict
    EntityID = int

_IntOrBitmask = Union[int, "Bitmask"]


class Bitmask(int):
    """
    Effectively a ``NewType(int)`` that allows bitwise operations.
    """

    __slots__ = ()

    # Normally, typing.NewType would be perfect for Bitmasks - after all,
    # we never want to pass a random integer into a function expecting a
    # Bitmask. Aliasing `Bitmask = int` doesn't help us at all.
    # However, NewType has a big problem::
    #
    #     foo: Bitmask = Bitmask(0b10)
    #     foo |= 0b01  # error: Incompatible types in assignment (expression
    #                  # has type "int", variable has type "Bitmask")
    #     foo = Bitmask(foo | 0b01)  # ok
    #
    # Why is this a problem? Because explicitly casting to Bitmask is slooooow.
    # I'm not kidding. The last line is twice as slow as the previous one on
    # my machine. That's the last thing we want when we're already using
    # bitmasks for performance!
    #
    # So, here's where the ugly hack comes in. We let Mypy know that
    # `Bitmask(0b10) | 0b01` is still a valid Bitmask, but at runtime, this
    # entire class body is just::
    #
    #     class Bitmask(int):
    #         pass
    #
    # That way, it doesn't screech at us when we use bitwise operators,
    # but at the same time, it raises warnings when we try to use a Bitmask
    # improperly - eg. by adding to, or multiplying it - or when we pass a
    # naked `int` into a function expecting a Bitmask.
    #
    # Yay.
    if TYPE_CHECKING:

        def __lshift__(self, other: "int") -> "Bitmask":
            ...

        def __rshift__(self, other: "int") -> "Bitmask":
            ...

        def __and__(self, other: "_IntOrBitmask") -> "Bitmask":
            ...

        def __xor__(self, other: "_IntOrBitmask") -> "Bitmask":
            ...

        def __or__(self, other: "_IntOrBitmask") -> "Bitmask":
            ...

        def __invert__(self) -> "Bitmask":
            ...


ZERO = Bitmask(0)


K = TypeVar("K")
V = TypeVar("V")


class InvariantDict(_Dict, Mapping[K, V], ABC):
    """
    A mapping with auto-assigned keys that rejects mutation other than add().
    """

    __slots__ = ()

    @abstractmethod
    def value_for(self, key: "K") -> "V":
        ...

    def add(self, key: "K") -> "V":
        v = self.value_for(key)
        dict.__setitem__(self, key, v)  # type: ignore
        return v

    def __setitem__(self, key: "K", value: "V") -> "NoReturn":
        raise TypeError(
            f"{self.__class__.__name__} does not support item assignment, "
            f"use .add() instead."
        )

    def update(  # type: ignore
        self, *args: "Any", **kwargs: "Any"
    ) -> "NoReturn":
        raise TypeError(
            f"{self.__class__.__name__} does not support .update(), use "
            f".add() instead."
        )

    def __delitem__(self, key: "K") -> "NoReturn":
        raise TypeError(
            f"{self.__class__.__name__} does not support key removal."
        )

    def setdefault(
        self, key: "K", default: "Optional[V]" = None
    ) -> "NoReturn":
        raise TypeError(
            f"{self.__class__.__name__} does not support .setdefault(), use "
            f".get() instead."
        )

    def pop(self, key: "K", default: "Optional[V]" = None) -> "NoReturn":
        raise TypeError(f"{self.__class__.__name__} does not support .pop().")

    def popitem(self) -> "NoReturn":
        raise TypeError(
            f"{self.__class__.__name__} does not support .popitem(). Use "
            f"reversed() instead."
        )

    @classmethod
    def fromkeys(
        cls, iterable: "Iterable[K]", value: "Optional[V]" = None
    ) -> "InvariantDict[K, V]":
        if value is not None:
            raise TypeError(
                f"{cls.__name__} does not support two-argument fromkeys()."
            )
        d = cls()
        for k in iterable:
            d.add(k)
        return d

    # You already know how this works.
    if TYPE_CHECKING:

        def __getitem__(self, item: "K") -> "V":
            ...

        def __iter__(self) -> "Iterator[K]":
            ...

        def __len__(self) -> "int":
            ...
