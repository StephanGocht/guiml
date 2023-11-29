Tutorial
========

.. warning::

    I just wrote the tutorial down without testing and did not have time to
    test the provided code. Please report if you encounter errors.

Introduction
------------

We can build an application with guiml by composing different components. The
root component is the application itself. Every other component has a single
parent component. This structure can easily be expressed via xml. For
example, the xml file

.. code-block:: xml

    <application>
        <window>
            <text text="Hello World!"></text>
        </window>
    </application>

specifies an application that has one window with a text component. To specify
the displayed text, the component has a property text.

Our first component
-------------------

Defining a component is as simple as creating a class inheriting from the
component base class and registering it with guiml.

.. code-block:: py

    from guiml.components import Component
    from guiml.registry import component

    @component('hello_world')
    class HelloWorld(Component):
        pass


The annotation :code:`@component('hello_world')` registers our new component
with guiml under the name :code:`hello_world`.

However, this component doesn't do much, yet. As we don't want to do
everything ourselves, we will build our component by extending an existing
container. Additionally, we use a template to fill our container.

.. code-block:: py

    from guiml.components import Div
    from guiml.registry import component

    @component(
        name="hello_world",
        template="""
        <template>
            <text text='Hello World!'></text>
        </template>
        """)
    class HelloWorld(Div):
        pass

We can now use our component in the application by using the following xml for our application.

.. code-block:: xml

    <application>
        <window>
            <hello_world></hello_world>
        </window>
    </application>

Guiml will automatically expand a components template. So after expansion,
the xml representing our application is actually the following.


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

.. code-block:: py

    from guiml.components import Div
    from guiml.registry import component

    @component(
        name="hello_world",
        template="""
        <template>
            <text py_text="f'Hello {self.name}!'"></text>
        </template>
        """)
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

    from dataclasses import dataclass

    from guiml.components import Div
    from guiml.registry import component

    @component(
        name="hello_world",
        template="""
        <template>
            <text py_text="f'Hello {self.properties.name}!'"></text>
        </template>
        """)
    class HelloWorld(Div):
        @dataclass
        class Properties(Div.Properties):
            name: str = "World"


Guiml will automatically provide an instance of the Properties class under
:code:`self.properties`. Hence, we can use the value by updating the property
binding on the text component accordingly.

.. note::

    Our component inherits from the class :code:`Div`. Therefore, our
    component should not only have the properties that we define but also the
    properties of a :code:`Div`. This is achieved by letting
    the :code:`Properties` class inherit from the :code:`Div.Properties`
    class.


We can now use the property name to specify who we want to greet.

.. code-block:: xml

    <application>
        <window>
            <hello_world name="Universe"></hello_world>
        </window>
    </application>


Control Structures
------------------

Guiml also supports control structure in the markup language. This is done by
adding the special attribute :code:`control` to a component tag. A control
can either be a :code:`for` loop or an :code:`if` condition. For example,
the xml

.. code-block:: xml

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

Adding all properties in the xml can become cumbersome. Instead we can use a
separate style file. Style files allow setting all properties that could be
set on the tag directly and vice versa. To make styling easier guiml adds
special attributes :code:`id` and :code:`class`, which can be used to attach
styles to a component. The style file is just a yaml file where the top level
key is either a component tag, an id prefixed by :code:`$` or a class
prefixed by :code:`.`.

Hence, if we describe our application with

.. code-block:: xml

    <application>
        <window>
            <hello_world></hello_world>
            <hello_world id="some_id"></hello_world>
            <hello_world class="some_class"></hello_world>
        </window>
    </application>

then we can use a style file to set the name of our three component instances with

.. code-block:: yaml

    hello_word:
        name: Country
    $some_id:
        name: World
    .some_class:
        name: Universe

which tells guiml to expand the application xml to

.. code-block:: xml

    <application>
        <window>
            <hello_world name="Country"></hello_world>
            <hello_world id="some_id" name="World"></hello_world>
            <hello_world class="some_class" name="Universe"></hello_world>
        </window>
    </application>

Events
------

Events are just properties that start with :code:`on_`, however the assigned
value will always be passed to pythons built in `eval
<https://docs.python.org/3/library/functions.html#eval>`_ function and should
return a callable. The signature of the callable should have depends on the
assigned property.


.. code-block:: py

    from guiml.components import Div
    from guiml.registry import component

    @component(
        name="hello_world",
        template="""
        <template>
            <text py_text="self.name"></text>
            <button on_click="self.hello">
                <text text='Hello!'></text>
            </button>
        </template>
        """)
    class HelloWorld(Div):
        def on_init(self):
            self.name = ''

        def hello(self):
            self.name = 'Hello, you too!'


Two Way Binding
---------------

Instead of only passing a value into a component with one way binding. We can
also use two way binding to allow a component to write into a property. This
is, for example, useful to always have the current value of an input field.
Two way binding is achieved by prefixing a property with :code:`bind_`.
For binding to work, the passed value must be assignable in python.

.. code-block:: py

    from guiml.components import Div
    from guiml.registry import component

    @component(
        name="hello_world",
        template="""
        <template>
            <text py_text="f'Hello {self.name}!'"></text>
            <input bind_text="self.name"></text>
        </template>
        """)
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
but not contain any application logic.

This is where dependency injection comes to the rescue.

An Injectable is a class marked with :code:`@injectable
('some_component_tag')` and thus managed by guiml.

.. code-block:: py

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

.. code-block:: py

    from dataclasses import dataclass

    from guiml.components import Div
    from guiml.registry import component

    @component(
        name="hello_world",
        template="""
        <template>
            <text py_text="f'Hello {self.dependencies.hello_service.name}!'"></text>
        </template>
        """)
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

