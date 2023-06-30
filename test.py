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

class MergeError(Exception):
    pass

def merge_data(a, b):
    """
    Merges b into a, b taking precedence. b is not modified.
    """

    if isinstance(a, list) and isinstance(b, list):
        return b + a
    elif isinstance(a, dict) and isinstance(b, dict):
        result = dict(**a)
        for key, value in b.items():
            if key in result:
                result[key] = merge_data(result[key], value)
            else:
                result[key] = value

        return result
    else:
        return b

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
        text: str = ""

    def __init__(self, properties):
        self.properties = properties

    def draw(self, ctx):
        color = self.properties.color
        ctx.set_source_rgb(color.red, color.green, color.blue)
        ctx.set_font_size(self.properties.font_size)
        ctx.select_font_face("Arial",
                             cairo.FONT_SLANT_NORMAL,
                             cairo.FONT_WEIGHT_NORMAL)
        ctx.move_to(self.properties.position.left, self.properties.position.top)
        ctx.show_text(self.properties.text)

class ComponentManager:
    def __init__(self):
        self.reload_styles()
        self.reload_markup()

    def get_properties(self, node, component_cls):
        converter = make_converter()

        data = {}


        data = merge_data(data, self.style.get(node.tag, {}))

        classes = node.get("class")
        if classes:
            classes = classes.split(" ")
            # let earlier mention have precedence
            classes.reverse()
            for style_class in classes:
                data = merge_data(data, self.style.get(".%s"%(style_class), {}))

        tag_id = node.get("id")
        if tag_id:
            data = merge_data(data, self.style.get("$%s"%(tag_id), {}))

        return converter.structure(data, component_cls.Properties)

    def mk_component(self, node):
        if node.tag not in _components:
            return

        component_cls = _components[node.tag]
        properties = self.get_properties(node, component_cls)

        return component_cls(properties)

    def reload_styles(self):
        with open("styles.yml", "r") as f:
            self.style = yaml.load(f, Loader = yaml.BaseLoader)

    def reload_markup(self):
        self.tree = ET.parse('gui.xml')
        wrapText(self.tree.getroot())

    def update(self):
        self.reload_styles()
        self.reload_markup()

        self.components = list()

        queue = list()
        queue.append(self.tree.getroot())
        while queue:
            node = queue.pop()
            component = self.mk_component(node)
            if component:
                self.components.append(component)

            for child in node:
                queue.append(child)

class GUI:
    @dataclass
    class Properties:
        width: int = 400
        height: int = 400

    def __init__(self, window, properties, components):
        self.properties = properties

        self.components = components

        width = self.properties.width
        height = self.properties.height

        # Create texture backed by ImageSurface
        self.surface_data = (ctypes.c_ubyte * (width * height * 4))()
        surface = cairo.ImageSurface.create_for_data(self.surface_data, cairo.FORMAT_ARGB32, width, height, width * 4);
        self.texture = image.Texture.create(width, height, gl.GL_TEXTURE_2D, gl.GL_RGBA)
        self.texture.tex_coords = (0, 1, 0) + (1, 1, 0) + (1, 0, 0) + (0, 0, 0)

        self.ctx = cairo.Context(surface)

        self.update(0)
        window.push_handlers("on_draw", self.on_draw)

        clock.schedule_interval(self.update, 0.1)

    def on_draw(self):
        # draw the texture
        self.texture.blit(0, 0)

    def clear(self):
        self.ctx.set_operator(cairo.Operator.CLEAR)
        self.ctx.rectangle(0, 0, self.properties.width, self.properties.height)
        self.ctx.fill()

        self.ctx.set_operator(cairo.Operator.OVER)

    def update(self, dt):
        self.clear()

        self.components.update()

        for component in self.components.components:
            component.draw(self.ctx)

        # Update texture from sruface data
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture.id)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA,
            self.properties.width, self.properties.height, 0, gl.GL_BGRA,
            gl.GL_UNSIGNED_BYTE, self.surface_data)


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
    manager = ComponentManager()

    gui = GUI(window, GUI.Properties(), manager)

    # run on draw first, i.e., push it as last handler
    window.push_handlers("on_draw", on_draw)
    app.run()

if __name__ == '__main__':
    main()