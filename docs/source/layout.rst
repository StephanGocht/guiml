Layout
======

All components are extrinsically sized, that is they have a property called
position that can be set to define where the component is drawn. This
position specifies a bounding box for the component to draw in. How the
component fills the bounding box depends on the used component.

Some components are intrinsically sized, that is they have a width and height
attribute.

A component that can contain other components is called a container and has a
property layout. The layout property specifies which algorithm is used to
layout the components in the container.

Guiml comes with a few predefined layout algorithms that can be combined to
create a wide variety of layouts. If that is not sufficient for your needs
you can write your own layout algorithm.

StackLayout
-----------

.. autoclass:: guimlcomponents.base.layout.StackLayout

    .. autoclass:: guimlcomponents.base.layout.StackLayout.Properties()
         :members:
         :undoc-members:

    .. autoclass:: guimlcomponents.base.layout.StackLayout.ChildProperties()
         :members:
         :undoc-members:


AlignLayout
-----------

.. autoclass:: guimlcomponents.base.layout.AlignLayout

    .. .. autoclass:: guimlcomponents.base.layout.AlignLayout.Properties()
    ..      :members:
    ..      :undoc-members:

    .. autoclass:: guimlcomponents.base.layout.AlignLayout.ChildProperties()
         :members:
         :undoc-members:


GridLayout
----------

.. autoclass:: guimlcomponents.base.layout.GridLayout

    .. autoclass:: guimlcomponents.base.layout.GridLayout.Properties()
         :members:
         :undoc-members:

    .. autoclass:: guimlcomponents.base.layout.GridLayout.ChildProperties()
         :members:
         :undoc-members: