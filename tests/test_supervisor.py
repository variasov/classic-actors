import os
import queue
import time
import tempfile

from classic.actors import Actor, Stop, Supervisor

import logging

logging.basicConfig(level=logging.DEBUG)


class HealthyActor(Actor):

    def __init__(self):
        super().__init__()
        self.counter = 0

    def _loop(self):
        self.counter += 1
        try:
            message = self._inbox.get(True, self.timeout)
        except queue.Empty:
            return

        if isinstance(message, Stop):
            self._stop()


class BrokenActor(Actor):

    def __init__(self):
        super().__init__()
        self.counter = 0

    def run(self):
        while True:
            self.counter += 1
            time.sleep(0.1)
            if self.counter >= 3:
                raise ValueError



def test__supervisor():
    supervisor = Supervisor()
    broken_actor = BrokenActor()
    supervisor.add(broken_actor)

    supervisor.start()
    time.sleep(1)

    supervisor.stop()
    supervisor.join()

    assert broken_actor.counter > 9


def test__supervisor__healthcheck__with__healthy_actor():
    tmp = os.path.join(tempfile.mkdtemp(), 'healthcheck')
    supervisor = Supervisor(
        healthcheck_filepath=tmp,
        # max_errors=(1, 0.1),
    )
    healthy_actor = HealthyActor()
    supervisor.add(healthy_actor)

    supervisor.start()
    time.sleep(1)

    supervisor.stop()
    supervisor.join()

    assert os.path.exists(tmp)


def test__supervisor__healthcheck__with__broken_actor():
    tmp = os.path.join(tempfile.mkdtemp(), 'healthcheck')
    supervisor = Supervisor(
        healthcheck_filepath=tmp,
        max_errors_count=5,
        max_errors_period=1.0,
    )
    broken_actor = BrokenActor()
    supervisor.add(broken_actor)

    supervisor.start()
    time.sleep(3)

    supervisor.stop()
    supervisor.join()

    assert supervisor._is_healthy is False
