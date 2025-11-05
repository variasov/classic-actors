from dataclasses import dataclass
import queue
from threading import Thread
from typing import Any


@dataclass
class Stop:
    pass


class Actor:
    _inbox: queue.Queue[Any]
    _timeout: float
    _thread: Thread | None
    _stopped: bool

    def __init__(
        self, *,
        timeout: float = 0.01,
        inbox: queue.Queue[Any] = None,
    ) -> None:
        self._thread = None
        self._timeout = timeout
        self._inbox = inbox or queue.Queue()
        self._stop_obj = None
        self._stopped = True

    def run(self) -> None:
        self._before_loop()

        self._stopped = False
        while not self._stopped:
            try:
                self._loop()
            except KeyboardInterrupt:
                self._stop()

        self._after_loop()

    def _before_loop(self) -> None:
        pass

    def _loop(self) -> None:
        try:
            message = self._inbox.get(True, self._timeout)
        except queue.Empty:
            message = self._on_timeout()

        if isinstance(message, Stop):
            self._stop()

        self._on_message(message)

    def _on_timeout(self) -> Any:
        return None

    def _on_message(self, message: Any) -> None:
        pass

    def _after_loop(self) -> None:
        pass

    @property
    def timeout(self) -> float:
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

    def stop(self) -> None:
        """
        Планирует завершение актора.
        """
        if self.is_alive():
            self._inbox.put(Stop())

    def _stop(self) -> None:
        self._stopped = True

    def join(self, timeout: float = None):
        if self.is_alive():
            self._thread.join(timeout)
