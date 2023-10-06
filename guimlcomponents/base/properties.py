from dataclasses import dataclass as _dataclass
from dataclasses import field as _field

@_dataclass
class Color:
    red: float = 0.
    green: float = 0.
    blue: float = 0.
    alpha: float = 0.

@_dataclass
class Border:
    width: int = 0.
    color: Color = _field(default_factory = Color)

@_dataclass
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

    @property
    def height(self):
        return self.bottom - self.top