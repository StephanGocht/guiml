import copy
import xml.etree.ElementTree as ET

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