from dataclasses import dataclass, field


@dataclass
class Color:
    red: float = 0.
    green: float = 0.
    blue: float = 0.
    alpha: float = 0.


@dataclass
class Border:
    width: int = 0.
    color: Color = field(default_factory=Color)


@dataclass
class Rectangle:
    top: int = 0
    left: int = 0
    bottom: int = 0
    right: int = 0

    def is_valid(self):
        return self.left < self.right and self.top < self.bottom

    @property
    def width(self):
        return self.right - self.left

    @width.setter
    def width(self, value):
        self.right = self.left + value

    @property
    def height(self):
        return self.bottom - self.top

    @height.setter
    def height(self, value):
        self.bottom = self.top + value

    def is_inside(self, x, y):
        return (self.left <= x
                and x <= self.right
                and self.top <= y
                and y <= self.bottom)