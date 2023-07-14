from guiml.components import component, Component, WidgetProperty
from dataclasses import dataclass, field

from guiml.injectables import Injectable, injectable

@injectable("todo")
class TodoService(Injectable):
  def on_init(self):
    self.todos = ["todo %i"%(i) for i in range(4)]

@component(
  name = "todo",
  template = "todo.xml"
)
class Todo(Component):
  @dataclass
  class Dependencies:
    todo_service: TodoService

  @dataclass
  class Properties(WidgetProperty):
    pass

  def on_init(self):
    print("init todo")

  def on_destroy(self):
    print("destroy todo")

  @property
  def todos(self):
    return self.dependencies.todo_service.todos


  def add_clicked(self):
    todos = self.dependencies.todo_service.todos
    todos.append("todo %i"%(len(todos)))
