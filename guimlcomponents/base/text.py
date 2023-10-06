import cairocffi as cairo
import pangocffi as pango
import pangocairocffi as pangocairo

from pangocffi import pango as pango_c

from collections import namedtuple
from guiml.registry import component

from guimlcomponents.base.container import *
from guimlcomponents.base.window import *

from typing import Optional, Callable

def escape( str_xml: str ):
    str_xml = str_xml.replace("&", "&amp;")
    str_xml = str_xml.replace("<", "&lt;")
    str_xml = str_xml.replace(">", "&gt;")
    str_xml = str_xml.replace("\"", "&quot;")
    str_xml = str_xml.replace("'", "&apos;")
    return str_xml

def unescape( str_xml: str ):
    str_xml = str_xml.replace("&lt;", "<")
    str_xml = str_xml.replace("&gt;", ">")
    str_xml = str_xml.replace( "&quot;", "\"")
    str_xml = str_xml.replace("&apos;", "'")
    str_xml = str_xml.replace("&amp;", "&")
    return str_xml

@injectable("window")
class PangoContext(Injectable):
    @dataclass
    class Dependencies:
        canvas: Canvas

    def on_init(self):
        super().on_init()
        subscription = self.canvas.on_context_change.subscribe(self.on_canvas_context_change)
        self._on_context_change = subscription

    def on_destroy(self):
        self._on_context_change.cancel()

    def on_canvas_context_change(self, context):
        self.context = pangocairo.create_context(context)

TextExtents = namedtuple("TextExtents", 'x_bearing y_bearing width height x_advance y_advance')

def get_extent(text, font_size):
    fontFace = cairo.ToyFontFace("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    fontMatrix = cairo.Matrix()
    fontMatrix.scale(font_size, font_size)
    user2device = cairo.Matrix()
    options = cairo.FontOptions()

    font = cairo.ScaledFont(fontFace, fontMatrix, user2device, options)
    return TextExtents(*font.text_extents(text))

# @component(
#     name = "input",
#     template = """<template><text py_text="self.escaped_text"></text></template>"""
# )
class Input(Div):
    @dataclass
    class Properties(Div.Properties):
        text: str = None
        on_text: Optional[Callable] = None

    @dataclass
    class Dependencies(Div.Dependencies):
        text_control: TextControl

    @property
    def escaped_text(self):
        return escape(self.text)

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

            if self.properties.on_text is not None:
                self.properties.on_text(self.text)

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


@component("text")
class Text(DrawableComponent):
    @dataclass
    class Properties(DrawableComponent.Properties):
        text: str = ''
        apply_markup: bool = True

    @dataclass
    class Dependencies(DrawableComponent.Dependencies):
        pango: PangoContext

    def get_display_text(self):
        return self.properties.text

    def get_layout(self):
        layout = pango.Layout(self.dependencies.pango.context)

        text = self.get_display_text()
        if not self.properties.apply_markup:
            text = escape(text)

        layout.apply_markup(text)
        return layout

    @property
    def width(self):
        value = self.get_layout().get_size()[0]
        value = pango.units_to_double(value)
        return value

    @property
    def height(self):
        value = self.get_layout().get_size()[1]
        value = pango.units_to_double(value)
        return value

    def on_draw(self, context):
        super().on_draw(context)

        with context:
            context.move_to(self.properties.position.left, self.properties.position.top)
            pat = cairo.SolidPattern(0, 0, 0, 1)
            context.set_source(pat)

            layout = self.get_layout()
            pangocairo.show_layout(context, layout)

        # 4.1) Layout::xy_to_index
        # 4.2) Layout::index_to_*
        # 4.3) Layout::get_cursor_pos
        # 4.4) Layout::get_caret_pos

@component(name = "input")
class RawInput(Text, Subscriber):
    @dataclass
    class Properties(Text.Properties):
        text: str = None
        on_text: Optional[Callable] = None

    @dataclass
    class Dependencies(Text.Dependencies):
        text_control: TextControl

    def on_init(self):
        super().on_init()

        self._text = ""
        self.cursor_position = 0

        self.selection_start = 1
        self.selection_end = 4

        text_control = self.dependencies.text_control
        self.subscribe('on_text', text_control)
        self.subscribe('on_text_motion', text_control)
        self.subscribe('on_text_motion_select', text_control)

    def on_destroy(self):
        self.cancel_subscriptions()

    def get_display_text(self):
        text = escape(self.text)

        if self.selection_start is not None:
            start = min(self.selection_start, self.selection_end)
            stop = max(self.selection_start, self.selection_end)

            return f'{text[:start]}<span fgcolor="white" bgcolor="blue">{text[start:stop]}</span>{text[stop:]}'

        else:
            return text

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

    def remove_selection(self):
        start = min(self.selection_start, self.selection_end)
        end = max(self.selection_start, self.selection_end)

        self.cursor_position = start
        self.text = self.text[:start] + self.text[end:]

        self.selection_start = None
        self.selection_end = None

    def on_text(self, text):
        if text:
            if self.selection_start is not None:
                self.remove_selection()

            self.text = self.text[:self.cursor_position] + text + self.text[self.cursor_position:]
            self.cursor_position += len(text)

            if self.properties.on_text is not None:
                self.properties.on_text(self.text)

    def on_draw(self, context):
        self.cursor_position = min(self.cursor_position, len(self.text))

        super().on_draw(context)

        with context:
            layout = self.get_layout()
            strong_cursor = pango.Rectangle()
            weak_cursor = pango.Rectangle()

            pango_c.pango_layout_get_cursor_pos(
                layout.pointer, self.cursor_position, strong_cursor.pointer, weak_cursor.pointer)

            left = pango.units_to_double(strong_cursor.x) + self.properties.position.left
            top = pango.units_to_double(strong_cursor.y) + self.properties.position.top
            width = 2
            height = pango.units_to_double(strong_cursor.height)

            context.rectangle(left, top, width, height)
            pat = cairo.SolidPattern(0, 0, 0, 1)
            context.set_source(pat)
            context.fill()

    def update_cursor_position(self, motion):
        if motion == pyglet_key.MOTION_LEFT:
            self.cursor_position -= 1
            self.cursor_position = max(self.cursor_position, 0)
        elif motion == pyglet_key.MOTION_RIGHT:
            self.cursor_position += 1
            self.cursor_position = min(self.cursor_position, len(self.text))
        elif motion == pyglet_key.MOTION_BEGINNING_OF_LINE:
            self.cursor_position = 0
        elif motion == pyglet_key.MOTION_END_OF_LINE:
            self.cursor_position = len(self.text)

    def is_remove_selection(self, motion):
        return (self.selection_start is not None
            and (
                motion == pyglet_key.MOTION_BACKSPACE
                or motion == pyglet_key.MOTION_DELETE
            ))

    def on_text_motion(self, motion):
        if self.is_remove_selection(motion):
            self.remove_selection()
        else:
            self.selection_start = None
            self.selection_end = None
            if motion == pyglet_key.MOTION_BACKSPACE:
                if self.cursor_position > 0:
                    self.text = self.text[:self.cursor_position - 1] + self.text[self.cursor_position:]
                    self.cursor_position -= 1
                    self.cursor_position = max(self.cursor_position, 0)
            elif motion == pyglet_key.MOTION_DELETE:
                self.text = self.text[:self.cursor_position] + self.text[self.cursor_position + 1:]
            else:
                self.update_cursor_position(motion)

    def on_text_motion_select(self, motion):
        if self.selection_start is None:
            self.selection_start = self.cursor_position

        self.update_cursor_position(motion)
        self.selection_end = self.cursor_position
