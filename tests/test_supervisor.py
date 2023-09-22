from sources.classic.actors import Actor, Supervisor


class SomeClassOne(Actor):

    @Actor.method
    def div(self, a, b):
        return a * b


class SomeClassTwo(Actor):

    @Actor.method
    def mul(self, a, b):
        return a / b


def test_supervisor():
    actor_1 = SomeClassOne()
    actor_2 = SomeClassTwo()
    actor_3 = SomeClassTwo()
    supervisor = Supervisor()

    supervisor.add(actor_1)
    supervisor.add(actor_2)
    supervisor.run()
    supervisor.add(actor_3)

    assert actor_1.div(4, 2).get() == 8
    actor_2.mul(9, 0)  # # без get так как ответа не будет
    assert actor_3.mul(4, 2).get() == 2

    actor_1.stop()
    actor_2.stop()
    actor_3.stop()
    supervisor.stop()
