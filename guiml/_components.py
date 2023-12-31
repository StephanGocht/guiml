from dataclasses import dataclass as _dataclass
from typing import Optional, Callable


class StyleClassHandler:
    """
    Helper class to manage dyamically set style classes of a component.
    """

    def __init__(self):
        self.classes = dict()

    def get(self):
        result = list()
        for key, condition in self.classes.items():
            if condition is None or condition():
                result.append(key)

        return result

    def add(self,
            style_class: str,
            condition: Optional[Callable[[], bool]] = None):
        """
        Add the given style class. If condition is not none then the style
        class will only be added if the condition returns true when called.
        """

        self.classes[style_class] = condition

    def __contains__(self, style_class):
        return style_class in self.get()

    def remove(self, style_class: str):
        """
        Remove the given style class.
        """

        self.classes.pop(style_class, None)


class Component:
    """
    .. note::
        The constructor of a component will be called automatically.
        Therefore, you may not change the arguments when inheriting from this
        class and you are generally discuraged from providing your
        own :code:`__init__` methode. Use :code:`on_init` instead.
    """

    @_dataclass
    class Properties:
        """
        The properties dataclass is used to specify all properties of a
        component. Properties will be automatically injected when the
        component is constructed and will be replaced with every draw cycle.
        The Properties instance can be acccessed
        through :code:`self.properties`.

        .. note::
            When inheriting a component, make sure to also inherit the
            Properties dataclass.

        """
        pass

    @_dataclass
    class Dependencies:
        """
        The dependencies dataclass is used to specify all dependencies of a
        component. Dependencies will be automatically injected when the
        component is constructed. The Properties instance can be acccessed
        through :code:`self.dependencies`.

        .. note::
            When inheriting a component, make sure to also inherit the
            Dependencies dataclass.
        """
        pass

    def __init__(self, properties, dependencies):
        self.properties = properties
        self.dependencies = dependencies
        self.style_classes = StyleClassHandler()
        self.on_init()

    def on_init(self):
        """
        This method is called when the component is initialized.
        """
        pass

    def on_destroy(self):
        """
        This method is called when the component will be removed from the
        application.
        """
        pass


class AsMemberMixin:
    """Inheriting from this class allows to access properties and dependencies
    directly as members.

    For example, when inheriting from AsMemberMixin, you can use self.position
    instead of self.properties.position

    If a propertie and a dependencie has the same name, then the property has
    precedence.

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
