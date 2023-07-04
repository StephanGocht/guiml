import ctypes
import cairo
import xml.etree.ElementTree as ET
import yaml
from cattrs.preconf.pyyaml import make_converter
from dataclasses import dataclass, field
from pyglet import app, clock, gl, image, window
import os


from guiml.filecache import StyleLoader, MarkupLoader


from guiml.transformer import *

from guiml.components import _components
from guiml.layout import _layouts


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



class ComponentManager:
    @property
    def tree(self):
        return self.markup_loader.data

    @property
    def style(self):
        return self.style_loader.data

    def __init__(self, root_markup):
        self.style_loader = StyleLoader("styles.yml")
        self.markup_loader = MarkupLoader(root_markup)
        self.dynamic_dom = DynamicDOM([
                TemplatesTransformer(),
                ControlTransformer(),
                TextTransformer(),
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
        component = None

        if node.tag in _components:
            component_cls = _components[node.tag].component_class
            properties = self.make_properties(component_cls, node, parents)
            component = component_cls(properties)

        self.dynamic_dom.update(node, component)
        return component

    def __iter__(self):
        return iter(self.components.values())

    def update(self):
        needUpdate = False
        needUpdate |= self.style_loader.reload()
        needUpdate |= self.markup_loader.reload()

        if needUpdate:
            self.do_update()

    def do_update(self):
        tree = copy.deepcopy(self.tree)

        self.components = dict()

        self.make_components(tree.getroot(), [])
        ET.dump(tree)
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
            print(component.__class__, component.properties)

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


class Window:
    def __init__(self, root_markup):
        # todo: window settings should be read from the xml!
        self.window = window.Window(width = 400, height = 400, resizable = True)
        self.window.set_location(2000, 500)
        self.root_markup = root_markup

    def on_draw(self):
        self.window.clear()

    def add(self, tag):
        pass

    def run(self):
        manager = ComponentManager(self.root_markup)

        gui = GUI(self.window, GUI.Properties(), manager)

        # run on draw first, i.e., push it as last handler
        self.window.push_handlers("on_draw", self.on_draw)
        app.run()