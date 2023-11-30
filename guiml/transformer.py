import copy
import xml.etree.ElementTree as ET

from guiml.registry import _components


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
        modified = True
        while modified:

            modified = False
            for manipulator in self.manipulators:
                modified |= manipulator(node, component)

                if modified:
                    break


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

                # todo: why do we check changed here? If this actually does
                # something then the update isn't correct, because changed
                # will only be true for the first time we request the template.
                if not self.is_expanded(node) or changed:
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
        self.getter = lambda value, context: lambda self: eval(
            value, None, context)

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

        return modified

    def transform(self, node, context):
        modified = False

        modified |= self.transform_attributes(node, context)

        offset = 0
        for i in range(len(node)):
            child = node[i + offset]

            control = child.get(self.CONTROL_ATTRIBUTE)
            if not control:
                modified |= self.transform(child, context)
            else:
                control = control.strip()
                del_atribute(child, self.CONTROL_ATTRIBUTE)
                modified = True

                if control[:2] == "if":
                    display = self.eval_if(control, context)
                    if display:
                        self.transform(child, context)
                    else:
                        node.remove(child)
                        offset += -1

                elif control[:3] == "for":
                    items = self.eval_for(control, context)
                    offset += -1 + len(items)

                    node.remove(child)

                    for j, sibling_context in enumerate(items):
                        sibling = copy.deepcopy(child)
                        node.insert(i + j, sibling)
                        # sibling_context = {**context, **item}

                        # sibling.set(CONTEXT_ATTRIBUTE, sibling_context)
                        self.transform(sibling, sibling_context)

        return modified

    def __call__(self, node, component):
        # context = {"self": component}
        # node.set(CONTEXT_ATTRIBUTE, context)
        # node.set(CLEAR_CONTEXT_ATTRIBUTE, True)

        return self.transform(node, {"self": component})

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
