from sources.classic.actors import Actor


class SomeClass(Actor):

    @Actor.method
    def add(self, a, b):
        return a + b

    @Actor.method
    def mul(self, a, b):
        return a * b

    @Actor.method
    def sub(self, a, b):
        return a / b


def test_actor_sum():
    some_class = SomeClass()
    some_class.run()
    assert some_class.add(1, 2).get() == 3
    some_class.stop()


def test_actor_mul():
    some_class = SomeClass()
    some_class.run()
    assert some_class.mul(2, 3).get() == 6
    some_class.stop()


def test_actor_exception():
    some_class = SomeClass()
    some_class.run()
    some_class.sub(2, 0)  # без get так как ответа не будет
    assert some_class.sub(4, 2).get() == 2
    some_class.stop()
