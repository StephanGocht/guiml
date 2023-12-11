Components
==========

Build in Components
-------------------

Button
~~~~~~

.. autoclass:: guimlcomponents.base.container.Button()

    .. autoclass:: guimlcomponents.base.container.Button.Properties()
         :members:
         :undoc-members:
         :inherited-members:

Div
~~~

.. autoclass:: guiml.components.Div()

    .. autoclass:: guiml.components.Div.Properties()
         :members:
         :undoc-members:
         :inherited-members:


Input
~~~~~

.. autoclass:: guimlcomponents.base.text.Input()

    .. autoclass:: guimlcomponents.base.text.Input.Properties()
         :members:
         :undoc-members:
         :inherited-members:

Svg
~~~

.. autoclass:: guimlcomponents.base.image.Svg()

    .. autoclass:: guimlcomponents.base.image.Svg.Properties()
         :members:
         :undoc-members:
         :inherited-members:

Text
~~~~

.. autoclass:: guimlcomponents.base.text.Text()

    .. autoclass:: guimlcomponents.base.text.Text.Properties()
         :members:
         :undoc-members:
         :inherited-members:

Window
~~~~~~

.. autoclass:: guimlcomponents.base.window.Window()

    .. autoclass:: guimlcomponents.base.window.Window.Properties()
         :members:
         :undoc-members:
         :inherited-members:


Important base classes for components
-------------------------------------

Component
~~~~~~~~~

.. autoclass:: guiml.components.Component()
    :members:
    :undoc-members:


StyleClassHandler
~~~~~~~~~~~~~~~~~

.. autoclass:: guiml.components.StyleClassHandler()
    :members:


DrawableComponent
~~~~~~~~~~~~~~~~~

.. autoclass:: guiml.components.DrawableComponent()

    .. autoclass:: guiml.components.DrawableComponent.Properties()
        :members:
        :undoc-members:


    .. automethod:: on_draw

Container
~~~~~~~~~

.. autoclass:: guiml.components.Container()
    :members: wrap_size, width, height
    :undoc-members:

    .. autoclass:: guiml.components.Container.Properties()
         :members:
         :undoc-members:

Property Types
--------------

.. autoclass:: guimlcomponents.base.shared.Color()
     :members:
     :undoc-members:

.. autoclass:: guimlcomponents.base.shared.Border()
     :members:
     :undoc-members:

.. autoclass:: guimlcomponents.base.shared.Rectangle()

    .. autoattribute:: top
    .. autoattribute:: left
    .. autoattribute:: bottom
    .. autoattribute:: right