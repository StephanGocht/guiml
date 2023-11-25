from dataclasses import dataclass

import gi
gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg


from guiml.registry import component
from guimlcomponents.base.container import UIComponent
from guimlcomponents.base.cairocffi_to_pycairo import _UNSAFE_cairocffi_context_to_pycairo as convert


@component("svg")
class Svg(UIComponent):
    @dataclass
    class Properties(UIComponent.Properties):
        src: str = ""
        width: int = 0
        height: int = 0

    @dataclass
    class Dependencies(UIComponent.Dependencies):
        pass

    @property
    def width(self):
        return self.properties.width

    @property
    def height(self):
        return self.properties.height

    def on_draw(self, context):
        pos = Rsvg.Rectangle()
        pos.x = self.properties.position.left
        pos.y = self.properties.position.top
        pos.width = self.properties.position.width
        pos.height = self.properties.position.height

        svg = Rsvg.Handle().new_from_file(self.properties.src)
        svg.render_document(convert(context), pos)

        super().on_draw(context)
