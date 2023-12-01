from dataclasses import dataclass
from collections import namedtuple

import cairocffi as cairo
import pangocffi as pango
import pangocairocffi as pangocairo
from pangocffi import pango as pango_c

from pyglet.window import key as pyglet_key
from guiml.registry import component

# from guimlcomponents.base.container import *
# from guimlcomponents.base.window import

from guimlcomponents.base.container import UIComponent, Div

from guimlcomponents.base.window import (
        Canvas,
        MouseControl,
        TextControl
    )

from guimlcomponents.base.shared import resources as res

from guiml.injectables import Injectable, injectable

from typing import Optional, Callable


def escape(str_xml: str):
    str_xml = str_xml.replace("&", "&amp;")
    str_xml = str_xml.replace("<", "&lt;")
    str_xml = str_xml.replace(">", "&gt;")
    str_xml = str_xml.replace("\"", "&quot;")
    str_xml = str_xml.replace("'", "&apos;")
    return str_xml


def unescape(str_xml: str):
    str_xml = str_xml.replace("&lt;", "<")
    str_xml = str_xml.replace("&gt;", ">")
    str_xml = str_xml.replace("&quot;", "\"")
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
        subscription = self.canvas.on_context_change.subscribe(
            self.on_canvas_context_change)
        self._on_context_change = subscription

    def on_destroy(self):
        self._on_context_change.cancel()

    def on_canvas_context_change(self, context):
        self.context = pangocairo.create_context(context)


TextExtents = namedtuple(
    "TextExtents", 'x_bearing y_bearing width height x_advance y_advance')


def get_extent(text, font_size):
    fontFace = cairo.ToyFontFace("Arial", cairo.FONT_SLANT_NORMAL,
                                 cairo.FONT_WEIGHT_NORMAL)
    fontMatrix = cairo.Matrix()
    fontMatrix.scale(font_size, font_size)
    user2device = cairo.Matrix()
    options = cairo.FontOptions()

    font = cairo.ScaledFont(fontFace, fontMatrix, user2device, options)
    return TextExtents(*font.text_extents(text))


@component("text", style=res.style_file('styles.yml'))
class Text(UIComponent):

    @dataclass
    class Properties(UIComponent.Properties):
        text: str = ''
        """The text to display."""
        apply_markup: bool = True
        """Whether to apply pango markup or to escape it."""
        selectable: bool = True
        """
        Whether the text can be selected. You can also use the class no_select
        to set this value, while also adjusting the style accordingly.
        """

    @dataclass
    class Dependencies(UIComponent.Dependencies):
        pango: PangoContext
        mouse_control: MouseControl

    def on_init(self):
        super().on_init()

        self.selection_start = None
        self.selection_end = None

        self.subscribe('on_mouse_press', self.dependencies.mouse_control)
        self.subscribe('on_mouse_drag', self.dependencies.mouse_control)

        self.last_click_index = None

    def on_destroy(self):
        self.cancel_subscriptions()

    def get_raw_text(self):
        # todo strip text from formatting for selection to work properly
        return self.get_input_text()

    def get_input_text(self):
        return self.properties.text

    def get_display_text(self):
        # return self.get_input_text()
        return self.add_selection(self.get_input_text())

    def byte_index_to_str_index(self, index):
        text = self.get_input_text()

        acc = 0
        i = 0
        for i, char in enumerate(text):
            if acc >= index:
                break

            char_size = len(char.encode('utf-8'))
            acc += char_size
        else:
            return i + 1

        return i

    def str_index_to_byte_index(self, index):
        text = self.get_input_text()
        return len(text[:index].encode('utf-8'))

    def has_selection(self):
        return (self.selection_start is not None
                and self.selection_end is not None
                and self.selection_start != self.selection_end)

    def add_selection(self, text):
        if self.has_selection():
            start = min(self.selection_start, self.selection_end)
            stop = max(self.selection_start, self.selection_end)

            return (f'{text[:start]}<span fgcolor="white" bgcolor="blue">'
                    f'{text[start:stop]}</span>{text[stop:]}')
        else:
            return text

    def get_layout(self):
        layout = pango.Layout(self.dependencies.pango.context)

        text = self.get_display_text()
        if not self.properties.apply_markup:
            text = escape(text)

        layout.apply_markup(text)
        return layout

    def index_from_position(self, x, y):
        index = pango.ffi.new("int *")
        trailing = pango.ffi.new("int *")

        didhit = pango_c.pango_layout_xy_to_index(  # noqa: F841
            self.get_layout().pointer,
            pango.units_from_double(x - self.properties.position.left),
            pango.units_from_double(y - self.properties.position.top), index,
            trailing)

        # Index is now the index of the character pressed. For positioning
        # cursor and selection we want to move the cursor by one position if
        # we hit the end of a character.
        index = index[0]

        pos = pango.Rectangle()

        pango_c.pango_layout_index_to_pos(self.get_layout().pointer, index,
                                          pos.pointer)

        if pos.width > 0:
            hitpos = pango.units_from_double(x - self.properties.position.left)
            hitp = (hitpos - pos.x) / (pos.width)
            if hitp > 0.6:
                index += 1

        return index

    def on_mouse_press(self, x, y, button, modifiers):
        if (not self.properties.selectable
                or not self.properties.position.is_inside(x, y)):
            self.selection_start = None
            self.selection_end = None
            self.last_click_index = None
            return

        self.last_click_index = self.byte_index_to_str_index(
            self.index_from_position(x, y))
        self.selection_start = self.last_click_index
        self.selection_end = None

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        if self.last_click_index is None:
            return

        self.last_click_index = self.byte_index_to_str_index(
            self.index_from_position(x, y))
        if self.last_click_index is not None:
            self.selection_end = self.last_click_index

    @property
    def width(self):
        value = self.get_layout().get_size()[0]
        value = pango.units_to_double(value)
        return value

    @property
    def height(self):
        value = self.get_layout().get_size()[1]
        value = pango.units_to_double(value)

        return round(value)

    def on_draw(self, context):
        super().on_draw(context)

        with context:
            context.move_to(self.properties.position.left,
                            self.properties.position.top)
            pat = cairo.SolidPattern(0, 0, 0, 1)
            context.set_source(pat)

            layout = self.get_layout()
            pangocairo.show_layout(context, layout)


@component(name="raw_input")
class RawInput(Text):

    @dataclass
    class Properties(Text.Properties):

        """Text in the input field. The text needs to be bound to a value by
            the calling class, as otherwise the pressed inputs will not be
            stored."""
        text: str = None

        on_text: Optional[Callable] = None
        on_text_hook: Optional[Callable] = None

    @dataclass
    class Dependencies(Text.Dependencies):
        text_control: TextControl

    def on_init(self):
        super().on_init()

        self._cursor_position = None

    def on_destroy(self):
        self.release_text_focus()
        super().on_destroy()

    def get_input_text(self):
        return escape(self.text)

    @property
    def text(self):
        return self.properties.text

    @text.setter
    def text(self, value):
        self.properties.text = value

    @property
    def cursor_position(self):
        return self._cursor_position

    @cursor_position.setter
    def cursor_position(self, value):
        if self._cursor_position is None and value is not None:
            self.take_text_focus()

        self._cursor_position = value

    def remove_selection(self):
        start = min(self.selection_start, self.selection_end)
        end = max(self.selection_start, self.selection_end)

        self.cursor_position = start
        self.text = self.text[:start] + self.text[end:]

        self.selection_start = None
        self.selection_end = None

    def on_text(self, text):
        if text:
            if self.properties.on_text_hook is not None:
                text = self.properties.on_text_hook(text)

            if text:
                if self.has_selection():
                    self.remove_selection()

                self.text = (self.text[:self.cursor_position]
                             + text
                             + self.text[self.cursor_position:])
                self.cursor_position += len(text)

            if self.properties.on_text is not None:
                self.properties.on_text(self.text)

    def on_draw(self, context):
        if self.cursor_position is not None:
            self.cursor_position = min(self.cursor_position, len(self.text))

            with context:
                layout = self.get_layout()
                strong_cursor = pango.Rectangle()
                weak_cursor = pango.Rectangle()

                byte_cursor = self.str_index_to_byte_index(self.cursor_position)
                pango_c.pango_layout_get_cursor_pos(layout.pointer, byte_cursor,
                                                    strong_cursor.pointer,
                                                    weak_cursor.pointer)

                left = pango.units_to_double(
                    strong_cursor.x) + self.properties.position.left
                top = pango.units_to_double(
                    strong_cursor.y) + self.properties.position.top
                width = 2
                height = pango.units_to_double(strong_cursor.height)

                context.rectangle(left, top, width, height)
                pat = cairo.SolidPattern(0, 0, 0, 1)
                context.set_source(pat)
                context.fill()

        super().on_draw(context)

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
        return (self.has_selection()
                and (motion == pyglet_key.MOTION_BACKSPACE
                     or motion == pyglet_key.MOTION_DELETE))

    def on_mouse_press(self, x, y, button, modifiers):
        super().on_mouse_press(x, y, button, modifiers)

        if self.last_click_index is not None:
            self.cursor_position = self.last_click_index

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        super().on_mouse_drag(x, y, dx, dy, button, modifiers)

        if self.last_click_index is not None:
            self.cursor_position = self.last_click_index

    def on_text_motion(self, motion):
        if self.is_remove_selection(motion):
            self.remove_selection()
        else:
            self.selection_start = None
            self.selection_end = None
            if motion == pyglet_key.MOTION_BACKSPACE:
                if self.cursor_position > 0:
                    self.text = self.text[:self.cursor_position -
                                          1] + self.text[self.cursor_position:]
                    self.cursor_position -= 1
                    self.cursor_position = max(self.cursor_position, 0)
            elif motion == pyglet_key.MOTION_DELETE:
                self.text = self.text[:self.cursor_position] + self.text[
                    self.cursor_position + 1:]
            else:
                self.update_cursor_position(motion)

    def on_text_motion_select(self, motion):
        if self.selection_start is None:
            self.selection_start = self.cursor_position

        self.update_cursor_position(motion)
        self.selection_end = self.cursor_position

    def take_text_focus(self):
        text_control = self.dependencies.text_control

        text_control.take_text_focus(self)

        self.text_subscriptions = [
            self.subscribe_unmanaged(event, text_control)
            for event in [
                'on_text',
                'on_text_motion',
                'on_text_motion_select',
                'on_new_text_focus'
            ]
        ]

    def release_text_focus(self):
        if self.cursor_position is not None:
            self.dependencies.text_control.release_text_focus(self)

        for subscription in self.text_subscriptions:
            subscription.cancel()

        self.text_subscriptions = []

        self.cursor_position = None

    def on_new_text_focus(self):
        self.release_text_focus()


@component(
    "input",
    template=res.template("""
        <input>
            <raw_input
                bind_text="self.text"
                on_text_hook="self.on_text_hook"
                on_text="self.on_text">
            </raw_input>
        </input>
    """),
    style=res.style_file('styles.yml'))
class Input(Div):
    @dataclass
    class Properties(Div.Properties):
        text: str = None
        on_submit: Optional[Callable] = None

    @dataclass
    class Dependencies(Div.Dependencies):
        pass

    def on_init(self):
        super().on_init()
        self._text = ''
        self.enter_pressed = False

    def on_destroy(self):
        super().on_destroy()

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

    def on_text_hook(self, text):
        if text == "\n":
            self.enter_pressed = True
            return ''

        return text

    def on_text(self, text):
        if self.enter_pressed:
            self.enter_pressed = False

            if self.properties.on_submit is not None:
                self.properties.on_submit(self.text)
