import copy
import xml.etree.ElementTree as ET

from guiml.components import _components
from guiml.filecache import FileCache, MarkupLoader

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
            # todo replace new line with space and condense space to single space

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
    template_marker = "_template_expanded"

    def __init__(self):
        self.cache = FileCache()

    def __call__(self, node, component):
        meta_data = _components.get(node.tag)

        if meta_data and meta_data.template:
            loader = self.cache.get(meta_data.template, MarkupLoader)
            is_expanded = node.get(self.template_marker, False)
            changed = loader.reload()
            if not is_expanded or changed:
                attrib = node.attrib
                node.clear()
                node.attrib = attrib
                node.set(self.template_marker, "True")
                node.extend(copy.deepcopy(loader.data.getroot()))

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

    def eval_if(self, control, context):
        return eval("bool(%s)"%(control[2:]), None, context)

    def eval_for(self, control, context):
        local = {}
        exec(for_loop % {"for_loop": control}, None, local)
        return local["__result__"]

    def transform(self, node, context):
        modified = False

        offset = 0
        for i in range(len(node)):
            child = node[i + offset]

            control = child.get(self.CONTROL_ATTRIBUTE)
            if not control:
                modified |= self.transform(child, context)
            else:
                control = control.strip()

                del child.attrib[self.CONTROL_ATTRIBUTE]
                assert(child.get(self.CONTROL_ATTRIBUTE) is None)
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

                    for j, item in enumerate(items):
                        sibling = copy.deepcopy(child)
                        node.insert(i + j, sibling)

                        context = {**context, **item}
                        self.transform(sibling, context)

        return modified



    def __call__(self, node, component):
        return self.transform(node, {"self": component})