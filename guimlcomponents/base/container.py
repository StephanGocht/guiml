from guiml._components import Component

from dataclasses import dataclass, field
from typing import Optional, Callable
from collections import namedtuple

from guiml.registry import component
from guiml.injectables import UILoop

from guimlcomponents.base.window import *


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

class Container(Component):
    @dataclass
    class Properties:
        # bounding box for registering clicks
        position: Rectangle = field(default_factory = Rectangle)
        layout: str = ""

    @property
    def content_position(self):
        return self.properties.position

class DrawableComponent(Container):
    @dataclass
    class Properties(Container.Properties):
        draw_bounding_box: bool = False

    @dataclass
    class Dependencies:
        canvas: Canvas

    def on_init(self):
        super().on_init()
        self._canvas_on_draw_subscription = self.dependencies.canvas.on_draw.subscribe(self.on_draw)

    def on_draw(self, context):
        if self.properties.draw_bounding_box:
            with context:
                context.new_path()

                context.rectangle(self.properties.position.left, self.properties.position.top, self.properties.position.width, self.properties.position.height)
                context.set_line_width(1)
                context.set_source(cairo.SolidPattern(0, 1, 0, 1))
                context.stroke()

    def on_destroy(self):
        self._canvas_on_draw_subscription.cancel()
        super().on_destroy()

@component("div")
class Div(DrawableComponent):
    @dataclass
    class Properties(DrawableComponent.Properties):
        border: Border = field(default_factory = Border)
        margin: Rectangle = field(default_factory = Rectangle)
        padding: Rectangle = field(default_factory = Rectangle)
        background: Color = field(default_factory = Color)

    @dataclass
    class Dependencies(DrawableComponent.Dependencies):
        pass

    @property
    def content_position(self):
        bwidth = self.properties.border.width / 2
        top = self.properties.position.top + self.properties.margin.top + bwidth + self.properties.padding.top
        left = self.properties.position.left + self.properties.margin.left + bwidth + self.properties.padding.left
        bottom = self.properties.position.bottom - self.properties.margin.bottom - bwidth - self.properties.padding.bottom
        right = self.properties.position.right - self.properties.margin.right - bwidth - self.properties.padding.right

        return Rectangle(top, left, bottom, right)

    def on_draw(self, ctx):
        with ctx:
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