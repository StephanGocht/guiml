from guiml.components import component, Component, WidgetProperty
from dataclasses import dataclass, field

@component(
  name = "todo",
  template = "todo.xml"
)
class Todo(Component):
  @dataclass
  class Properties(WidgetProperty):
    item: str = ""

  @property
  def text(self):
    return self.properties.item.text