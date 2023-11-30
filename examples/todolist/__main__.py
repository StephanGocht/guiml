import sys
import os
from pathlib import Path

APP_PATH = Path(__file__).parent
ROOT_PATH = APP_PATH.parent.parent
sys.path.extend([str(APP_PATH), str(ROOT_PATH)])

os.chdir(APP_PATH)

from guiml.components import component, Component
from guiml.core import run

from guiml.components import component, Component, Container
from dataclasses import dataclass, field

import dataclasses

from guiml.injectables import Injectable, injectable

from guiml.components import component, Container
from dataclasses import dataclass, field

from guiml.filecache import ResourceManager
from pathlib import Path
import json

BASE_DIR = Path(__file__).parent.resolve()

res = ResourceManager(
    basedir=BASE_DIR,
    paths={
        'checkbox_blank': 'resources/material-design-icons/check_box_outline_blank_FILL0_wght400_GRAD0_opsz24.svg',  # noqa: E501
        'checkbox_ticked': 'resources/material-design-icons/check_box_FILL0_wght400_GRAD0_opsz24.svg',  # noqa: E501
        'delete': 'resources/material-design-icons/delete_FILL0_wght400_GRAD0_opsz24.svg',  # noqa: E501
    })


@component("application", res.template_file("templates.xml"))
class Application(Component):
    pass


def main():
    run(interval=1 / 32)


@dataclass
class TodoItem:
    text: str
    done: bool = False


@injectable("todo")
class TodoService(Injectable):
    SAVE_FILE = BASE_DIR / 'todos.json'

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


@component("todo", res.template_file("templates.xml"))
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

    @property
    def num_open_todos(self):
        return sum((1 for todo in self.todos if not todo.done))

    def add_clicked(self):
        todo_service = self.dependencies.todo_service
        todo_service.add(self.text)
        self.text = ''

    def input_submit(self, text):
        self.add_clicked()


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

    def checkbox_svg(self):
        if self.item.done:
            return res.paths['checkbox_ticked']
        else:
            return res.paths['checkbox_blank']

    def delete_svg(self):
        return res.paths['delete']

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


if __name__ == '__main__':
    main()
