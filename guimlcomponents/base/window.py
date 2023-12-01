from guiml._components import Component
from guiml.registry import component
from guiml.injectables import Observable, Injectable, injectable, UILoop
import cairocffi as cairo
import functools
from dataclasses import dataclass
import pyglet
import ctypes
from typing import Optional

from pyglet import gl, image
from guimlcomponents.base.shared import Rectangle, Color


@injectable("window")
class Canvas(Injectable):

    def on_init(self):
        # context will be created and set by the window component
        self.context = None
        self.on_draw = Observable()
        self.on_context_change = Observable()

    def draw(self):
        self.on_draw(self.context)


@injectable("window")
class MouseControl(Injectable):

    def on_init(self):
        self.on_mouse_motion = Observable()
        self.on_mouse_press = Observable()
        self.on_mouse_release = Observable()
        self.on_mouse_drag = Observable()
        self.on_mouse_enter = Observable()
        self.on_mouse_leave = Observable()
        self.on_mouse_scroll = Observable()

        self.on_mouse_motion.post_call = self.compute_focus

        self.set_cursor = None

        self.focus = None
        self._hovers = set()

    def focus_enter(self, value):
        self._hovers.add(value)

    def focus_exit(self, value):
        self._hovers.discard(value)

    def compute_focus(self, x, y, dx, dy):
        def get_key(component):
            prop = component.properties
            return (-prop.z_index, -prop.zz_index)

        if not self._hovers:
            new_focus = None
        else:
            new_focus = min(self._hovers, key=get_key)
            if new_focus != self.focus:
                fn = getattr(self.focus, 'on_mouse_unfocus', None)
                if fn is not None:
                    fn()

                fn = getattr(new_focus, 'on_mouse_focus', None)
                if fn is not None:
                    fn()

                self.focus = new_focus

            with_cursor = set((component for component in self._hovers
                              if getattr(component, 'cursor_whish', '')))
            if with_cursor:
                new_focus_with_cursor = min(with_cursor, key=get_key)
                self.set_cursor(new_focus_with_cursor.cursor_whish)
            else:
                self.set_cursor(None)


@injectable("window")
class TextControl(Injectable):

    def on_init(self):
        self._focus = None

        self.on_text = Observable()
        self.on_text_motion = Observable()
        self.on_text_motion_select = Observable()
        self.on_new_text_focus = Observable()

    def take_text_focus(self, component):
        if component != self._focus:
            self.on_new_text_focus()

            assert self._focus is None, \
                   'Text focus should have been released.'

            self._focus = component

    def release_text_focus(self, component):
        assert self._focus == component, \
               'Text focus released without having it.'

        self._focus = None


@component("window")
class Window(Component):

    @dataclass
    class Properties:
        width: int = 400
        height: int = 400
        resizable: bool = False

        top: int = 500
        left: int = 2000

        @property
        def position(self):
            return Rectangle(0, 0, self.height, self.width)

        @position.setter
        def position(self, value):
            pass

        background: Optional[Color] = Color(1, 1, 1, 1)
        """Background color to draw or None to draw nothing"""

        layout: str = "stack"
        show_fps: bool = False

    @dataclass
    class Dependencies:
        canvas: Canvas
        ui_loop: UILoop
        mouse_control: MouseControl
        text_control: TextControl

    def on_init(self):
        super().on_init()
        self.init_window()
        self.init_canvas()
        self.setup_mouse_control()

        self.fps_display = pyglet.window.FPSDisplay(window=self.window)

        self._ui_loop_on_update_subscription = \
            self.dependencies.ui_loop.on_update.subscribe(self.on_update)

        self._on_draw_subscription = \
            self.dependencies.canvas.on_draw.subscribe(self.on_draw)

    @property
    def content_position(self):
        return self.properties.position

    @property
    def wrap_size(self):
        return Rectangle(0, 0, 0, 0)

    def remap_mouse_pos(self, callable, x, y, *args, **kwargs):
        # pyglet uses bot left as origin, swapt origin to top right
        return callable(x, self.properties.height - y, *args, **kwargs)

    def on_text(self, text):
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")
        self.dependencies.text_control.on_text(text)

    def set_mouse_cursor(self, value):
        cursor = self.window.get_system_mouse_cursor(value)
        self.window.set_mouse_cursor(cursor)

    def setup_mouse_control(self):
        self.register_mouse_events()

        mouse_control = self.dependencies.mouse_control
        mouse_control.set_cursor = self.set_mouse_cursor

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
            event:
            functools.partial(self.remap_mouse_pos,
                              getattr(self.dependencies.mouse_control, event))
            for event in mouse_events
        }

        self.window.push_handlers(**args)

    # def on_destroy(self):
    #     self._ui_loop_on_update_subscription.cancel()

    def init_window(self):
        args = {
            key: getattr(self.properties, key)
            for key in ["width", "height", "resizable"]
        }
        args["vsync"] = False
        self.window = pyglet.window.Window(**args)
        self.window.set_location(self.properties.left, self.properties.top)

        self.window.push_handlers(on_draw=self.on_window_draw)
        self.window.push_handlers(
            on_text=self.on_text)
        self.window.push_handlers(
            on_text_motion=self.dependencies.text_control.on_text_motion)
        self.window.push_handlers(on_text_motion_select=self.dependencies.
                                  text_control.on_text_motion_select)

    def on_window_draw(self):
        self.window.clear()
        # draw the texture
        self.texture.blit(0, 0)
        if self.properties.show_fps:
            self.fps_display.draw()

    def on_draw(self, ctx):
        with ctx:
            if self.properties.background is not None:
                ctx.new_path()

                top = self.properties.position.top
                left = self.properties.position.left
                bottom = self.properties.position.bottom
                right = self.properties.position.right

                ctx.rectangle(left, top, right - left, bottom - top)

                color = self.properties.background
                pat = cairo.SolidPattern(color.red, color.green, color.blue,
                                         color.alpha)
                ctx.set_source(pat)
                ctx.fill()

    def init_canvas(self):
        width = self.properties.width
        height = self.properties.height

        # Create texture backed by ImageSurface
        self.surface_data = (ctypes.c_ubyte * (width * height * 4))()
        surface = cairo.ImageSurface.create_for_data(self.surface_data,
                                                     cairo.FORMAT_ARGB32,
                                                     width, height, width * 4)
        self.texture = image.Texture.create(width, height, gl.GL_TEXTURE_2D,
                                            gl.GL_RGBA)
        self.texture.tex_coords = (0, 1, 0) + (1, 1, 0) + (1, 0, 0) + (0, 0, 0)

        self.context = cairo.Context(surface)
        self.dependencies.canvas.context = self.context
        self.dependencies.canvas.on_context_change(self.context)

    def clear(self):
        self.context.set_operator(cairo.OPERATOR_CLEAR)
        self.context.rectangle(0, 0, self.properties.width,
                               self.properties.height)
        self.context.fill()

        self.context.set_operator(cairo.OPERATOR_OVER)

    def on_update(self, dt):
        self.clear()
        self.dependencies.canvas.draw()

        # Update texture from sruface data
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture.id)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, self.properties.width,
                        self.properties.height, 0, gl.GL_BGRA,
                        gl.GL_UNSIGNED_BYTE, self.surface_data)
