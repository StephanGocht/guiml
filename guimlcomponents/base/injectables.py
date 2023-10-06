from guiml.injectables import injectable, Injectable, Observable

@injectable("window")
class Canvas(Injectable):
  def on_init(self):
    # context will be created and set by the window component
    self.context = None
    self.on_draw = Observable()

  def draw(self):
    self.on_draw(self.context)

@injectable("window")
class MouseControl(Injectable):
  def on_init(self):
    self.on_mouse_motion = Observable()
    self.on_mouse_press = Observable()
    self.on_mouse_release = Observable()
    self.on_mouse_drag = Observable()
    self.on_mouse_enter = Observable()
    self.on_mouse_leave = Observable()
    self.on_mouse_scroll = Observable()

@injectable("window")
class TextControl(Injectable):
  def on_init(self):
    self.on_text = Observable()
    self.on_text_motion = Observable()


