import copy
import xml.etree.ElementTree as ET

from guiml.registry import _components
from guiml.injectables import timeit


def del_atribute(node, attribute):
    # the doc states that for the attrib dictionary: 'an ElementTree
    # implementation may choose to use another internal representation, and
    # create the dictionary only if someone asks for it', hence it might be
    # that deletion on it doesn't work in case we switch to a different
    # implementation
    del node.attrib[attribute]
    assert (node.get(attribute) is None)


class Transformer:
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

    def update(self, node, component):
        for manipulator in self.manipulators:
            # with timeit.record(manipulator.__class__.__name__):
            manipulator(node, component)


class TextTransformer:

    def addText(self, element, text, position):
        if text:
            text = text.strip()

        if text:
            self.modified = True

            texts = text.split(" ")
            for i, text in enumerate(texts):
                txt = ET.Element('text')
                txt.text = text + " "

                element.insert(position + i, txt)

    def __call__(self, node, component):
        self.modified = False

        if node.tag != "text":
            for i, child in reversed(list(enumerate(node))):
                self.addText(node, child.tail, i + 1)
                child.tail = None

            self.addText(node, node.text, 0)
            node.text = None

        return self.modified


class TemplatesTransformer:
    ATTR_TEMPLATE_MARKER = "_template_expanded"
    ATTR_CREATOR_STYLE = "_creator_style"

    @classmethod
    def get_creator_style(cls, node):
        return node.get(cls.ATTR_CREATOR_STYLE, None)

    def insert_template(self, node, template, style):
        # todo add proper error message
        assert (template.tag == node.tag)

        attrib = node.attrib
        node.clear()
        node.attrib = attrib
        node.set(self.ATTR_TEMPLATE_MARKER, True)
        node.extend(copy.deepcopy(template))

        if style is not None:
            for decendent in node.iter():
                decendent.set(self.ATTR_CREATOR_STYLE, style)

    def is_expanded(self, node):
        return node.get(self.ATTR_TEMPLATE_MARKER, False)

    def __call__(self, node, component):
        meta_data = _components.get(node.tag)

        if meta_data:
            if meta_data.template is not None:
                data, changed = meta_data.template.get()

                if data is not None:
                    self.insert_template(node, data, meta_data.style)
                    return True

        return False


for_loop = """
__result__ = list()
%(for_loop)s:
    __locals__ = dict(locals())
    del __locals__["__result__"]
    __locals__.pop("__locals__", None)
    __result__.append(__locals__)
"""


class ControlTransformer:
    CONTROL_ATTRIBUTE = "control"

    CONTEXT_ATTRIBUTE = "_context"
    CLEAR_CONTEXT_ATTRIBUTE = "_clear_context"

    def __init__(self):
        def getter(value, context):
            def _getter(self):
                return eval(value, None, context)

            return _getter

        self.getter = getter

        def setter(value, context):

            def _setter(self, x):
                context["_guiml_bind_value"] = x
                exec(f"{value} = _guiml_bind_value", None, context)

            return _setter

        self.setter = setter

    def eval_if(self, control, context):
        return eval("bool(%s)" % (control[2:]), None, context)

    def eval_for(self, control, context):
        local = {**context}
        exec(for_loop % {"for_loop": control}, None, local)
        return local["__result__"]

    # @timeit('renew > on_data_renewed > ')
    def transform_attributes(self, node, context):
        modified = False

        for key in node.keys():
            if key.startswith("py_") or key.startswith("on_"):
                value = node.get(key)
                if isinstance(value, str):
                    modified = True
                    del_atribute(node, key)
                    new_value = eval(value, None, context)

                    if key.startswith("py_"):
                        key = key[3:]
                    node.set(key, new_value)
            elif key.startswith("bind_"):
                value = node.get(key)

                if isinstance(value, str):
                    modified = True
                    del_atribute(node, key)
                    key = key[5:]

                    new_value = property(self.getter(value, context),
                                         self.setter(value, context))

                    node.set(key, new_value)
            elif key.startswith("class_"):
                value = f"bool({node.get(key)})"
                del_atribute(node, key)

                def condition(value=value, context=context):
                    result = eval(value, None, context)
                    return result

                # todo: the transformation should only be called once on the
                # template but is called multiple times, thus we need to
                # rename the tag to avoid double expansion
                node.set(f'_expanded_{key}', condition)

        return modified

    def transform(self, node, context, component_root=False):
        new_node = ET.Element(node.tag, attrib=copy.copy(node.attrib))
        new_node.text = node.text
        new_node.tail = node.tail

        if not component_root:
            self.transform_attributes(new_node, context)

        for child in node:
            control = child.get(self.CONTROL_ATTRIBUTE)
            if not control:
                new_node.append(self.transform(child, context))
            else:
                control = control.strip()
                del_atribute(child, self.CONTROL_ATTRIBUTE)

                if control[:2] == "if":
                    display = self.eval_if(control, context)
                    if display:
                        new_node.append(self.transform(child, context))

                elif control[:3] == "for":
                    items = self.eval_for(control, context)

                    for j, sibling_context in enumerate(items):
                        new_node.append(self.transform(child, sibling_context))

        return new_node

    def __call__(self, node, component):
        meta_data = _components.get(node.tag)

        if not meta_data or meta_data.template is None:
            return

        new_node = self.transform(node, {"self": component}, component_root=True)

        # copy childs from new node, but otherwise keep original node
        for i in reversed(range(len(node))):
            del node[i]
        node.extend(new_node)

    # @classmethod
    # def iter_context(cls, node):
    #     contexts = list()

    #     for node in tree_dfs(node):
    #         if node is None:
    #             contexts.pop()
    #         else:
    #             new_context = node.get(cls.CONTEXT_ATTRIBUTE, None)
    #             clear_context = node.get(cls.CLEAR_CONTEXT_ATTRIBUTE, False)

    #             if new_context:
    #                 if clear_context:
    #                     contexts.push(new_context)
    #                 else:
    #                     contexts.push({**contexts[-1], **new_context})
    #             else:
    #                 if clear_context:
    #                     contexts.push({})

    #         yield node, contexts[-1]
