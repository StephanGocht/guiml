

Using Material Design Icons Font
================================

Instead of adding individual SVG files for icons, it is common in Webdesign to
use an icon font such as (Material Design Icon Font)
[https://fonts.google.com/icons].

The advantage of this approach is to have less files (probably more important
for web than for this project) and to be able to easily color the icons via
the text engine.


Pango does support different fonts, which allows use these fonts as well.
However, it seems that dynamically loading a font is quite system specific
and would take some time to get working properly across systems.

Debian also ships fonts from projects that are derived from the Material
Design Icon fonts, such as the package `fonts-materialdesignicons-webfont`
which comes from https://github.com/Templarian/MaterialDesign-Webfont .

A problem with these fonts is that the used code points vary between versions,
and hence the code points shown on the website are not be up to date. This is
why these fonts come with .css files that map a name to a code point. For
example, the debian package `fonts-materialdesignicons-webfont` also includes
the file

    /usr/share/fonts-materialdesignicons-webfont/css/materialdesignicons.css

Which contains the required mapping. For example the css code

    .mdi-access-point:before {
      content: "\F002";
    }

says that the icon 'access-point' has the codepoint `F002`, which we can
access in python using `\uf002`.

Once the font is installed it can be used via the pango styling syntax

    <span font="Material Design Icons" foreground="red">\uF597</span>



Improvements
============

- automatically add base class for dependencies and properties
- scrollable field
- multiple text inputs
- allow passing inner xml to component and use of control and one way binding