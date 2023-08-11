from functools import wraps
from queue import Queue
from typing import Any, TypeVar, Type, Union, List

from classic.components import add_extra_annotation

from .classes import Actor, Call, Result


T = TypeVar('T', bound=Union[Any, Actor])


def in_actor(function: T) -> T:

    @wraps(function)
    def wrapper(self: Actor, *args, **kwargs):
        call = Call(function, *args, **kwargs)
        self.inbox.put(call)
        return call.output

    add_extra_annotation(wrapper, 'inbox', Queue)

    return wrapper


def group(cls: Type[Actor], size: int) -> List[Actor]:
    return [cls() for __ in range(size)]
