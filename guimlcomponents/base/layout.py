import copy
from dataclasses import dataclass

from guiml.registry import layout

from guimlcomponents.base.container import Rectangle
from typing import Optional


def add_wrap_size(extend, wrap_size):
    extend.width = extend.width + wrap_size.left + wrap_size.right
    extend.height = extend.height + wrap_size.top + wrap_size.bottom


@layout("stack")
class Stack:
    """
    Stack intrinsically sized components.
    """
    @dataclass
    class Properties():
        """
        direction for stacking either vertical or horizontal
        """
        direction: str = 'vertical'

    @dataclass
    class ChildProperties():
        """
        gravity of stacked elements either left or right for vertical stacking
        and top or bottom for horizontal stacking or stretch for both
        """
        gravity: str = 'center'
        stretch: Optional[int] = None

    def __init__(self, component):
        self.component = component

        direction = self.component.properties.direction
        if direction not in ['vertical', 'horizontal']:
            raise ValueError(f'Invalid direction "{direction}".')

    def compute_recommended_size(self, children):
        result = Rectangle()
        direction = self.component.properties.direction

        width = 0
        height = 0
        for child in children:
            if direction == 'vertical':
                width = max(width, child.width)
                height += child.height
            elif direction == 'horizontal':
                width += child.width
                height = max(height, child.height)

        result.width = width
        result.height = height
        add_wrap_size(result, self.component.wrap_size)
        self.component.properties.position = result

    def layout(self, children):
        position = self.component.content_position
        center_y = position.top + position.height / 2
        center_x = position.left + position.width / 2

        direction = self.component.properties.direction

        if direction == 'vertical':
            next_pos = position.top
        elif direction == 'horizontal':
            next_pos = position.left

        total_stretch = 0

        if direction == 'horizontal':
            free_space = position.width
        elif direction == 'vertical':
            free_space = position.height

        for child in children:
            if child.properties.stretch is not None:
                total_stretch += child.properties.stretch

            if direction == 'horizontal':
                free_space -= child.width
            elif direction == 'vertical':
                free_space -= child.height

        for child in children:
            child_pos = copy.copy(child.properties.position)
            gravity = child.properties.gravity

            child_height = child.height
            child_width = child.width
            stretch = child.properties.stretch
            if stretch is not None:
                stretch = stretch // total_stretch * free_space
                if direction == 'vertical':
                    child_height += stretch
                elif direction == 'horizontal':
                    child_width += stretch

            if direction == 'vertical':
                child_pos.top = next_pos
                next_pos += child_height

                if gravity == 'left' or gravity == 'stretch':
                    child_pos.left = position.left
                elif gravity == 'right':
                    child_pos.left = position.right - child_width
                elif gravity == 'center':
                    child_pos.left = center_x - child_width / 2
                else:
                    raise ValueError(f'Invalid gravity "{gravity}".')

                if gravity == 'stretch':
                    child_pos.right = position.right
                else:
                    child_pos.width = child_width
                child_pos.height = child_height

            elif direction == 'horizontal':
                child_pos.left = next_pos
                next_pos += child_width
                if gravity == 'top' or gravity == 'stretch':
                    child_pos.top = position.top
                elif gravity == 'bottom':
                    child_pos.top = position.bottom - child_height
                elif gravity == 'center':
                    child_pos.top = center_y - child_height / 2
                else:
                    raise ValueError(f'Invalid gravity "{gravity}".')

                if gravity == 'stretch':
                    child_pos.bottom = position.bottom
                else:
                    child_pos.height = child_height

                child_pos.width = child_width

            child.properties.position = child_pos


@layout("align")
class Align:
    """
    Align an intrinsically sized component relative to the containing element.
    """

    ALIGNMENTS = set(['top left', 'top', 'top right', 'left', 'center',
                      'right', 'bottom left', 'bottom', 'bottom right'])

    @dataclass
    class Properties():
        pass

    @dataclass
    class ChildProperties():
        """
        alignment can be one of top left, top, top right, left, center, right,
        bottom left, bottom, bottom right
        """
        alignment: str = 'center'

        """
        Direction to stretch the contained element.
        Either 'horizontal', 'vertical', or '' (empty).
        """
        stretch: str = ''

    def __init__(self, component):
        self.component = component

    def compute_recommended_size(self, children):
        result = Rectangle()
        for child in children:
            result.width = max(result.width, child.width)
            result.height = max(result.height, child.height)

        add_wrap_size(result, self.component.wrap_size)
        self.component.properties.position = result

    def layout(self, children):
        position = self.component.content_position
        center_y = position.top + position.height / 2
        center_x = position.left + position.width / 2

        for child in children:
            alignment = child.properties.alignment

            if alignment not in self.ALIGNMENTS:
                raise RuntimeError(
                    f"Recieved unknown alignment '{alignment}'.")

            alignment = alignment.split(' ')

            child_pos = copy.copy(child.properties.position)

            child_pos.top = center_y - child.height / 2
            child_pos.left = center_x - child.width / 2

            if 'top' in alignment:
                child_pos.top = position.top
            if 'bottom' in alignment:
                child_pos.top = position.bottom - child.height
            if 'left' in alignment:
                child_pos.left = position.left
            if 'right' in alignment:
                child_pos.left = position.right - child.width

            child_pos.width = child.width
            child_pos.height = child.height

            if child.properties.stretch == 'horizontal':
                child_pos.left = position.left
                child_pos.right = position.right
            elif child.properties.stretch == 'vertical':
                child_pos.top = position.top
                child_pos.bottom = position.bottom

            child.properties.position = child_pos


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

    def compute_recommended_size(self, children):
        if (self.component.properties.position.width != 0
                and self.component.properties.position.height != 0):
            return
        else:
            width = 0
            height = 0
            for child in children:
                width = max(width, child.width / child.properties.colspan)
                height = max(height, child.height / child.properties.rowspan)

            result = Rectangle()
            result.width = self.component.properties.cols * width
            result.height = self.component.properties.rows * height

            add_wrap_size(result, self.component.wrap_size)
            self.component.properties.position = result

    def layout(self, children):
        position = self.component.content_position
        assert (position.is_valid())

        width = position.right - position.left
        height = position.bottom - position.top

        def col2pos(col):
            return ((col * width / self.component.properties.cols)
                    + position.left)

        def row2pos(row):
            return ((row * height / self.component.properties.rows)
                    + position.top)

        for i, child in enumerate(children):
            child_pos = copy.copy(child.properties.position)

            child_pos.top = row2pos(child.properties.row)
            child_pos.bottom = row2pos(child.properties.row +
                                       child.properties.rowspan)

            child_pos.left = col2pos(child.properties.col)
            child_pos.right = col2pos(child.properties.col +
                                      child.properties.colspan)

            child.properties.position = child_pos
