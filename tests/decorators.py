from queue import Queue

from classic.actors import actor


class SomeClass:

    def run(self):
        stop = False
        while not stop:
            try:
                item = self.queue.get()

            except KeyboardInterrupt:
                return


def test_actor():
    pass
