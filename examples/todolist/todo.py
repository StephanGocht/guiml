from guiml.components import component, Component, Container
from dataclasses import dataclass, field

from guiml.injectables import Injectable, injectable

@injectable("todo")
class TodoService(Injectable):
  def on_init(self):
    self.todos = ["todo %i"%(i) for i in range(4)]

@component(
  name = "todo",
  template_file = "todo.xml"
)
class Todo(Container):
  @dataclass
  class Dependencies:
    todo_service: TodoService

  @dataclass
  class Properties(Container.Properties):
    pass

  def on_init(self):
    self.text = 'Das ist ein Üäöööä text der sher komisch ist.'
    print("init todo")

  def on_destroy(self):
    print("destroy todo")

  @property
  def todos(self):
    return self.dependencies.todo_service.todos

  def add_clicked(self):
    print(self.text)

    todos = self.dependencies.todo_service.todos
    todos.append(self.text)
    self.text = ''
