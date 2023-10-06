from guiml._components import Component
from guiml.registry import component
from guiml.injectables import *
import cairocffi as cairo
import functools
from dataclasses import dataclass
import pyglet
import ctypes
from pyglet import app, clock, gl, image, window
from pyglet.window import key as pyglet_key

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

@injectable("window")
class TextControl(Injectable):
  def on_init(self):
    self.on_text = Observable()
    self.on_text_motion = Observable()
    self.on_text_motion_select = Observable()


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
        text_control: TextControl


    def on_init(self):
        super().on_init()
        self.init_window()
        self.init_canvas()
        self.register_mouse_events()

        self.fps_display = pyglet.window.FPSDisplay(window=self.window)

        self._ui_loop_on_update_subscription = \
            self.dependencies.ui_loop.on_update.subscribe(self.on_update)

    def remap_mouse_pos(self, callable, x, y, *args, **kwargs):
        # pyglet uses bot left as origin, swapt origin to top right
        return callable(x, self.properties.height - y, *args, **kwargs)

    def on_text(self, text):
        self.dependencies.text_control.on_text(text)

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
        args["vsync"] = False
        self.window = pyglet.window.Window(**args)
        self.window.set_location(self.properties.left, self.properties.top)

        self.window.push_handlers(on_draw = self.on_draw)
        self.window.push_handlers(on_text = self.dependencies.text_control.on_text)
        self.window.push_handlers(on_text_motion = self.dependencies.text_control.on_text_motion)
        self.window.push_handlers(on_text_motion_select = self.dependencies.text_control.on_text_motion_select)

    def on_draw(self):
        self.window.clear()
        # draw the texture
        self.texture.blit(0, 0)
        self.fps_display.draw()

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
        self.dependencies.canvas.on_context_change(self.context)

    def clear(self):
        self.context.set_operator(cairo.OPERATOR_CLEAR)
        self.context.rectangle(0, 0, self.properties.width, self.properties.height)
        self.context.fill()

        self.context.set_operator(cairo.OPERATOR_OVER)

    def on_update(self, dt):
        self.clear()
        self.dependencies.canvas.draw()

        # Update texture from sruface data
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture.id)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA,
            self.properties.width, self.properties.height, 0, gl.GL_BGRA,
            gl.GL_UNSIGNED_BYTE, self.surface_data)