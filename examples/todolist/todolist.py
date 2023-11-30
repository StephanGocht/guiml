from guiml.components import component, Container
from dataclasses import dataclass, field

from resources import resources as res
from todo import TodoItem, TodoService


@component(name="todolist", template=res.template_file("templates.xml"))
class TodoList(Container):

    @dataclass
    class Properties(Container.Properties):
        todos: list = field(default_factory=list)

    @property
    def todos(self):
        return self.properties.todos


@component(
    name="todo_item",
    template=res.template_file("templates.xml"))
class TodoItemComponent(Container):
    @dataclass
    class Dependencies(Container.Dependencies):
        todo_service: TodoService

    @dataclass
    class Properties(Container.Properties):
        item: TodoItem = None

    def on_init(self):
        self.destroyed = False
        super().on_init()

    def on_draw(self, canvas):
        super().on_draw(canvas)

    @property
    def item(self):
        return self.properties.item

    def checkbox_clicked(self):
        self.dependencies.todo_service.toggle_done(self.item)

    def get_checkbox_class(self):
        if self.item.done:
            return 'checkbox_ticked'
        else:
            return 'checkbox'

    def delete_clicked(self):
        self.dependencies.todo_service.remove(self.item)

    def on_destroy(self):
        self.destroyed = True
        super().on_destroy()