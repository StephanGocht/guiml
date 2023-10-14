from dataclasses import dataclass as _dataclass


class Component:

    @_dataclass
    class Properties:
        pass

    @_dataclass
    class Dependencies:
        pass

    def __init__(self, properties, dependencies):
        self.properties = properties
        self.dependencies = dependencies
        self.on_init()

    def on_init(self):
        pass

    def on_destroy(self):
        pass


class AsMemberMixin:
    """Inheriting from this class allows to access properties and dependencies
    directly as members.

    For example, when inheriting from AsMemberMixin, you can use self.position instead of self.properties.position

    If a propertie and a dependencie has the same name, then the property has precedence.

    """

    def __getattr__(self, name):
        try:
            return getattr(self.properties, name)
        except AttributeError:
            return getattr(self.dependencies, name)

    def __setattr__(self, name, value):
        if hasattr(self.properties, name):
            setattr(self.properties, name, value)
        elif hasattr(self.dependencies, name):
            setattr(self.dependencies, name, value)
        else:
            super().__setattr__(name, value)
