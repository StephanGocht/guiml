from guiml.components import component, Component, WidgetProperty
from dataclasses import dataclass, field

@component(
  name = "todolist",
  template = "todolist.xml"
)
class TodoList(Component):
  @dataclass
  class Properties(WidgetProperty):
    todos: list = field(default_factory = list)

  @property
  def todos(self):
    return self.properties.todos