from collections import defaultdict
from dataclasses import dataclass
from typing import Type, Optional

_components = {}
_layouts = {}
_injectables = defaultdict(list)


@dataclass
class ComponentMetaProperties:
    component_class: Type['Component']  # noqa: F821
    name: str
    template: Optional['DataHandle'] = None  # noqa: F821
    style: Optional['DataHandle'] = None  # noqa: F821


def component(*args, **kwargs):

    def register(cls):
        if not hasattr(cls, 'Properties'):
            raise AttributeError('Component is missing Properties')

        if not hasattr(cls, 'Dependencies'):
            raise AttributeError('Component is missing Dependencies')

        cls.Properties.__doc__ = ''
        cls.Dependencies.__doc__ = ''

        component = ComponentMetaProperties(cls, *args, **kwargs)
        if component.template is not None:
            component.template.index = component.name

        if component.style is not None:
            component.style.index = component.name

        if cls.__doc__ is None:
            cls.__doc__ = ''

        cls.__doc__ += ("\n    This component can be used via the tag"
                        f" :code:`{component.name}`.")

        _components[component.name] = component
        return cls

    return register


def layout(name):

    def register(cls):
        _layouts[name] = cls

        cls.__doc__ += ("\n    This layout can be used by setting the property "
                        f"layout to :code:`{name}`.")
        return cls

    return register


def injectable(providers):
    if isinstance(providers, str):
        providers = [providers]

    def register(cls):
        for provider in providers:
            _injectables[provider].append(cls)

        return cls

    return register
