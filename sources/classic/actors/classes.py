from dataclasses import dataclass, field
from queue import Queue
from time import sleep
from threading import Thread
from typing import Any, Callable, Dict, Tuple, Protocol, List

from classic.components import Registry


@dataclass
class Call:
    function: Callable[[...], Any]
    args: Tuple[Any]
    kwargs: Dict[str, Any]

    output: Queue[Any] = field(
        default_factory=lambda: Queue(1),
        init=False,
    )

    def __call__(self):
        result = self.function(*self.args, **self.kwargs)
        self.output.put(result)

    @property
    def result(self) -> Any:
        return self.output.get()


@dataclass
class Result:
    call: Call

    def __getattr__(self, item: str) -> Any:
        obj = getattr(self.call.result, item)
        if isinstance(obj, Exception):
            raise obj
        return obj


class Actor:
    inbox: Queue[Any] = field(default_factory=Queue)

    def run(self):
        stop = False
        while not stop:
            try:
                obj: Any = self.inbox.get()

                if isinstance(obj, Call):
                    obj()
                else:
                    self._handle(obj)

            except KeyboardInterrupt:
                stop = True

    def _handle(self, obj: Any) -> None:
        pass


@dataclass
class SuperVisor(Registry):
    actors: List[Actor] = field(init=False, default_factory=list)

    def register(self, obj: Actor) -> None:
        self.actors.append(obj)

    def unregister(self, obj: Actor) -> None:
        self.actors.remove(obj)

    def run(self):
        threads = [
            Thread(target=actor.run)
            for actor in self.actors
        ]

        for thread in threads:
            thread.start()

        stop = False
        while not stop:
            try:
                for thread in threads:
                    if not thread.is_alive():
                        thread.start()
            except KeyboardInterrupt:
                stop = True
            else:
                # Поддержка Gevent
                sleep(0)
