from guiml.components import component, Component, Container
from dataclasses import dataclass, field

import dataclasses

from guiml.injectables import Injectable, injectable


import json


@dataclass
class TodoItem:
    text: str
    done: bool = False


@injectable("todo")
class TodoService(Injectable):
    SAVE_FILE = 'todos.json'

    def on_init(self):
        self.load()

    def load(self):
        try:
            with open(self.SAVE_FILE) as f:
                data = json.load(f)
        except OSError as e:
            print('Create empty todolist, due to error opening saved todos.'
                  'Error: %s' % (str(e)))

            data = []

        self.todos = [TodoItem(**item) for item in data]

    def save(self):
        data = [dataclasses.asdict(item) for item in (self.todos)]

        try:
            with open(self.SAVE_FILE, 'w') as f:
                json.dump(data, f)
        except OSError as e:
            print('Error saving file: ' % (str(e)))

    def add(self, text):
        self.todos.append(TodoItem(text))
        self.save()

    def remove(self, item):
        self.todos.remove(item)
        self.save()

    def toggle_done(self, item):
        item.done = not item.done
        self.save()


@component(name="todo", template_file="todo.xml")
class Todo(Container):

    @dataclass
    class Dependencies:
        todo_service: TodoService

    @dataclass
    class Properties(Container.Properties):
        pass

    def on_init(self):
        self.text = ''

    def on_destroy(self):
        pass

    @property
    def todos(self):
        return self.dependencies.todo_service.todos

    def add_clicked(self):
        todo_service = self.dependencies.todo_service
        todo_service.add(self.text)
        self.text = ''
