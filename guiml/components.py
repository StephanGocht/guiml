from dataclasses import dataclass, field
from typing import Type, Optional, Callable
import dataclasses
import pyglet
import cairo
import ctypes

import functools
from pyglet import app, clock, gl, image, window

from guiml.injectables import Canvas, UILoop, MouseControl

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

class DrawableComponent(Component):
    @dataclass
    class Dependencies:
        canvas: Canvas

    def on_init(self):
        super().on_init()
        self._canvas_on_draw_subscription = self.dependencies.canvas.on_draw.subscribe(self.on_draw)

    def on_draw(self, context):
        pass

    def on_destroy(self):
        self._canvas_on_draw_subscription.cancel()
        super().on_destroy()

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


@component("window")
class Window(Component):
    @dataclass
    class Properties:
        width: int = 400
        height: int = 400
        resizable: bool = False

        top: int = 500
        left: int = 2000

    @dataclass
    class Dependencies:
        canvas: Canvas
        ui_loop: UILoop
        mouse_control: MouseControl

    def on_init(self):
        super().on_init()
        self.init_window()
        self.init_canvas()
        self.register_mouse_events()

        self._ui_loop_on_update_subscription = \
            self.dependencies.ui_loop.on_update.subscribe(self.on_update)

    def remap_mouse_pos(self, callable, x, y, *args, **kwargs):
        # pyglet uses bot left as origin, swapt origin to top right
        return callable(x, self.properties.height - y, *args, **kwargs)

    def register_mouse_events(self):
        mouse_events = [
            "on_mouse_motion",
            "on_mouse_press",
            "on_mouse_release",
            "on_mouse_drag",
            "on_mouse_enter",
            "on_mouse_leave",
            "on_mouse_scroll",
        ]

        args = {
            event: functools.partial(self.remap_mouse_pos,
                getattr(self.dependencies.mouse_control, event))
            for event in mouse_events
        }

        self.window.push_handlers(**args)

    # def on_destroy(self):
    #     self._ui_loop_on_update_subscription.cancel()

    def init_window(self):
        args = {key: getattr(self.properties, key) for key in ["width", "height", "resizable"]}
        self.window = pyglet.window.Window(**args)
        self.window.set_location(self.properties.left, self.properties.top)

        self.window.push_handlers(on_draw = self.on_draw)

    def on_draw(self):
        self.window.clear()
        # draw the texture
        self.texture.blit(0, 0)

    def init_canvas(self):
        width = self.properties.width
        height = self.properties.height

        # Create texture backed by ImageSurface
        self.surface_data = (ctypes.c_ubyte * (width * height * 4))()
        surface = cairo.ImageSurface.create_for_data(self.surface_data, cairo.FORMAT_ARGB32, width, height, width * 4);
        self.texture = image.Texture.create(width, height, gl.GL_TEXTURE_2D, gl.GL_RGBA)
        self.texture.tex_coords = (0, 1, 0) + (1, 1, 0) + (1, 0, 0) + (0, 0, 0)

        self.context = cairo.Context(surface)
        self.dependencies.canvas.context = self.context

    def clear(self):
        self.context.set_operator(cairo.Operator.CLEAR)
        self.context.rectangle(0, 0, self.properties.width, self.properties.height)
        self.context.fill()

        self.context.set_operator(cairo.Operator.OVER)

    def on_update(self, dt):
        self.clear()
        self.dependencies.canvas.draw()

        # Update texture from sruface data
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture.id)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA,
            self.properties.width, self.properties.height, 0, gl.GL_BGRA,
            gl.GL_UNSIGNED_BYTE, self.surface_data)


@dataclass
class WidgetProperty:
    # bounding box for registering clicks
    position: Rectangle = field(default_factory = Rectangle)
    layout: str = ""

@component("div")
class Div(DrawableComponent):
    @dataclass
    class Properties(WidgetProperty):
        border: Border = field(default_factory = Border)
        margin: Rectangle = field(default_factory = Rectangle)
        padding: Rectangle = field(default_factory = Rectangle)
        background: Color = field(default_factory = Color)

    def on_draw(self, ctx):
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

@component("button")
class Button(Div):
    @dataclass
    class Properties(Div.Properties):
        on_click: Optional[Callable] = None

    @dataclass
    class Dependencies(Div.Dependencies):
        mouse_control: MouseControl

    def on_init(self):
        super().on_init()
        on_mouse_release = self.dependencies.mouse_control.on_mouse_release
        subscription = on_mouse_release.subscribe(self.on_mouse_release)
        self._on_mouse_release_subscription = subscription

    def on_destroy(self):
        self._on_mouse_release_subscription.cancel()

    def on_mouse_release(self, x, y, button, modifiers):
        position = self.properties.position
        if position.left <= x and x <= position.right and position.top <= y and y <= position.bottom:
            if self.properties.on_click:
                self.properties.on_click()


def get_extent(text, font_size):
    fontFace = cairo.ToyFontFace("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    fontMatrix = cairo.Matrix()
    fontMatrix.scale(font_size, font_size)
    user2device = cairo.Matrix()
    options = cairo.FontOptions()

    font = cairo.ScaledFont(fontFace, fontMatrix, user2device, options)
    return font.text_extents(text)


@component("text")
class Text(DrawableComponent):
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

    def on_draw(self, ctx):
        color = self.properties.color
        ctx.set_source_rgb(color.red, color.green, color.blue)
        ctx.set_font_size(self.properties.font_size)
        ctx.select_font_face("Arial",
                             cairo.FONT_SLANT_NORMAL,
                             cairo.FONT_WEIGHT_NORMAL)
        ctx.move_to(self.properties.position.left, self.properties.position.top + self.height)
        ctx.show_text(self.properties.text)