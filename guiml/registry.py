from collections import defaultdict
from dataclasses import dataclass
from typing import Type, Optional

import xml.etree.ElementTree as ET

_components = {}
_layouts = {}
_injectables = defaultdict(list)


@dataclass
class ComponentMetaProperties:
    component_class: Type['Component']  # noqa: F821
    name: str
    template: Optional[str] = None
    template_file: Optional[str] = None


def component(*args, **kwargs):

    def register(cls):
        component = ComponentMetaProperties(cls, *args, **kwargs)
        if component.template:
            component.template = ET.fromstring(component.template)
        _components[component.name] = component
        return cls

    return register


def layout(name):

    def register(cls):
        _layouts[name] = cls
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
