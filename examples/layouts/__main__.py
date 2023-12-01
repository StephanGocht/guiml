from pathlib import Path

from guiml.components import component, Component, Div
from guiml.resources import ResourceManager
from guiml.core import run

# Get the directory containing this file.
DIR = Path(__file__).parent.resolve()

# Create a resource manager to access resources, such as xml files, from DIR.
# This makes sure that the program still works if we call it from a different
# directory.
resources = ResourceManager(DIR)


def app_component(name):
    return component(
        name=name,
        template=resources.template_file('templates.xml'),
        style=resources.style_file('styles.yml'),)


@app_component("application")
class Application(Component):
    pass


def main():
    # Start the guiml main loop
    run()


if __name__ == '__main__':
    main()
