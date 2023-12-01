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


@component(
    # the root component is always named application
    name="application",
    # We will provide the markup for the application in templates.xml
    template=resources.template_file('templates.xml')
)
class Application(Component):
    pass


# Let us define a shorthand, as we will always use the same template file.
# in this tutorial.
def app_component(name):
    return component(name, template=resources.template_file('templates.xml'))


@app_component("hello_world")
class HelloWorld(Div):
    pass


def main():
    # Start the guiml main loop
    run()


if __name__ == '__main__':
    main()
