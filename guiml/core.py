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
from typing import Optional

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

class PersistationStrategy:
    def store(self, children, payloads):
        pass

    def load(self, children):
        pass

    def __iter__(self):
        pass

class OrderPersistation:
    def __init__(self):
        self.storage = dict()

    def sibling_number(self, children):
        sibling_counter = defaultdict(int)
        for child in children:
            number = sibling_counter[child.tag]
            yield number
            sibling_counter[child.tag] = number + 1

    def save(self, children, payloads):
        self.storage = dict()
        for number, child, payload in zip(self.sibling_number(children), children, payloads):
            self.storage[(child.tag, number)] = payload

    def load(self, children):
        for number, child in zip(self.sibling_number(children), children):
            yield self.storage.get((child.tag, number))

    def __iter__(self):
        return iter(self.storage.values())

def new_strategy_from_name(name):
    if name != "order":
        raise NotImplementedError()
    return OrderPersistation()

class PersistationManager():
    STRATEGY_ATTRIBUTE = "persistation_strategy"

    @dataclass
    class Payload:
        children: dict[str, PersistationStrategy] = field(default_factory = dict)
        component: Optional["Component"] = None

    def __init__(self):
        self.root = None
        self.components = dict()

    def create_component(self, node, parent_nodes):
        pass

    def destroy_component(self, component):
        pass

    def on_component_restored(self, component, node, parent_nodes):
        pass

    def on_component_renewed(self, component, node, parent_nodes):
        pass

    def renew(self, root_node):
        self.components = dict()
        self.root = self.traverse(root_node, self.root, [])

    def traverse(self, node, restored_data, parent_nodes):
        if restored_data is None:
            restored_data = self.Payload()

        component = restored_data.component
        if component is None:
            component = self.create_component(node, parent_nodes)
        else:
            self.on_component_restored(component, node, parent_nodes)
        self.on_component_renewed(component, node, parent_nodes)
        self.components[node] = component

        childs_by_strategy = defaultdict(list)
        for child in node:
            childs_by_strategy[child.get(self.STRATEGY_ATTRIBUTE, "order")].append(child)

        restored_childs = dict()
        for key, children in childs_by_strategy.items():
            strategy = restored_data.children.get(key)
            if strategy:

                maintained = set()
                for child, data in zip(children, strategy.load(children)):
                    restored_childs[child] = data
                    if data is not None:
                        maintained.add(id(data.component))

                for data in strategy:
                    if data.component is not None and id(data.component) not in maintained:
                        self.destroy_component(data.component)

            else:
                for child in children:
                    restored_childs[child] = None

        parent_nodes.append(node)

        child_data = dict()
        for child in node:
            data = self.traverse(child, restored_childs[child], parent_nodes)
            child_data[child] = data

        parent_nodes.pop()

        saved_data = self.Payload()
        saved_data.component = component

        for key, children in childs_by_strategy.items():
            strategy = new_strategy_from_name(key)
            strategy.save(children, [child_data[child] for child in children])
            saved_data.children[key] = strategy

        return saved_data

    def __iter__(self):
        pass

class ComponentManager(PersistationManager):
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
        super().__init__()
        self.dependencies = None

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
                if self.components[parent]:
                    layout_parent_cls = getattr(self.components[parents[-1]].properties, "layout", None)
                    break

            if layout_parent_cls:
                layout_parent_cls = _layouts[layout_parent_cls]
                property_classes.append(layout_parent_cls.ChildProperties)

        converter = make_converter()
        converter.register_structure_hook(typing.Callable, lambda val, type: val)
        property_class = dataclass(type("Properties", tuple(property_classes), dict()))
        properties = converter.structure(data, property_class)
        return properties


    def create_component(self, node, parent_nodes):
        component = None

        self.injector.add_tag(node.tag)
        if node.tag == "application" and self.dependencies is None:
            print("create application")
            self.dependencies = self.injector.get_dependencies(self)
            self.on_init()

        if node.tag in _components:
            print("create", node.tag)
            component_cls = _components[node.tag].component_class
            properties = self.make_properties(component_cls, node, parent_nodes)
            dependencies = self.injector.get_dependencies(component_cls)
            component = component_cls(properties, dependencies)

        return component

    def destroy_component(self, component):
        component.on_destroy()

    def on_component_restored(self, component, node, parent_nodes):
        # todo: do we really want to overwrite the properties every time?
        # note: cattrs copies leaf attributes such as lists. This cause
        # not overwriting properties to not work as intended.
        component.properties = self.make_properties(type(component), node, parent_nodes)

    def on_component_renewed(self, component, node, parent_nodes):
        self.dynamic_dom.update(node, component)

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
        self.renew(tree.getroot())

        self.layout(tree.getroot(), [])

        # self.dump_tree(tree.getroot())

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
