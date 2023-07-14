import ctypes
import cairo
import xml.etree.ElementTree as ET
import yaml
from cattrs.preconf.pyyaml import make_converter
from dataclasses import dataclass, field
import dataclasses
from pyglet import app, clock, gl, image, window
import os

import typing

from collections import defaultdict, namedtuple

from guiml.filecache import StyleLoader, MarkupLoader


from guiml.transformer import *

from guiml.components import _components
from guiml.layout import _layouts
from guiml.injectables import Injector, UILoop

def tree_dfs(node):
    """
    Yield nodes in DFS search. On every backtrack None is returned.
    """

    queue = list()
    queue.append(node)

    while queue:
        node = queue.pop()
        yield node

        if node is not None:
            queue.append(None)

            for child in reversed(node):
                queue.append(child)

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

NodeComponentPair = namedtuple("NodeComponentPair", "node component")

class ComponentManager:
    @dataclass
    class Dependencies:
        ui_loop: UILoop

    @property
    def tree(self):
        return self.markup_loader.data

    @property
    def style(self):
        return self.style_loader.data

    PERSISTANCE_KEY_ATTRIBUTE = "persistance_key"

    def __init__(self, root_markup):
        self.window = None
        self.components = {}
        self.dependencies = None

        self.component_store = dict()

        self.style_loader = StyleLoader("styles.yml")
        self.markup_loader = MarkupLoader(root_markup)
        self.injector = Injector()
        self.dynamic_dom = DynamicDOM([
                TemplatesTransformer(),
                ControlTransformer(),
                TextTransformer(),
            ])

        self.do_update()


    def on_init(self):
        # on_init is called when application tag is encountered

        self._update_subscription = self.dependencies.ui_loop.on_update.subscribe(self.on_update)

    def on_destroy(self):
        self._update_subscription.cancel()


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

        data = merge_data(data, node.attrib)

        return data

    def make_properties(self, component_cls, node, parents):
        data = self.collect_properties(node)

        property_classes = [component_cls.Properties]

        layout_cls = data.get("layout", None)
        if layout_cls:
            layout_cls = _layouts[layout_cls]
            property_classes.append(layout_cls.Properties)

        if parents:
            layout_parent_cls = None
            for parent in reversed(parents):
                if parent.component:
                    layout_parent_cls = getattr(parents[-1].component.properties, "layout", None)
                    break

            if layout_parent_cls:
                layout_parent_cls = _layouts[layout_parent_cls]
                property_classes.append(layout_parent_cls.ChildProperties)

        converter = make_converter()
        converter.register_structure_hook(typing.Callable, lambda val, type: val)
        property_class = dataclass(type("Properties", tuple(property_classes), dict()))
        properties = converter.structure(data, property_class)
        return properties


    def mk_component(self, node, parents):
        component = None

        persistance_key = node.get(self.PERSISTANCE_KEY_ATTRIBUTE)
        stored_component = self.component_store.get(persistance_key)

        if stored_component:
            component = stored_component

            # todo: do we really want to overwrite the properties every time?
            # note: cattrs copies leaf attributes such as lists. This cause
            # not overwriting properties to not work as intended.
            component.properties = self.make_properties(type(component), node, parents)
        else:
            self.injector.add_tag(node.tag)
            if node.tag == "application" and self.dependencies is None:
                self.dependencies = self.injector.get_dependencies(self)
                self.on_init()

            if node.tag in _components:
                component_cls = _components[node.tag].component_class
                properties = self.make_properties(component_cls, node, parents)
                dependencies = self.injector.get_dependencies(component_cls)
                component = component_cls(properties, dependencies)

        self.dynamic_dom.update(node, component)
        return component

    def __iter__(self):
        return iter(self.components.values())

    def on_update(self, dt):
        needUpdate = False
        needUpdate |= self.style_loader.reload()
        needUpdate |= self.markup_loader.reload()

        # if needUpdate:
        self.do_update()

    def do_update(self):
        tree = copy.deepcopy(self.tree)

        self.components = dict()
        self.make_components(tree.getroot(), [])
        self.update_component_store()

        self.layout(tree.getroot(), [])

        # self.dump_tree(tree.getroot())

    def update_component_store(self):
        old_store = self.component_store
        self.component_store = dict()

        for node, component in self.components.items():
            self.component_store[node.get(self.PERSISTANCE_KEY_ATTRIBUTE)] = component

        for key, component in old_store.items():
            if key not in self.component_store:
                component.on_destroy()


    def dump_tree(self, node):
        stack = list()
        indent = 0
        for node in tree_dfs(node):
            if node is not None:
                component = self.components.get(node)
                print("  " * indent, "<%s>"%(node.tag))
                if component:
                    for field in dataclasses.fields(component.properties):
                        print("  " * (indent + 2), "%s: %s"%(field.name, getattr(component.properties, field.name)))

                stack.append(node.tag)
                indent += 1
            else:
                indent -= 1
                print("  " * indent, "</%s>"%(stack.pop()))

    def add_persistance_key(self, node, parents, sibling_count = 0):
        if not parents:
            key = "/"
        else:
            key = parents[-1].node.get(self.PERSISTANCE_KEY_ATTRIBUTE) + "/"

        key += "%s[%i]"%(node.tag, sibling_count)

        node.set(self.PERSISTANCE_KEY_ATTRIBUTE, key)


    def make_components(self, node, parents, sibling_count = 0):
        self.add_persistance_key(node, parents, sibling_count)
        component = self.mk_component(node, parents)
        if component:
            self.components[node] = component

        parents.append(NodeComponentPair(node, component))

        sibling_counter = defaultdict(int)
        for child in node:
            sibling_count = sibling_counter[child.tag]
            self.make_components(child, parents, sibling_count)
            sibling_counter[child.tag] = sibling_count + 1

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
