from guiml.components import *
from guiml.components import component

from guiml.injectables import UILoop

from guimlcomponents.base.injectables import *

class DrawableComponent(Container):
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

@component("div")
class Div(DrawableComponent):
    @dataclass
    class Properties(Container.Properties):
        border: Border = field(default_factory = Border)
        margin: Rectangle = field(default_factory = Rectangle)
        padding: Rectangle = field(default_factory = Rectangle)
        background: Color = field(default_factory = Color)

    @property
    def content_position(self):
        bwidth = self.properties.border.width / 2
        top = self.properties.position.top + self.properties.margin.top + bwidth + self.properties.padding.top
        left = self.properties.position.left + self.properties.margin.left + bwidth + self.properties.padding.left
        bottom = self.properties.position.bottom - self.properties.margin.bottom - bwidth - self.properties.padding.bottom
        right = self.properties.position.right - self.properties.margin.right - bwidth - self.properties.padding.right

        return Rectangle(top, left, bottom, right)

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

TextExtents = namedtuple("TextExtents", 'x_bearing y_bearing width height x_advance y_advance')

def get_extent(text, font_size):
    fontFace = cairo.ToyFontFace("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    fontMatrix = cairo.Matrix()
    fontMatrix.scale(font_size, font_size)
    user2device = cairo.Matrix()
    options = cairo.FontOptions()

    font = cairo.ScaledFont(fontFace, fontMatrix, user2device, options)
    return TextExtents(*font.text_extents(text))

@component(
    name = "input",
    template = """<template><text py_text="self.text"></text></template>"""
)
class Input(Div):
    @dataclass
    class Properties(Div.Properties):
        text: str = None

    @dataclass
    class Dependencies(Div.Dependencies):
        text_control: TextControl

    @property
    def text(self):
        if self.properties.text is not None:
            return self.properties.text
        else:
            return self._text

    @text.setter
    def text(self, value):
        if self.properties.text is not None:
            self.properties.text = value
        else:
            self._text = value

    def on_init(self):
        super().on_init()
        self._text = ""
        self.cursor_position = 0
        text_control = self.dependencies.text_control
        subscription = text_control.on_text.subscribe(self.on_text)
        self._on_text_subscription = subscription
        subscription = text_control.on_text_motion.subscribe(self.on_text_motion)
        self._on_text_motion_subscription = subscription

    def on_text(self, text):
        if text:
            self.text = self.text[:self.cursor_position] + text + self.text[self.cursor_position:]
            self.cursor_position += len(text)

    def on_draw(self, context):
        super().on_draw(context)

        with context:
            font_size = 14
            cursor_x_position = get_extent(self.text[:self.cursor_position], font_size).x_advance

            content = self.content_position
            cursor_width = 2

            context.rectangle(content.left + cursor_x_position, content.top + 2, cursor_width, font_size)
            pat = cairo.SolidPattern(0, 0, 0, 1)
            context.set_source(pat)
            context.fill()

    def on_text_motion(self, motion):
        if motion == pyglet_key.MOTION_BACKSPACE:
            if self.cursor_position > 0:
                self.text = self.text[:self.cursor_position - 1] + self.text[self.cursor_position:]
                self.cursor_position -= 1
                self.cursor_position = max(self.cursor_position, 0)
        elif motion == pyglet_key.MOTION_DELETE:
            self.text = self.text[:self.cursor_position] + self.text[self.cursor_position + 1:]

        elif motion == pyglet_key.MOTION_LEFT:
            self.cursor_position -= 1
            self.cursor_position = max(self.cursor_position, 0)
        elif motion == pyglet_key.MOTION_RIGHT:
            self.cursor_position += 1
            self.cursor_position = min(self.cursor_position, len(self.text))
        elif motion == pyglet_key.MOTION_BEGINNING_OF_LINE:
            self.cursor_position = 0
        elif motion == pyglet_key.MOTION_END_OF_LINE:
            self.cursor_position = len(self.text)



    def on_destroy(self):
        self._on_text_subscription.cancel()
        self._on_text_motion_subscription.cancel()


#@component("text")
class Text(DrawableComponent):
    @dataclass
    class Properties(Container.Properties):
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

@component("text")
class Text(DrawableComponent):
    @dataclass
    class Properties(Container.Properties):
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

    def on_draw(self, context):
        super().on_draw(context)

        assert(self.properties.position.is_valid())

        with context:
            context.new_path()

            context.rectangle(self.properties.position.left, self.properties.position.top, self.properties.position.width, self.properties.position.height)
            context.set_line_width(1)
            context.set_source(cairo.SolidPattern(0, 1, 0, 1))
            context.stroke()

        with context:
            context.move_to(self.properties.position.left, self.properties.position.top)
            pat = cairo.SolidPattern(0, 0, 0, 1)
            context.set_source(pat)

            layout = pangocairo.create_layout(context)
            layout.width = pango.units_from_double(self.properties.position.width)
            # print(self.properties.position.width)
            #layout.height = pango.units_from_double(self.properties.position.height)
            layout.apply_markup(self.properties.text)
            pangocairo.show_layout(context, layout)

        # todo:
        # 1) Create a recording surface https://doc.courtbouillon.org/cairocffi/stable/api.html#cairocffi.RecordingSurface
        # 2) Create a layout and write text into the recording surface https://pangocairocffi.readthedocs.io/en/latest/overview.html
        # 3) Draw recording surface into the actual surface.
        # 4) Implement missing methods from Layout https://docs.gtk.org/Pango/class.Layout.html
        # 4.1) Layout::xy_to_index
        # 4.2) Layout::index_to_*
        # 4.3) Layout::get_cursor_pos
        # 4.4) Layout::get_caret_pos

