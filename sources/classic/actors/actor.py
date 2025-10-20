from dataclasses import dataclass
from queue import Queue
from threading import Thread
from typing import Any


@dataclass
class Stop:
    pass


class Actor:
    _inbox: Queue[Any]
    _timeout: float
    _thread: Thread | None
    _stopped: bool

    def __init__(
        self, *,
        timeout: float = 0.01,
        inbox: Queue[Any] = None,
    ) -> None:
        self._thread = None
        self._timeout = timeout
        self._inbox = inbox or Queue()
        self._stop_obj = None
        self._stopped = True

    def run(self):
        self._before_run()

        self._stopped = False
        while not self._stopped:
            try:
                self._loop()
            except KeyboardInterrupt:
                self._stop()

        self._after_run()

    def _before_run(self) -> None:
        pass

    def _loop(self):
        pass

    def _after_run(self):
        pass

    @property
    def timeout(self):
        return self._timeout

    @property
    def thread_ident(self) -> int | None:
        if self._thread:
            return self._thread.ident

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> int:
        """
        Запускает выполнение планировщика.
        """
        if not self.is_alive():
            # TODO: Без deamon=True потоки не останавливались до завершения
            # выполнения задачи. Нужно найти аналогичное решение для
            # корректной остановки потока.
            self._thread = Thread(target=self.run, daemon=True)
            self._thread.start()

        return self._thread.ident

    def stop(self):
        """
        Планирует завершение актора.
        """
        message = Stop()
        if self.is_alive():
            self._inbox.put(message)

    def _stop(self) -> None:
        self._stopped = True

    def join(self, timeout: float = None):
        if self.is_alive():
            self._thread.join(timeout)
