from dataclasses import dataclass, field
from typing import Optional, Callable

import cairocffi as cairo

from guiml._components import Component
from guiml.registry import component
from guiml.injectables import Subscriber
from guimlcomponents.base.window import Canvas, MouseControl


@dataclass
class Color:
    red: float = 0.
    green: float = 0.
    blue: float = 0.
    alpha: float = 0.


@dataclass
class Border:
    width: int = 0.
    color: Color = field(default_factory=Color)


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

    @width.setter
    def width(self, value):
        self.right = self.left + value

    @property
    def height(self):
        return self.bottom - self.top

    @height.setter
    def height(self, value):
        self.bottom = self.top + value

    def is_inside(self, x, y):
        return (self.left <= x
                and x <= self.right
                and self.top <= y
                and y <= self.bottom)


class DrawableComponent(Component, Subscriber):

    @dataclass
    class Properties(Component.Properties):
        # bounding box of the component
        position: Rectangle = field(default_factory=Rectangle)
        draw_bounding_box: bool = False
        z_index: int = 0

        """
        zz_index contains the number of parents and will be set
        automatically.
        """
        zz_index: int = 0

    @dataclass
    class Dependencies(Component.Dependencies):
        canvas: Canvas

    def on_init(self):
        super().on_init()
        self.subscribe('on_draw', self.dependencies.canvas)

    def on_draw(self, context):
        if self.properties.draw_bounding_box:
            with context:
                context.new_path()

                context.rectangle(self.properties.position.left,
                                  self.properties.position.top,
                                  self.properties.position.width,
                                  self.properties.position.height)
                context.set_line_width(1)
                context.set_source(cairo.SolidPattern(0, 1, 0, 1))
                context.stroke()

    def on_destroy(self):
        self.cancel_subscriptions()
        super().on_destroy()


class InteractiveComponent(DrawableComponent):
    STYLE_CLASS_HOVER = 'hover'
    STYLE_CLASS_FOCUS = 'mouse_focus'

    @dataclass
    class Properties(DrawableComponent.Properties):
        on_click: Optional[Callable] = None
        cursor: Optional[str] = None

    @dataclass
    class Dependencies(DrawableComponent.Dependencies):
        mouse_control: MouseControl

    def on_init(self):
        super().on_init()
        self.subscribe('on_mouse_release', self.dependencies.mouse_control)
        self.subscribe('on_mouse_motion', self.dependencies.mouse_control)
        self._hover = False

    def on_mouse_enter(self):
        self._hover = True
        self.style_classes.add(self.STYLE_CLASS_HOVER)

        mouse_control = self.dependencies.mouse_control
        mouse_control.focus_enter(self)

    def on_mouse_focus(self):
        self.style_classes.add(self.STYLE_CLASS_FOCUS)

        mouse_control = self.dependencies.mouse_control

        if self.properties.cursor is not None:
            mouse_control.set_cursor(self.properties.cursor)

    def on_mouse_unfocus(self):
        self.style_classes.discard(self.STYLE_CLASS_FOCUS)

        mouse_control = self.dependencies.mouse_control
        mouse_control.set_cursor(None)

    def on_mouse_exit(self):
        self._hover = False
        self.style_classes.discard(self.STYLE_CLASS_HOVER)

        mouse_control = self.dependencies.mouse_control
        mouse_control.focus_exit(self)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.properties.position.is_inside(x, y):
            if not self._hover:
                self.on_mouse_enter()
        else:
            if self._hover:
                self.on_mouse_exit()

    def on_mouse_release(self, x, y, button, modifiers):
        position = self.properties.position
        if position.is_inside(x, y):
            if self.properties.on_click:
                self.properties.on_click()


class UIComponent(InteractiveComponent):
    pass


class Container(UIComponent):
    @dataclass
    class Properties(UIComponent.Properties):
        layout: str = ""

    @dataclass
    class Dependencies(UIComponent.Dependencies):
        pass

    @property
    def content_position(self):
        return self.properties.position

    @property
    def wrap_size(self):
        return Rectangle(0, 0, 0, 0)

    @property
    def width(self):
        return self.properties.position.width

    @property
    def height(self):
        return self.properties.position.height


@component("div")
class Div(Container):

    @dataclass
    class Properties(Container.Properties):
        border: Border = field(default_factory=Border)
        margin: Rectangle = field(default_factory=Rectangle)
        padding: Rectangle = field(default_factory=Rectangle)
        background: Color = field(default_factory=Color)

    @dataclass
    class Dependencies(Container.Dependencies):
        pass

    @property
    def bwidth(self):
        return self.properties.border.width / 2

    @property
    def wrap_size(self):
        top = (self.properties.margin.top
               + self.bwidth
               + self.properties.padding.top)

        left = (self.properties.margin.left
                + self.bwidth
                + self.properties.padding.left)

        bottom = (self.properties.margin.bottom
                  + self.bwidth
                  + self.properties.padding.bottom)

        right = (self.properties.margin.right
                 + self.bwidth
                 + self.properties.padding.right)

        return Rectangle(top, left, bottom, right)

    @property
    def content_position(self):
        wrap_size = self.wrap_size

        top = (self.properties.position.top
               + wrap_size.top)

        left = (self.properties.position.left
                + wrap_size.left)

        bottom = (self.properties.position.bottom
                  - wrap_size.bottom)

        right = (self.properties.position.right
                 - wrap_size.right)

        return Rectangle(top, left, bottom, right)

    def on_draw(self, ctx):
        with ctx:
            ctx.new_path()

            bwidth = self.properties.border.width / 2
            top = (self.properties.position.top
                   + self.properties.margin.top
                   + bwidth)

            left = (self.properties.position.left
                    + self.properties.margin.left
                    + bwidth)

            bottom = (self.properties.position.bottom
                      - self.properties.margin.bottom
                      - bwidth)

            right = (self.properties.position.right
                     - self.properties.margin.right
                     - bwidth)

            ctx.rectangle(left, top, right - left, bottom - top)

            color = self.properties.background
            pat = cairo.SolidPattern(color.red, color.green, color.blue,
                                     color.alpha)
            ctx.set_source(pat)
            ctx.fill_preserve()

            ctx.set_line_width(self.properties.border.width)
            color = self.properties.border.color
            pat = cairo.SolidPattern(color.red, color.green, color.blue,
                                     color.alpha)
            ctx.set_source(pat)
            ctx.stroke()

        super().on_draw(ctx)


@component("button")
class Button(Div):
    pass
