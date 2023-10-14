from guiml.components import component, Component, Container
from dataclasses import dataclass, field


@component(name="todolist", template_file="todolist.xml")
class TodoList(Container):

    @dataclass
    class Properties(Container.Properties):
        todos: list = field(default_factory=list)

    @property
    def todos(self):
        return self.properties.todos
