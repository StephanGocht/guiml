from dataclasses import dataclass, field
from typing import Type, Optional, Callable
import dataclasses
import pyglet

# import cairo
import cairocffi as cairo
import pangocffi as pango
import pangocairocffi as pangocairo


import ctypes
import xml.etree.ElementTree as ET
from collections import namedtuple

import functools
from pyglet import app, clock, gl, image, window
from pyglet.window import key as pyglet_key

@dataclass
class Color:
    red: float = 0.
    green: float = 0.
    blue: float = 0.
    alpha: float = 0.

@dataclass
class Border:
    width: int = 0.
    color: Color = field(default_factory = Color)

@dataclass
class Rectangle:
    top: int = 0
    left: int = 0
    bottom: int = 0
    right: int = 0

    def is_valid(self):
        return self.left < self.right and self.top < self.bottom

    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.bottom - self.top

class Component:
    @dataclass
    class Properties:
        pass

    @dataclass
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

class Container(Component):
    @dataclass
    class Properties:
        # bounding box for registering clicks
        position: Rectangle = field(default_factory = Rectangle)
        layout: str = ""

    @property
    def content_position(self):
        return self.properties.position

_components = {}

class AsMemberMixin:
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

@dataclass
class ComponentMetaProperties:
    component_class: Type[Component]
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