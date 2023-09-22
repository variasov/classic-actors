# Todo and Bugs list

## Bugs

Есть забавный баг. Код для воспроизведения ниже:

```python
from sources.classic.actors import Actor, Supervisor
import time


class SomeClass(Actor):

    @Actor.method
    def add(self, a, b):
        return a + b


some_class_1 = SomeClass()
some_class_2 = SomeClass()

supervisor = Supervisor()
supervisor.run()
supervisor.add(some_class_1)
supervisor.add(some_class_2)
supervisor.run()
# time.sleep(1)
supervisor.stop()
```

При его исполнении метод супервизора `stop()` останавливает поток супервизора, а акторы продолжают работать. То есть программа не заканчивает свою работу, два потока акторов продолжают работать.

Если перед `stop()` расскоментировать строку с задержкой по времени - то все акторы выключаются нормально.

Скорее всего проблем в близком расположении инструкций супер визора `start` и `stop`: потоки акторов еще начинают свою работу, а поток супервизора уже остановился.

## TODO

Подумать про перенос акторов с потоков на процессы.
