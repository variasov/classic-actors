import threading

from classic.actors.actor import Actor


class Supervisor(Actor):
    """
    Супервизор акторов. Запускает, останавливает, поднимает потоки при падении.
    """

    def __init__(self) -> None:
        super().__init__()
        self.actors: dict[int, Actor] = {}
        self.default_excepthook = threading.excepthook

        # подменим дефолтный обработчик падающих поток на свою реализацию
        threading.excepthook = self.excepthook

    def __del__(self):
        # при удалении супервизора возвращаем обработчик падающих потоков
        threading.excepthook = self.default_excepthook

    def stop(self, stop_all_actors=True):
        """
        Останавливает поток супервизора и опционально,
        всех переданных ему акторов.
        """
        if stop_all_actors:
            for actor in self.actors.values():
                actor.stop()
        super().stop()

    @Actor.method
    def add(self, actor: Actor):
        """
        Добавляет актор в супервизор для отслеживания и запускает его.

        Args:
            actor (Actor): Экземпляр актора.
        """
        actor.run()
        self.actors[actor.thread.ident] = actor

    @Actor.method
    def remove(self, actor):
        """
        Удаляет актор из супервизор для отслеживания.

        Args:
            actor (Actor): Экземпляр актора.
        """
        if ident := actor.thread.ident in self.actors:
            del self.actors[ident]

    def excepthook(self, args):
        """
        Наш обработчик не перехваченных исключений потока.

        Args:
            args (_type_): Аргументы упавшего потока.
        """
        # в хук может не придти поток - пропускаем это
        if not args.thread:
            return

        # если упавший поток это наш актор - перезапускаем его
        if actor := self.actors.get(args.thread.ident):
            actor.run()

        self.default_excepthook(args)
