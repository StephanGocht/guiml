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

    def update_node(self, node):
        modified = True
        while modified:

            modified = False
            for manipulator in self.manipulators:
                modified |= manipulator(node)

                if modified:
                    break

    def update(self, origin):
        self.tree = copy.deepcopy(origin)

        queue = list()
        queue.append(self.tree.getroot())
        while queue:
            node = queue.pop()
            self.update_node(node)
            for child in node:
                queue.append(child)

        return self.tree

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

    def __call__(self, node):
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

    def __call__(self, node):
        meta_data = _components.get(node.tag)

        if meta_data and meta_data.template:
            loader = self.cache.get(meta_data.template, MarkupLoader)
            is_expanded = node.get(self.template_marker, False)
            changed = loader.reload()
            if not is_expanded or changed:
                attrib = node.attrib
                node.clear()
                node.attrib = attrib
                node.set(self.template_marker, True)
                node.extend(copy.deepcopy(loader.data.getroot()))

                return True

        return False
