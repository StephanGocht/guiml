Tutorial
========

This tutorial should give you a brief overview over the fundamental concepts
driving guiml. To follow this tutorial, you should already be familiar with
programming in python and understand the file formats XML and YAML.

Introduction
------------

We can build an application with guiml by composing different components. The
root component is the application itself. Every other component has a single
parent component. This structure can easily be expressed via xml. So let us
first create a file :code:`templates.xml` with the following content.

.. code-block:: xml
    :caption: Content of :code:`templates.xml`

    <templates>
        <application>
            <window>
                <text text="Hello World!"></text>
            </window>
        </application>
    </templates>

This file now contains a template for the application component, which has a
window with a text component.  To specify the displayed text, the component
has a property text.

To run this application we need a bit of boiler plate, which we put in a
new file :code:`app.py` right beside the :code:`templates.xml`.

.. code-block:: py
    :caption: Content of :code:`app.py`


    from pathlib import Path

    from guiml.components import component, Component
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


    def main():
        # Start the guiml main loop
        run()


    if __name__ == '__main__':
        main()

We can now run our application with :code:`python3 app.py`.

.. note::

    Changing the :code:`templates.xml` while the application is running will
    automatically update the displayed components. This makes it easy to
    adjust the appearance of your application, without having to restart it.
    A restart of the application is only required for changes to the python
    files.

Our first component
-------------------

We have already seen how to define a component for the application itself. The
annotation :code:`@component(name='application', template=...)` registers a
new component with guiml under the name :code:`application` and the provided
template.

The easiest way to build a new component is to compose other existing
components. So if we want a :code:`hello_world` component, that only consists
of a text, then we can update the :code:`templates.xml` accordingly.

.. code-block:: xml
    :caption: Content of :code:`templates.xml`

    <templates>
        <application>
            <window>
                <hello_world></hello_world>
            </window>
        </application>

        <hello_world>
            <text text="Hello World!"></text>
        </hello_world>
    </templates>

However, this is not quite sufficient, as we also need to create the new
component in the source code. We could derive our component from
the :ref:`components:Component` base class. This, however, would be quite
cumbersome as we would need to implement everything ourselves. Given that our
component is supposed to hold other components, we should instead derive our
component from a container, such as a :ref:`div <components:div>`.

.. code-block:: py
    :caption: Snippet for :code:`app.py`

    from guiml.components import Div

    # Let us define a shorthand, as we will always use the same template file.
    # in this tutorial.
    def app_component(name):
        return component(name, template=resources.template_file('templates.xml'))

    @app_component("hello_world")
    class HelloWorld(Div):
        pass

We can now run the application again. Guiml will automatically expand all
components based on their template. So after expansion, the XML representing
our application is the following.


.. code-block:: xml

    <application>
        <window>
            <hello_world>
                <text text='Hello World!'></text>
            </hello_world>
        </window>
    </application>

One Way Property Binding
------------------------

To set a property dynamically we can bind it to a value that will be evaluated
in python. This is achieved by prefixing the property with :code:`py_`.

.. code-block:: xml
    :caption: Snippet for :code:`templates.xml`

    <hello_world>
        <text py_text="f'Hello {self.name}!'"></text>
    </hello_world>

.. code-block:: py
    :caption: Snippet for :code:`app.py`

    @app_component("hello_world")
    class HelloWorld(Div):
        def on_init(self):
            self.name = 'World'


What happens now is that guiml will evaluate :code:`f'Hello
{self.name}!'`, where self is our component, to :code:`'Hello World!'`. Then
the text property is set to that value. Instead of an f-string, you can also
pass any expression that is accepted by pythons built in `eval
<https://docs.python.org/3/library/functions.html#eval>`_ function.

The result is the same as before, but we can now programmatically change the
value of :code:`self.name` and thus update the display.


Custom Properties
-----------------

To allow other components to pass values into our component, we have to
specify which properties our component has. This is done by defining a a
`dataclass <https://docs.python.org/3/library/dataclasses.html>`_
named :code:`Properties` as inner class of our component.

.. code-block:: py
    :caption: Snippet for :code:`app.py`

    from dataclasses import dataclass

    @app_component("hello_world")
    class HelloWorld(Div):
        @dataclass
        class Properties(Div.Properties):
            name: str = "World"


.. note::

    Our component inherits from the class :code:`Div`. Therefore, our
    component should not only have the properties that we define but also the
    properties of a :code:`Div`. This is achieved by letting
    the :code:`Properties` class inherit from the :code:`Div.Properties`
    class.

Guiml will automatically provide an instance of the Properties class under
:code:`self.properties`. Hence, we can use the value by updating the property
binding on the :code:`text` component and setting property :code:`name` on
our :code:`hello_world` component to specify who we want to greet.

.. code-block:: xml
    :caption: Content of :code:`templates.xml`

    <templates>
        <application>
            <window>
                <hello_world name="Universe"></hello_world>
            </window>
        </application>

        <hello_world>
            <text py_text="f'Hello {self.properties.name}!'"></text>
        </hello_world>
    </templates>

Control Structures
------------------

Guiml also supports control structure in the markup language. This is done by
adding the special attribute :code:`control` to a component tag. A control
can either be a :code:`for` loop or an :code:`if` condition. For example,
the XML

.. code-block:: xml
    :caption: Snippet for :code:`templates.xml`

    <application>
        <window>
            <hello_world
                control="for name in ['Country', 'World', 'Universe']"
                py_name="name"></hello_world>
            <text control="if True" text="true"></text>
            <text control="if False" text="false"></text>
        </window>
    </application>

will evaluate to

.. code-block:: xml

    <application>
        <window>
            <hello_world name="Country"></hello_world>
            <hello_world name="World"></hello_world>
            <hello_world name="Universe"></hello_world>
            <text text="true"></text>
        </window>
    </application>

.. note::

    The variable used in the for loop will be available in the context passed
    to :code:`eval`, when doing property binding. This allows us to pass the
    value to other components.


Style Files
-----------

Adding all properties in the XML can become cumbersome. Instead we can use a
separate style file. Style files use YAML syntax and allow setting all
properties that could be set on the tag directly and vice versa. To make
styling easier guiml adds special attributes :code:`id` and :code:`class`,
which can be used to attach styles to a component. The style file is just a
YAML file where the top level key is either a component tag, an id prefixed
by :code:`$` or a class prefixed by :code:`.`.

Hence, if we describe our application with

.. code-block:: xml
    :caption: Snippet for :code:`templates.xml`

    <application>
        <window>
            <hello_world></hello_world>
            <hello_world id="some_id"></hello_world>
            <hello_world class="some_class"></hello_world>
        </window>
    </application>

then we can use a style file to set the name of our three component instances with

.. code-block:: yaml
    :caption: Content of :code:`styles.yml`

    application: # apply styles to the component template of application
        hello_word: # apply styles to all instances of the hello_world component
            name: Country
        $some_id: # apply styles to the component with the given id
            name: World
        .some_class: # apply styles to all components with the given class
            name: Universe

which tells guiml to expand the application XML to

.. code-block:: xml

    <application>
        <window>
            <hello_world name="Country"></hello_world>
            <hello_world id="some_id" name="World"></hello_world>
            <hello_world class="some_class" name="Universe"></hello_world>
        </window>
    </application>

To apply styles in the file :code:`styles.yaml` we can use the style argument
of the annotation function :code:`component`, e.g., by updating our
convenience function to the following.

.. code-block:: py
    :caption: Snippet for :code:`app.py`

    def app_component(name):
        return component(
            name=name,
            template=resources.template_file('templates.xml'),
            style=resources.style_file("styles.yml"))

.. note::

    Styles are only active within the scope of a component's template. The
    top-level key in the YAML file tells guiml to which component's template
    the style should be applied to.

Events
------

Events are just properties that start with :code:`on_`, however the assigned
value will always be passed to pythons built in `eval
<https://docs.python.org/3/library/functions.html#eval>`_ function and should
return a callable. The signature the callable should have depends on the
assigned property.

.. code-block:: xml
    :caption: Snippet for :code:`templates.xml`

        <hello_world>
            <text py_text="self.greeting"></text>
            <button on_click="self.hello">
                <text text='Hello!'></text>
            </button>
        </hello_world>

.. code-block:: py
    :caption: Snippet for :code:`app.py`

    @component("hello_world")
    class HelloWorld(Div):
        def on_init(self):
            self.greeting = ''

        def hello(self):
            self.greeting = 'Hello, you too!'


Two Way Binding
---------------

Instead of only passing a value into a component with one way binding. We can
also use two way binding to allow a component to write into a property. For
example, we can use tow way binding to always have the current value of an
input field. Two way binding is achieved by prefixing a property
with :code:`bind_`. For binding to work, the passed value must be assignable
in python.

.. code-block:: xml
    :caption: Snippet for :code:`templates.xml`

        <hello_world>
            <text py_text="f'Hello {self.name}!'"></text>
            <input bind_text="self.name"></text>
        </hello_world>

.. code-block:: py
    :caption: Snippet for :code:`app.py`

    @app_component("hello_world")
    class HelloWorld(Div):
        def on_init(self):
            self.name = 'World'


Dependency Injection
--------------------

So far all interaction between components has been between a component and its
child. In realistic applications this is often not sufficient and sharing
state between components can be quite complicated. Especially, if we do not
want to use global variables or a singleton pattern. Additionally, we might
want to keep state beyond the lifetime of a component and to have a better
separation of concerns: A component should just deal with displaying state
but not contain any application logic. This is where automatic dependency
injection comes to the rescue.

An Injectable is a class marked with :code:`@injectable
('some_component_tag')`. Classes marked as injectable will be automatically
created by guiml.

.. code-block:: py
    :caption: Snippet for :code:`app.py`

    from dataclasses import dataclass

    from guiml.injectables import Injectable
    from guiml.registry import injectable

    @injectable("window")
    class HelloWorldService(Injectable):

        @dataclass
        class Dependencies(Injectable.Dependencies):
            pass

        def on_init(self):
            self.name = "World"


This creates an injectable that is bound to a window. Whenever a new window is
created or destroyed so is a HelloWorldService. If multiple windows will be
created, there will be multiple HelloWorldService instances, one for each
window. To access an injectable in a component or in a different injectable,
we list it as a dependency.

.. code-block:: xml
    :caption: Snippet for :code:`templates.xml`

        <hello_world>
            <text py_text="f'Hello {self.dependencies.hello_service.name}!'"></text>
        </hello_world>

.. code-block:: py
    :caption: Snippet for :code:`app.py`

    @app_component("hello_world")
    class HelloWorld(Div):
        @dataclass
        class Dependencies(Div.Dependencies):
            hello_service: HelloWorldService

If a component or injectable has a dependency, then guiml will automatically
provide the dependency. Components can access the dependencies
under :code:`self.dependencies`, while injectables will get the dependencies
as a direct member. E.g. if a dependency is named :code:`foo` then it can be
accessed via :code:`self.foo`.

.. note::

    If component A has a dependency on an injectable and the injectable is
    bound to some component B, then B must be one of the parents of A.
    Otherwise, the dependency can not be resolved. If an injectable is
    provided by multiple parents, then the dependency will always be filled
    with the closest one.


Where to go next
----------------

You now have an understanding of all the fundamental concepts of guiml. To get
more control over how to layout components, you should look
into :doc:`layout`. An overview of builtin components can be found
in :doc:`components`. Or you can study the `examples <https://github.com/StephanGocht/guiml/tree/main/examples>`_ that come with guiml.

