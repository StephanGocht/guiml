from dataclasses import dataclass, field
from typing import Type, Optional
import cairo

class Component:
    def __init__(self, properties):
        self.properties = properties

        self.on_init()

    def on_init(self):
        pass

    def draw(self, ctx):
        pass

_components = {}

@dataclass
class ComponentMetaProperties:
    component_class: Type[Component]
    name: str
    template: Optional[str] = None

def component(*args, **kwargs):
    def register(cls):
        component = ComponentMetaProperties(cls, *args, **kwargs)
        _components[component.name] = component
        return cls

    return register

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
        return self.bottom - self.right

@dataclass
class WidgetProperty:
    # bounding box for registering clicks
    position: Rectangle = field(default_factory = Rectangle)
    layout: str = ""

@component("div")
class Div(Component):
    @dataclass
    class Properties(WidgetProperty):
        border: Border = field(default_factory = Border)
        margin: Rectangle = field(default_factory = Rectangle)
        padding: Rectangle = field(default_factory = Rectangle)
        background: Color = field(default_factory = Color)

    def draw(self, ctx):
        ctx.new_path()

        bwidth = self.properties.border.width / 2
        top = self.properties.position.top + self.properties.margin.top + bwidth
        left = self.properties.position.left + self.properties.margin.left + bwidth
        bottom = self.properties.position.bottom - self.properties.margin.bottom - bwidth
        right = self.properties.position.right - self.properties.margin.right - bwidth

        ctx.rectangle(left, top, right - left, bottom - top)
        ctx.set_line_width(self.properties.border.width)
        color = self.properties.border.color
        pat = cairo.SolidPattern(color.red, color.green, color.blue, color.alpha)
        ctx.set_source(pat)
        ctx.stroke_preserve()

        color = self.properties.background
        pat = cairo.SolidPattern(color.red, color.green, color.blue, color.alpha)
        ctx.set_source(pat)
        ctx.fill()

def get_extent(text, font_size):
    fontFace = cairo.ToyFontFace("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    fontMatrix = cairo.Matrix()
    fontMatrix.scale(font_size, font_size)
    user2device = cairo.Matrix()
    options = cairo.FontOptions()

    font = cairo.ScaledFont(fontFace, fontMatrix, user2device, options)
    return font.text_extents(text)


@component("text")
class Text(Component):
    @dataclass
    class Properties(WidgetProperty):
        font_size: int = 14
        color: Color = field(default_factory = Color)
        text: str = ""

    @property
    def width(self):
        extend = get_extent(self.properties.text, self.properties.font_size)
        return extend.x_advance

    @property
    def height(self):
        return self.properties.font_size

    def draw(self, ctx):
        color = self.properties.color
        ctx.set_source_rgb(color.red, color.green, color.blue)
        ctx.set_font_size(self.properties.font_size)
        ctx.select_font_face("Arial",
                             cairo.FONT_SLANT_NORMAL,
                             cairo.FONT_WEIGHT_NORMAL)
        ctx.move_to(self.properties.position.left, self.properties.position.top + self.height)
        ctx.show_text(self.properties.text)