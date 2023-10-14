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
from typing import Optional, Any

from collections import defaultdict, namedtuple

from guiml.filecache import StyleLoader, MarkupLoader

from guiml.transformer import *

from guiml.registry import _components, _layouts
from guiml.injectables import Injector, UILoop

import logging

# by importing guiml plugins we trigger plugin detection and will load all
# components
import guiml.plugins
import guiml.layout


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
        for number, child, payload in zip(self.sibling_number(children),
                                          children, payloads):
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
    class DataNode:
        children: dict[str, PersistationStrategy] = field(default_factory=dict)
        data: Any = None

    def __init__(self):
        self.root = None

    def create_data(self, node, parent_nodes):
        pass

    def destroy_data(self, data):
        pass

    def on_data_restored(self, data, node, parent_nodes):
        pass

    def on_data_renewed(self, data, node, parent_nodes):
        pass

    def renew(self, root_node):
        self.root = self.traverse(root_node, self.root, [])

    def traverse(self, node, restored_data, parent_nodes):
        if restored_data is None:
            restored_data = self.DataNode()

        data = restored_data.data
        if data is None:
            data = self.create_data(node, parent_nodes)
        else:
            self.on_data_restored(data, node, parent_nodes)
        self.on_data_renewed(data, node, parent_nodes)

        childs_by_strategy = defaultdict(list)
        for child in node:
            childs_by_strategy[child.get(self.STRATEGY_ATTRIBUTE,
                                         "order")].append(child)

        restored_childs = dict()
        for key, children in childs_by_strategy.items():
            strategy = restored_data.children.get(key)
            if strategy:

                maintained = set()
                for child, data_node in zip(children, strategy.load(children)):
                    restored_childs[child] = data_node
                    if data_node is not None:
                        maintained.add(id(data_node.data))

                for data_node in strategy:
                    if data_node.data is not None and id(
                            data_node.data) not in maintained:
                        self.destroy_data(data_node.data)

            else:
                for child in children:
                    restored_childs[child] = None

        parent_nodes.append(node)

        child_data = dict()
        for child in node:
            data_node = self.traverse(child, restored_childs[child],
                                      parent_nodes)
            child_data[child] = data_node

        parent_nodes.pop()

        saved_data = self.DataNode()
        saved_data.data = data

        for key, children in childs_by_strategy.items():
            strategy = new_strategy_from_name(key)
            strategy.save(children, [child_data[child] for child in children])
            saved_data.children[key] = strategy

        return saved_data

    def __iter__(self):
        pass


@dataclass
class NodeObjects:
    component: "Optional[Component]" = None
    injectables: Optional[dict] = None

    def on_destroy(self):
        component.on_destroy()
        for injectable in injectables.items():
            injectable.on_destroy()


def make_intermediate_dataclass(base, properties):
    # Create an intermediate dataclass that disables initialization of the
    # property so that a bound value does not get overwritten

    definitions = dict()
    annotations = dict()

    for name, data in properties.items():
        value, field_type = data
        annotations[name] = field_type
        definitions[name] = dataclasses.field(init=False)

    definitions['__annotations__'] = annotations
    return dataclass(type("guiml_intermediate_class", (base, ), definitions))


def add_properties(base, properties):
    intermediate = make_intermediate_dataclass(base, properties)

    definitions = dict()

    for name, data in properties.items():
        value, field_type = data
        definitions[name] = value

    return dataclass(
        type('guiml_added_properties', (intermediate, ), definitions))


def structure(data, data_type):
    if data is None:
        return None
    elif isinstance(data, data_type):
        return data
    elif dataclasses.is_dataclass(data_type):
        args = dict()
        properties = dict()
        for field in dataclasses.fields(data_type):
            try:
                value = data[field.name]
            except KeyError:
                pass
            else:
                if isinstance(value, property):
                    properties[field.name] = (value, field.type)
                else:
                    origin = typing.get_origin(field.type)
                    if origin is not None:
                        type_args = typing.get_args(field.type)
                        if origin is typing.Union:
                            if len(type_args) == 2 and type(None) in type_args:
                                if value is None:
                                    args[field.name] = value
                                else:
                                    field_type = next(
                                        iter((t for t in type_args
                                              if t is not type(None))))
                                    args[field.name] = structure(
                                        value, field_type)
                            else:
                                args[field.name] = value
                    else:
                        args[field.name] = structure(value, field.type)

        if properties:
            data_type = add_properties(data_type, properties)

        return data_type(**args)
    else:
        try:
            return data_type(data)
        except TypeError:
            return data


_logged_unknown_components = set()


def log_unknown_component(tag):
    if tag not in _logged_unknown_components:
        logging.warning(f'Encountered unknown tag {tag}')
        _logged_unknown_components.add(tag)


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
        self.node_data = dict()

        self.style_loader = StyleLoader("styles.yml")
        self.markup_loader = MarkupLoader(root_markup)
        self.dynamic_dom = DynamicDOM([
            TemplatesTransformer(),
            ControlTransformer(),
            TextTransformer(),
        ])

        self.do_update()

    def on_init(self):
        # on_init is called when application tag is encountered

        self._update_subscription = self.dependencies.ui_loop.on_update.subscribe(
            self.on_update)

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
                data = merge_data(data,
                                  self.style.get(".%s" % (style_class), {}))

        tag_id = node.get("id")
        if tag_id:
            data = merge_data(data, self.style.get("$%s" % (tag_id), {}))

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
                parent_component = self.node_data[parent].component
                if parent_component:
                    layout_parent_cls = getattr(parent_component.properties,
                                                "layout", None)
                    break

            if layout_parent_cls:
                layout_parent_cls = _layouts[layout_parent_cls]
                property_classes.append(layout_parent_cls.ChildProperties)

        property_class = dataclass(
            type("Properties", tuple(property_classes), dict()))
        properties = structure(data, property_class)
        return properties

    def create_data(self, node, parent_nodes):
        result = NodeObjects()

        component = None

        injector = Injector(
            [self.node_data[parent].injectables for parent in parent_nodes])
        result.injectables = injector.add_tag(node.tag)
        if node.tag == "application" and self.dependencies is None:
            self.dependencies = injector.get_dependencies(self)
            self.on_init()
        elif node.tag in _components:
            component_cls = _components[node.tag].component_class
            properties = self.make_properties(component_cls, node,
                                              parent_nodes)
            dependencies = injector.get_dependencies(component_cls)
            component = component_cls(properties, dependencies)
        else:
            log_unknown_component(node.tag)

        result.component = component
        return result

    def destroy_data(self, data):
        data.on_destroy()

    def on_data_restored(self, data, node, parent_nodes):
        if data.component:
            # todo: do we really want to overwrite the properties every time?
            # note: cattrs copies leaf attributes such as lists. This cause
            # not overwriting properties to not work as intended.
            data.component.properties = self.make_properties(
                type(data.component), node, parent_nodes)
            #pass

    def on_data_renewed(self, data, node, parent_nodes):
        self.node_data[node] = data
        self.dynamic_dom.update(node, data.component)

    def on_update(self, dt):
        needUpdate = False
        needUpdate |= self.style_loader.reload()
        needUpdate |= self.markup_loader.reload()

        # if needUpdate:
        self.do_update()

    def do_update(self):
        tree = copy.deepcopy(self.tree)

        self.node_data = dict()
        self.renew(tree.getroot())

        self.layout(tree.getroot(), [])

        # self.dump_tree(tree.getroot())

    def dump_tree(self, node):
        stack = list()
        indent = 0
        for node in tree_dfs(node):
            if node is not None:
                data = self.node_data.get(node)
                print("  " * indent, "<%s>" % (node.tag))
                if data and data.component:
                    component = data.component
                    for field in dataclasses.fields(component.properties):
                        print(
                            "  " * (indent + 2), "%s: %s" %
                            (field.name,
                             getattr(component.properties, field.name)))

                stack.append(node.tag)
                indent += 1
            else:
                indent -= 1
                print("  " * indent, "</%s>" % (stack.pop()))

    def layout(self, node, parents):
        data = self.node_data.get(node)
        component = data.component if data else None
        if component:
            component = data.component
            layout_cls = getattr(component.properties, "layout", None)
            if layout_cls:
                layout_cls = _layouts[layout_cls]
                layouter = layout_cls(component)

                childs = list()
                for child in node:
                    child_data = self.node_data.get(child)
                    if child_data and child_data.component:
                        childs.append(child_data.component)

                layouter.layout(childs)

            parents.append(component)

        for child in node:
            self.layout(child, parents)

        if component:
            parents.pop()
