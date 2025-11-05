import logging
import queue
from collections import defaultdict
from concurrent.futures import Future
from dataclasses import dataclass, field
import time
import threading

from .actor import Actor, Stop


@dataclass
class AddActor:
    actor: Actor
    future: Future = field(default_factory=Future)


@dataclass
class RemoveActor:
    actor: Actor
    future: Future = field(default_factory=Future)


@dataclass
class ThreadFailed:
    thread: threading.Thread | None
    timestamp: int = field(default_factory=time.time)


class HealthCheck:
    pass


class ActorsRegistry:
    _threads_to_actors: dict[int, Actor]
    _actors_to_threads: dict[int, int]
    _fails: dict[int, list[float]]

    def __init__(self, max_errors_count: int, max_errors_period: float):
        self._threads_to_actors = {}
        self._actors_to_threads = {}
        self._fails = defaultdict(list)
        self._max_errors_count = max_errors_count
        self._max_errors_period = max_errors_period

    def add(self, actor: Actor) -> None:
        thread_id = self._actors_to_threads.get(id(actor))
        if thread_id is None:
            thread_id = actor.start()
            self._actors_to_threads[id(actor)] = thread_id
            self._threads_to_actors[thread_id] = actor

    def remove(self, actor: Actor) -> None:
        thread_id = self._actors_to_threads.pop(id(actor), None)
        if thread_id is not None:
            actor = self._threads_to_actors[thread_id]
            actor.stop()

    def remove_all(self):
        while self._actors_to_threads:
            actor_id, thread_id = self._actors_to_threads.popitem()
            actor = self._threads_to_actors.pop(thread_id)
            actor.stop()

    def ensure(self, thread_id: int) -> None | int | RuntimeError:
        actor = self._threads_to_actors.get(thread_id)
        if actor is not None:
            self._threads_to_actors.pop(thread_id, None)

            actor_id = id(actor)
            self._fails[actor_id].append(time.time())
            if not self.is_errors_limit_exceeded(actor):
                thread_id = actor.start()
                self._actors_to_threads[actor_id] = thread_id
                self._threads_to_actors[thread_id] = actor
            else:
                del self._actors_to_threads[actor_id]
                del self._fails[actor_id]
                return RuntimeError(
                    f'Actor {actor} with id {actor_id} failed more than '
                    f'{self._max_errors_count} times '
                    f'for {self._max_errors_period} period, '
                    f'and was removed from supervisor.'
                )

    def ensure_all(self) -> None:
        for actor_id, thread_id in self._actors_to_threads.items():
            actor = self._threads_to_actors.pop(thread_id)
            new_thread_id = actor.start()
            self._threads_to_actors[new_thread_id] = actor
            self._actors_to_threads[id(actor)] = new_thread_id

    def is_errors_limit_exceeded(self, actor: Actor):
        time_elapsed = time.monotonic() - self._max_errors_period
        all_errors = self._fails.get(id(actor))
        counter = 0
        while counter < len(all_errors):
            e = all_errors[counter]
            if e > time_elapsed:
                counter += 1
            else:
                all_errors.remove(counter)

        return counter > self._max_errors_count


class Supervisor(Actor):
    _actors: ActorsRegistry
    _stopped: bool
    _is_healthy: bool
    _healthcheck_filepath: str | None
    _logger: logging.Logger

    def __init__(
        self,
        *,
        healthcheck_filepath: str = None,
        max_errors_count: int = 10,
        max_errors_period: float = 1.0,
        logger: logging.Logger | None = None,
        timeout: float = 60.0,
        **kwargs,
    ):
        super().__init__(timeout=timeout, **kwargs)
        self._logger = logger or logging.getLogger('classic.actors.supervisor')
        self._actors = ActorsRegistry(max_errors_count, max_errors_period)
        self._default_excepthook = None
        self._is_healthy = True
        self._healthcheck_filepath = healthcheck_filepath
        self._last_healthcheck = None

    def _before_loop(self):
        self._default_excepthook = threading.excepthook
        threading.excepthook = self.excepthook

        self._logger.info('Supervisor started')

    def _after_loop(self):
        threading.excepthook = self._default_excepthook
        self._actors.remove_all()

        self._logger.info('Supervisor stopped')

    @property
    def timeout(self):
        if self._healthcheck_filepath is None or not self._is_healthy:
            return None

        if self._last_healthcheck is None:
            return 0

        time_since_last_healthcheck = time.monotonic() - self._last_healthcheck
        timeout = self._timeout - time_since_last_healthcheck
        if timeout < 0:
            timeout = 0
        return timeout

    def _loop(self):
        try:
            message = self._inbox.get(True, self.timeout)
        except queue.Empty:
            self._healthcheck()
            return

        if isinstance(message, Stop):
            self._stop()
        elif isinstance(message, AddActor):
            self._on_add(message)
        elif isinstance(message, RemoveActor):
            self._on_remove(message)
        elif isinstance(message, ThreadFailed):
            self._on_thread_failed(message)

    def _on_thread_failed(self, message: ThreadFailed):
        if message.thread is None:
            self._actors.ensure_all()
        else:
            result = self._actors.ensure(message.thread.ident)
            if isinstance(result, RuntimeError):
                self._logger.error(result)
                self._is_healthy = False

    def add(self, actor: Actor):
        """
        Добавляет актор в супервизора для отслеживания и запускает его.

        Args:
            actor (Actor): Экземпляр актора.
        """
        task = AddActor(actor)
        self._inbox.put(task)
        return task.future

    def _on_add(self, task: AddActor):
        self._actors.add(task.actor)
        task.future.set_result(None)

    def remove(self, actor: Actor):
        """
        Удаляет актор из супервизора для отслеживания.

        Args:
            actor (Actor): Экземпляр актора.
        """
        task = RemoveActor(actor)
        self._inbox.put(task)
        return task.future

    def _on_remove(self, task: RemoveActor):
        self._actors.remove(task.actor)
        task.future.set_result(None)

    def excepthook(self, args):
        """
        Наш обработчик не перехваченных исключений потока.

        Args:
            args (_type_): Аргументы упавшего потока.
        """
        self._inbox.put(ThreadFailed(args.thread))

    def _healthcheck(self):
        """
        Создает файл для проверки жизнеспособности.
        Проверяется через что-то вроде:
        sh test `find "path/to/live_file" -mmin -1`
        """
        if self._healthcheck_filepath and self._is_healthy:
            open(self._healthcheck_filepath, 'w').close()
            self._last_healthcheck = time.monotonic()
            self._logger.debug('Healthcheck file written')
