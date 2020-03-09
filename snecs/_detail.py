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

if TYPE_CHECKING:
    from typing import Generator, Iterable, NoReturn, Iterator

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
    # So, here's where the ugly hack comes in. Mypy ignores `del`s,
    # so we let it know that `Bitmask(0b10) | 0b01` is still a valid
    # Bitmask, but we immediately delete the definition right afterwards -
    # so that at runtime, this entire class body is just::
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
    def __lshift__(self, other: "int") -> "Bitmask":
        ...

    del __lshift__

    def __rshift__(self, other: "int") -> "Bitmask":
        ...

    del __rshift__

    def __and__(self, other: "_IntOrBitmask") -> "Bitmask":
        ...

    del __and__

    def __xor__(self, other: "_IntOrBitmask") -> "Bitmask":
        ...

    del __xor__

    def __or__(self, other: "_IntOrBitmask") -> "Bitmask":
        ...

    del __or__


class EntityID(int):
    """
    A ``NewType(int)`` that only allows incrementation.
    """

    __slots__ = ()

    def __add__(self, other: "int") -> "EntityID":
        ...

    del __add__

    def __iadd__(self, other: "int") -> "EntityID":
        ...

    del __iadd__


def bits(bitmask: "Bitmask") -> "Generator[Bitmask, None, None]":
    """Return a list of individual bits in a bitmask."""
    for n in range(bitmask.bit_length()):
        bit = bitmask & (1 << n)
        if bit:
            yield bit


ZERO = Bitmask(0)


class _Dict:
    """Dict, but ignored by mypy."""

    # Definition intentionally left blank.
    #
    # ...wait, what?
    #
    # Yup. Hello. This is, quite possibly, one of the worst hacks I've done
    # in my life. If you're reading this, I'm so sorry.
    #
    # Here's the problem:
    # I want InvariantDict to keep the native dict performance, so it has to
    # inherit from dict. At the same time, calling most normal dict methods on
    # an InvariantDict is not valid, and I'd like the type system to reflect
    # this.
    # Ideally, I'd like to mark InvariantDict as a subtype of Mapping,
    # and not Dict. Unfortunately, you can't subtype X and tell
    # mypy to *pretend* your class isn't *really* a subtype of X.


# ...Or can you?
# Welcome to an indentation level down from where we were a moment ago. Turns
# out that if you try hard enough, you *can* actually fool mypy, using a dirty,
# dirty hack in the same vein as our earlier `del` trick in Bitmask, a couple
# lines above.
#
# Mypy sees the _Dict above as just an empty class with no bases,
# so it *won't* override the Mapping we actually want - great! All that's left
# now is to make Python itself see _Dict not as an empty class, but as... well,
# dict. To do that while still fooling mypy into not realizing _Dict is `dict`,
# we have to replace it with `dict` in a way that Mypy doesn't understand.
# The trivial:
#
#   _Dict = dict
#
# just wouldn't work, because that is just type aliasing. So, what alternate
# ways of setting a variable does Python offer? Off the top of my head,
# we have `exec("foo = bar")` and locals() / globals(). The latter option is
# slightly easier to maintain, so I'm choosing that one:
# Bada bing-
locals()[_Dict.__name__] = dict
# -bada boom.
#
# The last thing that needs explanation is that I'm using `_Dict.__name__`
# rather than a string "_Dict", so that there's no risk of forgetting to
# update the string if the class name ever changes.


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

    def update(self, *args: "Any", **kwargs: "Any") -> "NoReturn":
        raise TypeError(
            f"{self.__class__.__name__} does not support .update(), use "
            f".add() instead."
        )

    def __delitem__(self, key: "K") -> "NoReturn":
        raise TypeError(
            f"{self.__class__.__name__} does not support key removal."
        )

    def setdefault(self, key: "K", default: "V" = None) -> "NoReturn":
        raise TypeError(
            f"{self.__class__.__name__} does not support .setitem(), use "
            f".getitem() instead."
        )

    def pop(self, key: "K", default: "V" = None) -> "NoReturn":
        raise TypeError(f"{self.__class__.__name__} does not support .pop().")

    def popitem(self) -> "NoReturn":
        raise TypeError(
            f"{self.__class__.__name__} does not support .popitem(). Use "
            f"reversed() instead."
        )

    def fromkeys(
        self, iterable: "Iterable[K]", value: "V" = None
    ) -> "NoReturn":
        raise TypeError(
            f"{self.__class__.__name__} does not support .fromkeys()."
        )

    # You already know how this works.
    def __getitem__(self, item: "K") -> "V":
        ...

    del __getitem__

    def __iter__(self) -> "Iterator[K]":
        ...

    del __iter__

    def __len__(self) -> "int":
        ...

    del __len__
