import dataclasses
from dataclasses import dataclass

from typing import Optional
import typing

from pyglet import clock

from guiml.registry import injectable
from guiml.registry import _injectables


class Injectable:

    @dataclass
    class Dependencies:
        pass

    def __init__(self, dependencies):
        for field in dataclasses.fields(dependencies):
            setattr(self, field.name, getattr(dependencies, field.name))

        self.on_init()

    def on_init(self):
        pass

    def on_destroy(self):
        pass


class CyclicDependencyError(RuntimeError):
    pass


def get_dependency_class(injectable):
    return injectable.Dependencies


def get_dependencies(injectable, with_name=False):
    dependency_class = get_dependency_class(injectable)
    resolved_types = typing.get_type_hints(dependency_class)

    if with_name:
        return [(field.name, resolved_types[field.name])
                for field in dataclasses.fields(dependency_class)]
    else:
        return [
            resolved_types[field.name]
            for field in dataclasses.fields(dependency_class)
        ]


class DependencyResolver:

    @dataclass
    class Node:
        injectable: type
        dependencies: list
        t_visit: Optional[int] = None

    def __init__(self, injectables):
        self.nodes = {
            injectable: self.Node(injectable, get_dependencies(injectable))
            for injectable in injectables
        }

        self.notvisited = set(injectables)
        self.t = 0

        while self.notvisited:
            for node in self.notvisited:
                self.visit(self.nodes[node])
                break

    def visit(self, node):
        try:
            self.notvisited.remove(node.injectable)
        except KeyError:
            if node.t_visit is None:
                raise CyclicDependencyError()
            else:
                return
        else:
            for child in node.dependencies:
                self.visit(self.nodes[child])

            node.t_visit = self.t
            self.t += 1

    def __iter__(self):
        dag_order = sorted(self.nodes.values(), key=lambda x: x.t_visit)
        return iter((node.injectable for node in dag_order))


class Injector:

    def __init__(self, injectables):
        # list of dicts mapping injectable classes to its instance
        self.injectables = injectables

    def add_tag(self, tag):
        result = dict()
        self.injectables.append(result)

        to_add = DependencyResolver(_injectables[tag])
        for injectable_cls in to_add:
            if injectable_cls not in self:
                result[injectable_cls] = injectable_cls(
                    self.get_dependencies(injectable_cls))

        return result

    def get_dependencies(self, class_with_dependencies):
        args = {}
        for field_name, field_type in get_dependencies(class_with_dependencies,
                                                       with_name=True):
            args[field_name] = self[field_type]

        return get_dependency_class(class_with_dependencies)(**args)

    def __contains__(self, key):
        for layer in reversed(self.injectables):
            if key in layer:
                return True
        return False

    def __getitem__(self, key):
        for layer in reversed(self.injectables):
            try:
                return layer[key]
            except KeyError:
                pass

        raise KeyError(key)


class Subscription:

    def __init__(self, observable, callback):
        self.observable = observable
        self.callback = callback

    def cancel(self):
        self.observable.unsubscribe(self.callback)


class Observable:

    def __init__(self):
        self.callbacks = list()
        self.pre_call = None
        self.post_call = None

    def __call__(self, *args, **kwargs):
        if self.pre_call is not None:
            self.pre_call(*args, **kwargs)

        for callback in self.callbacks:
            callback(*args, **kwargs)

        if self.post_call is not None:
            self.post_call(*args, **kwargs)

    def subscribe(self, callback):
        self.callbacks.append(callback)
        return Subscription(self, callback)

    def unsubscribe(self, callback):
        self.callbacks.remove(callback)


class Subscriber:

    def subscribe_unmanaged(self, observable_name, owner, callback=None):
        if callback is None:
            callback = getattr(self, observable_name)

        observable = getattr(owner, observable_name)
        return observable.subscribe(callback)

    def subscribe(self, observable_name, owner, callback=None):
        subscription = self.subscribe_unmanaged(observable_name, owner, callback)
        if not hasattr(self, '_subscriptions'):
            self._subscriptions = list()
        self._subscriptions.append(subscription)

    def cancel_subscriptions(self):
        subscriptions = getattr(self, '_subscriptions')
        for subscription in subscriptions:
            subscription.cancel()


@injectable("application")
class UILoop(Injectable):

    def on_init(self):
        clock.schedule_interval(self._update, 0.01)
        self.on_update = Observable()

    def _update(self, dt):
        self.on_update(dt)
