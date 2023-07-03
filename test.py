import ctypes
import cairo
import xml.etree.ElementTree as ET
import sys
import yaml

import copy

from cattrs.preconf.pyyaml import make_converter

from dataclasses import dataclass, field

from pyglet import app, clock, gl, image, window

from typing import Optional

import os

_components = {}

def component(name):
    def register(cls):
        _components[name] = cls
        return cls

    return register

_layouts = {}

def layout(name):
    def register(cls):
        _layouts[name] = cls
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
        return self.bottom - self.right

@dataclass
class WidgetProperty:
    # bounding box for registering clicks
    position: Rectangle = field(default_factory = Rectangle)

class Component:
    def __init__(self, properties):
        self.properties = properties

        self.on_init()

    def on_init(self):
        pass

@component("div")
class Div(Component):
    @dataclass
    class Properties(WidgetProperty):
        border: Border = field(default_factory = Border)
        margin: Rectangle = field(default_factory = Rectangle)
        padding: Rectangle = field(default_factory = Rectangle)
        background: Color = field(default_factory = Color)

        layout: str = ""

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

def get_extent(text, font_size):
    fontFace = cairo.ToyFontFace("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    fontMatrix = cairo.Matrix()
    fontMatrix.scale(font_size, font_size)
    user2device = cairo.Matrix()
    options = cairo.FontOptions()

    font = cairo.ScaledFont(fontFace, fontMatrix, user2device, options)
    return font.text_extents(text)


@component("text")
class Text(Component):
    @dataclass
    class Properties(WidgetProperty):
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

    def draw(self, ctx):
        color = self.properties.color
        ctx.set_source_rgb(color.red, color.green, color.blue)
        ctx.set_font_size(self.properties.font_size)
        ctx.select_font_face("Arial",
                             cairo.FONT_SLANT_NORMAL,
                             cairo.FONT_WEIGHT_NORMAL)
        ctx.move_to(self.properties.position.left, self.properties.position.top + self.height)
        ctx.show_text(self.properties.text)

@layout("hflow")
class HorizontalFlow:
    @dataclass
    class Properties(WidgetProperty):
        pass

    @dataclass
    class ChildProperties(WidgetProperty):
        pass

    def __init__(self, properties):
        self.properties = properties

    def layout(self, children):
        width = self.properties.position.width
        height = self.properties.position.height

        posx = self.properties.position.left
        posy = self.properties.position.top
        max_height = 0

        for child in children:
            if posx + child.width > self.properties.position.right:
                posx = self.properties.position.left
                posy += max_height
                max_height = 0

            position = child.properties.position
            position.top = posy
            position.left = posx

            posx += child.width
            max_height = max(max_height, child.height)

            position.bottom = posx
            position.right = posy + child.height


@layout("grid")
class GridLayout:
    @dataclass
    class Properties(WidgetProperty):
        rows: int = 1
        columns: int = 1

    @dataclass
    class ChildProperties(WidgetProperty):
        row: int = 0
        rowspan: int = 1
        column: int = 0
        colspan: int = 1

    def __init__(self, properties):
        self.properties = properties

    def layout(self, children):
        assert(self.properties.position.is_valid())

        position = self.properties.position
        width = position.right - position.left
        height = position.bottom - position.top

        col2pos = lambda col: col * (width / self.properties.columns)
        row2pos = lambda row: row * height / self.properties.rows

        for i, child in enumerate(children):
            position = child.properties.position

            position.top = row2pos(child.properties.row)
            position.bottom = row2pos(child.properties.row + child.properties.rowspan)

            position.left = col2pos(child.properties.column)
            position.right = col2pos(child.properties.column + child.properties.colspan)

class Manipulator:
    """
    Manipulate the DOM. Operations need to be idempoetnt, i.e., f(f(x)) = f(x).

    """

    def __call__(self, node):
        """
        Manipulates the DOM.

        Returns:
            bool: if the DOM was changed
        """

        pass

class DynamicDOM:
    def __init__(self, manipulators):
        self.manipulators = manipulators

    def update(self, origin):
        self.tree = copy.deepcopy(origin)

        modified = True
        while modified:

            modified = False
            for manipulator in self.manipulators:
                modified |= manipulator(self.tree.getroot())

                if modified:
                    break

        return self.tree

class TextManipulator:
    def addText(self, element, text, position):
        if text:
            text = text.strip()
            # todo replace new line with space and condense space to single space

        if text:
            self.modified = True

            texts = text.split(" ")
            for i, text in enumerate(texts):
                txt = ET.Element('text')
                txt.text = text + " "

                element.insert(position + i, txt)

    def __call__(self, node):
        self.modified = False

        queue = list()
        queue.append(node)
        while queue:
            element = queue.pop()
            if element.tag != "text":
                for i, child in reversed(list(enumerate(element))):
                    queue.append(child)
                    self.addText(element, child.tail, i + 1)
                    child.tail = None

                self.addText(element, element.text, 0)
                element.text = None

        return self.modified


class LazyFileLoader:
    def __init__(self, filename):
        self.filename = filename
        self.read_time = None
        self.data = None

        self.reload()

    def reload(self):
        m_time = os.stat(self.filename).st_mtime
        if self.read_time != m_time:
            self.read_time = m_time
            self.load()
            return True

        return False

    def load(self):
        with open(self.filename, "r") as f:
            self.data = f.read()

        return self.data

class StyleLoader(LazyFileLoader):
    def load(self):
        with open(self.filename, "r") as f:
            self.data = yaml.load(f, Loader = yaml.BaseLoader)

class MarkupLoader(LazyFileLoader):
    def load(self):
        self.data = ET.parse(self.filename)

class ComponentManager:
    @property
    def tree(self):
        return self.markup_loader.data

    @property
    def style(self):
        return self.style_loader.data

    def __init__(self):
        self.style_loader = StyleLoader("styles.yml")
        self.markup_loader = MarkupLoader("gui.xml")
        self.dynamic_dom = DynamicDOM([
                TextManipulator(),
            ])

        self.do_update()

    def collect_properties(self, node):
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

        data["text"] = node.text

        return data

    def make_properties(self, component_cls, node, parents):
        data = self.collect_properties(node)

        property_classes = [component_cls.Properties]

        layout_cls = data.get("layout", None)
        if layout_cls:
            layout_cls = _layouts[layout_cls]
            property_classes.append(layout_cls.Properties)

        if parents:
            layout_parent_cls = getattr(parents[-1].properties, "layout", None)
            if layout_parent_cls:
                layout_parent_cls = _layouts[layout_parent_cls]
                property_classes.append(layout_parent_cls.ChildProperties)

        converter = make_converter()
        property_class = dataclass(type("Properties", tuple(property_classes), dict()))
        return converter.structure(data, property_class)

    def mk_component(self, node, parents):
        if node.tag not in _components:
            return

        component_cls = _components[node.tag]
        properties = self.make_properties(component_cls, node, parents)
        return component_cls(properties)

    def __iter__(self):
        return iter(self.components.values())

    def update(self):
        needUpdate = False
        needUpdate |= self.style_loader.reload()
        needUpdate |= self.markup_loader.reload()

        if needUpdate:
            self.do_update()

    def do_update(self):
        tree = self.dynamic_dom.update(self.tree)

        self.components = dict()

        self.make_components(tree.getroot(), [])
        self.layout(tree.getroot(), [])

    def make_components(self, node, parents):
        component = self.mk_component(node, parents)
        if component:
            self.components[node] = component

            parents.append(component)

        for child in node:
            self.make_components(child, parents)

        if component:
            parents.pop()

    def layout(self, node, parents):
        component = self.components.get(node)
        if component:
            layout_cls = getattr(component.properties, "layout", None)
            if layout_cls:
                layout_cls = _layouts[layout_cls]
                layouter = layout_cls(component.properties)

                childs = list()
                for child in node:
                    child_component = self.components.get(child)
                    if child_component:
                        childs.append(child_component)

                layouter.layout(childs)

            parents.append(component)

        for child in node:
            self.layout(child, parents)

        if component:
            parents.pop()


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

        for component in self.components:
            component.draw(self.ctx)

        # Update texture from sruface data
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture.id)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA,
            self.properties.width, self.properties.height, 0, gl.GL_BGRA,
            gl.GL_UNSIGNED_BYTE, self.surface_data)


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