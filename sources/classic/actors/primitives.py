from dataclasses import dataclass, field
from queue import Queue
from typing import Any, Callable, Dict, Tuple


@dataclass
class Future:
    """
    Ссылка на будущий результат вызова метода в цикле актора.
    """
    # очередь в одно сообщение для возврата результата метода
    output: Queue[Any] = field(
        default_factory=lambda: Queue(1),
        init=False,
    )

    def set(self, value: Any) -> None:
        """
        Установка результата вызова для возврата.

        Args:
            value (Any): Результат вызова метода.
        """
        self.output.put(value)

    def get(self, timeout=None) -> Any:
        """
        Возвращает результат вызова метода. Блокируется на время ожидания.

        Args:
            timeout (_type_, optional): Время ожидания. По умолчанию None.

        Returns:
            Any: Результат вызова метода
        """
        return self.output.get(block=True, timeout=timeout)

    def check(self):
        """
        Проверяет очередь возврата результата. Возвращает значение или
        генерирует исключение пустой очереди.

        Raises:
            Exception: Исключение что результата пока нет.

        Returns:
            Any: Результат вызова метода
        """
        return self.output.get(block=False)


@dataclass
class Call:
    """
    Вызываемый объект. Передается через inbox, для последующего вызова
    в главном цикле актора.
    """
    # метод для вызова с его параметрами - args и kwargs
    function: Callable[[], Any]
    args: Tuple[Any]
    kwargs: Dict[str, Any]

    # ссылка на результат вызова в главном цикле актора
    result: Future = field(default_factory=Future)

    # вызов метода актора с возвратом ссылки на результат
    def __call__(self):
        result = self.function(*self.args, **self.kwargs)
        self.result.set(result)
