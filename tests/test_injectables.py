from dataclasses import dataclass
from guiml.injectables import *


@injectable(providers="application")
class Injectable3(Injectable):

    @dataclass
    class Dependencies:
        injectable1: 'Injectable1'
        injectable2: 'Injectable2'

    def value(self):
        return 7 * self.injectable1.value() * self.injectable2.value()


@injectable(providers="application")
class Injectable1(Injectable):

    @dataclass
    class Dependencies:
        pass

    def value(self):
        return 3


@injectable(providers="application")
class Injectable2(Injectable):

    @dataclass
    class Dependencies:
        injectable1: Injectable1

    def value(self):
        return 5 * self.injectable1.value()


def test_injector_application():
    injector = Injector()
    injector.add_tag("application")
    assert (injector[Injectable3].value() == 7 * 5 * 3 * 3)
