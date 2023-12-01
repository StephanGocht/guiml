from dataclasses import dataclass, field
from typing import Optional, Callable, Literal

import cairocffi as cairo

from guiml._components import Component
from guiml.registry import component
from guiml.injectables import Subscriber
from guimlcomponents.base.window import Canvas, MouseControl
from guimlcomponents.base.shared import Rectangle, Border, Color
from guimlcomponents.base.shared import resources as res


class DrawableComponent(Component, Subscriber):
    """
    A base class for all components that draw onto the window.
    """

    @dataclass
    class Properties(Component.Properties):
        """ """

        position: Rectangle = field(default_factory=Rectangle)
        """
        The Bounding box for the component to draw in.
        """

        draw_bounding_box: bool = False
        z_index: int = 0
        zz_index: int = 0
        """
        zz_index contains the number of parents and will be set
        automatically.

        :meta private:
        """

    @dataclass
    class Dependencies(Component.Dependencies):
        canvas: Canvas

    def on_init(self):
        super().on_init()
        self.subscribe('on_draw', self.dependencies.canvas)

    def on_draw(self, context):
        """
        By inheriting from this component and overwriting this method you
        can add additional draw commands to the cairo context.

        Remember to call :code:`super().on_draw(context)` if you want to
        inherit drawing behaviour.

        Args:
            context: The cairo context to draw on.
        """

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
        mouse_cursor: Literal[
            '',
            'default',
            'crosshair',
            'hand',
            'help',
            'no',
            'size',
            'size_down',
            'size_down_left',
            'size_down_right',
            'size_left',
            'size_left_right',
            'size_right',
            'size_up',
            'size_up_down',
            'size_up_left',
            'size_up_right',
            'text',
            'wait',
            'wait_arrow',
        ] = ''
        """
        See the
        `pyglet documentation
        <https://pyglet.readthedocs.io/en/latest/programming_guide/mouse.html#changing-the-mouse-cursor>`_
        for the possible values.
        """

    @dataclass
    class Dependencies(DrawableComponent.Dependencies):
        mouse_control: MouseControl

    @property
    def cursor_whish(self):
        return self.properties.mouse_cursor

    def on_init(self):
        super().on_init()
        self.subscribe('on_mouse_release', self.dependencies.mouse_control)
        self.subscribe('on_mouse_motion', self.dependencies.mouse_control)
        self._hover = False

    def on_destroy(self):
        mouse_control = self.dependencies.mouse_control
        mouse_control.focus_exit(self)
        super().on_destroy()

    def on_mouse_enter(self):
        self._hover = True
        self.style_classes.add(self.STYLE_CLASS_HOVER)

        mouse_control = self.dependencies.mouse_control
        mouse_control.focus_enter(self)

    def on_mouse_focus(self):
        self.style_classes.add(self.STYLE_CLASS_FOCUS)

    def on_mouse_unfocus(self):
        self.style_classes.discard(self.STYLE_CLASS_FOCUS)

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
    """
    Base class for containers that are compatible with the builtin layouts.
    """

    @dataclass
    class Properties(UIComponent.Properties):
        """ """
        layout: str = "stack"

    @dataclass
    class Dependencies(UIComponent.Dependencies):
        """ """
        pass

    @property
    def content_position(self):
        """
        The Area within this container to palce contained components.
        """
        return self.properties.position

    @property
    def wrap_size(self):
        """
        The wrap size is the additional size for each direction that this
        component needs around its content.
        """
        return Rectangle(0, 0, 0, 0)

    @property
    def width(self):
        return self.properties.position.width

    @property
    def height(self):
        return self.properties.position.height


@component("div")
class Div(Container):
    """
    A simple container with a border, margin, padding and a background color.
    """

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


@component("button", style=res.style_file('styles.yml'))
class Button(Div):
    @dataclass
    class Properties(Div.Properties):
        pass

    @dataclass
    class Dependencies(Div.Dependencies):
        pass
