import ctypes
import cairo
import xml.etree.ElementTree as ET
import sys
import yaml

from cattrs.preconf.pyyaml import make_converter

from dataclasses import dataclass, field

from pyglet import app, clock, gl, image, window

_components = {}

def component(name):
    def register(cls):
        _components[name] = cls
        return cls

    return register

@dataclass
class Color:
    red: float = 0.
    green: float = 0.
    blue: float = 0.
    alpha: float = 1.

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

@dataclass
class WidgetProperty:
    # bounding box for registering clicks
    position: Rectangle = field(default_factory = Rectangle)

@component("div")
class Div:
    @dataclass
    class Properties(WidgetProperty):
        border: Border = field(default_factory = Border)
        margin: Rectangle = field(default_factory = Rectangle)
        padding: Rectangle = field(default_factory = Rectangle)
        background: Color = field(default_factory = Color)

    def __init__(self, properties):
        self.properties = properties

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

@component("text")
class Text:
    @dataclass
    class Properties(WidgetProperty):
        font_size: int = 0
        color: Color = field(default_factory = Color)

    def __init__(self, properties, data):
        self.properties = properties
        self.text = data

    def draw(self, ctx):
        ctx.set_source_rgb(color.red, color.green, color.blue)
        ctx.set_font_size(self.properties.font_size)
        ctx.select_font_face("Arial",
                             cairo.FONT_SLANT_NORMAL,
                             cairo.FONT_WEIGHT_NORMAL)
        ctx.move_to(self.properties.position.left, self.properties.position.top)
        ctx.show_text(self.text)

class GUI:
    @dataclass
    class Properties:
        width: int = 400
        height: int = 400

    def __init__(self, window, properties):
        self.properties = properties

        width = self.properties.width
        height = self.properties.height

        # Create texture backed by ImageSurface
        self.surface_data = (ctypes.c_ubyte * (width * height * 4))()
        surface = cairo.ImageSurface.create_for_data(self.surface_data, cairo.FORMAT_ARGB32, width, height, width * 4);
        self.texture = image.Texture.create(width, height, gl.GL_TEXTURE_2D, gl.GL_RGBA)
        self.texture.tex_coords = (0, 1, 0) + (1, 1, 0) + (1, 0, 0) + (0, 0, 0)

        self.ctx = cairo.Context(surface)

        window.push_handlers("on_draw", self.on_draw)
        clock.schedule_interval(self.update, 0.5)

    def on_draw(self):
        # Update texture from sruface data
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture.id)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA,
            self.properties.width, self.properties.height, 0, gl.GL_BGRA,
            gl.GL_UNSIGNED_BYTE, self.surface_data)

        # draw the texture
        self.texture.blit(0, 0)

    def reload_styles(self):
        with open("styles.yml", "r") as f:
            self.style = yaml.load(f, Loader = yaml.BaseLoader)

    def reload_markup(self):
        self.tree = ET.parse('gui.xml')
        wrapText(self.tree.getroot())

    def update(self, dt):
        self.reload_styles()
        self.reload_markup()

        converter = make_converter()
        properties = converter.structure(self.style["div"], Div.Properties)

        component = Div(properties)
        component.draw(self.ctx)


def addText(element, text, position):
    if text:
        text = text.strip()

    if text:
        txt = ET.Element('text')
        txt.text = text

        element.insert(position, txt)

def wrapText(node):
    queue = list()
    queue.append(node)
    while queue:
        element = queue.pop()
        if element.tag != "text":
            addText(element, element.text, 0)
            element.text = None

            for i, child in enumerate(element):
                queue.append(child)
                addText(element, child.tail, i + 1)
                child.tail = None

window = window.Window(width = 400, height = 400)

def on_draw():
    window.clear()

def main():
    gui = GUI(window, GUI.Properties())

    # run on draw first, i.e., push it as last handler
    window.push_handlers("on_draw", on_draw)
    app.run()

if __name__ == '__main__':
    main()