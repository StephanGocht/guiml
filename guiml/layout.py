from dataclasses import dataclass, field

_layouts = {}

def layout(name):
    def register(cls):
        _layouts[name] = cls
        return cls

    return register

@layout("hflow")
class HorizontalFlow:
    @dataclass
    class Properties():
        pass

    @dataclass
    class ChildProperties():
        pass

    def __init__(self, component):
        self.component = component

    def layout(self, children):
        position = self.component.content_position

        width = position.width
        height = position.height

        posx = position.left
        posy = position.top
        max_height = 0

        for child in children:
            if posx + child.width > position.right:
                posx = position.left
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
    class Properties():
        rows: int = 1
        cols: int = 1

    @dataclass
    class ChildProperties():
        row: int = 0
        rowspan: int = 1
        col: int = 0
        colspan: int = 1

    def __init__(self, component):
        self.component = component

    def layout(self, children):
        position = self.component.content_position

        assert(position.is_valid())

        width = position.right - position.left
        height = position.bottom - position.top

        col2pos = lambda col: (col * width / self.component.properties.cols) + position.left
        row2pos = lambda row: (row * height / self.component.properties.rows) + position.top

        for i, child in enumerate(children):
            child_pos = child.properties.position

            child_pos.top = row2pos(child.properties.row)
            child_pos.bottom = row2pos(child.properties.row + child.properties.rowspan)

            child_pos.left = col2pos(child.properties.col)
            child_pos.right = col2pos(child.properties.col + child.properties.colspan)