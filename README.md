[![Documentation Status](https://readthedocs.org/projects/guiml/badge/?version=latest)](https://guiml.readthedocs.io/en/latest/?badge=latest)

guiml
=====

A simple to use GUI framework for python. You define what you want and the
framework does the rest. You build the UI out of components that are defined
using XML as markup language. The markup language allows you to interact with
your python code via variable binding, callbacks and the use of control flow
primitives. To help you with organizing your application, the framework
allows you to nicely compose components and comes with automated dependency
injection.

Ever wondered why so many GUIs nowadays seem to be written with a HTTP/CSS/JS
front end, even for desktop (e.g. via electron)? How is that the easiest way
of designing modern GUIs? Some things in web front end development are nice
and shiny, like live inspection and editing of styles, reactive variable
bindings, defining components and the UI in a nice markup language, allow
control flow in the markup language, have automatic dependency injection...

Can't we have all these nice things but in python? And without the hassle of a
client-server architecture?

This project is a case study where I try to figure out and build the GUI
framework that I would want to use. To not have to deal with legacy issues of
other GUI frameworks, this project starts quite low level using pyglet as
window engine and to deal with IO, cairo for drawing and pango for text
setting. Everything else is build from scratch.

Installation
============

Step 1) Install non Python Dependencies
---------------------------------------

### Debian/ Ubuntu / Windows with WSL2 + Debian

Install external requirenments (to access librsvg, cairo, pango from python)

    sudo apt install librsvg2-dev libcairo2-dev python3-gi-cairo
    cd guiml
    pip install -r requirements.txt

If you run into problems with installing the dependencies, you can check out
the links in the Other section below.

### Other (Windows Native / Mac / Other Linux Distributions)

For Windows it is recommended to use Debian on WSL2 ([Instructions]
(https://wiki.debian.org/InstallingDebianOn/Microsoft/Windows/SubsystemForLinux))
once on the Debian command line you can follow the normal Debian instructions
for installing this package.

If you are not on a debian derivate, then installation should in principle be
possible if you are sufficiently brave and smart, but you will have to figure
it out yourself. Here are some links to the dependencies that might be
helpfull.

You will need [pygobject](https://pygobject.readthedocs.io/en/latest/getting_started.html)
with cairo and librsvg.

Check how to install [cairocffi]
(https://doc.courtbouillon.org/cairocffi/stable/overview.html#installing-cffi)
and [pangocffi](https://pangocffi.readthedocs.io/en/latest/overview.html) on
their respective sites.

Once the dependencies are installed you should be able to run the examples
after installing the python dependencies

    pip install -r requirements.txt
    python3 -m examples.todolist

If you want to use guiml for your own project you can install it directly via

    pip install .

Step 2a) Installation from source
---------------------------------

It is recommended to use the latest version of pip and setuptools.

    pip install -U pip setuptools

You can install the project from source via

    git clone https://github.com/StephanGocht/guiml.git
    cd guiml
    pip install -e .

After installation (or just installing the packages from requirements.txt) you
can run the examples from the guiml folder to confirm everything is working.
For the todo list example run

    python3 -m examples.todolist

To update to the latest version, run

    git pull


Step 2b) Installation from PyPi
-------------------------------

tbd.

Current state
-------------

The current state is a proof of concept. It should work on the example
todolist, but is other wise terribly tested, terrebly documented and throws
non-sensical error messages at you when you do something wrong.


License
-------

The source code is licensed under the MIT license found at `/LICENSE`. The
icons under `/examples/todolist/resources/material-design-icons` are licensed
under Apache-2 license found under
`/examples/todolist/resources/material-design-icons/LICENSE`.

Related Work
------------

You can find more boradly used GUI frameworks on
[awesome-python](https://github.com/vinta/awesome-python#gui-development).

See also:

[collgraph](https://github.com/fork-tongue/collagraph)

> Write your Python interfaces in a declarative manner with plain render
> functions, component classes or even single-file components using Vue-like
> syntax, but with Python!
