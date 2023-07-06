import dataclasses
from collections import defaultdict

from typing import Optional

class Patient:
  @dataclass
  class Dependencies:
    pass

class Injectable:
  def __init__(self, dependencies):
    for field in dataclasses.fields(dependencies);
      setattr(self, field.name, getattr(dependencies, field.name))

_injectables = defaultdict(list)

def injectable(providers):
  if isinstance(providers, str):
    providers = [providers]

  def register(cls):
    for provider in providers:
      _injectables[provider].append(cls)

    return cls

class CyclicDependencyError(RuntimeError):
  pass

def dependencies(injectable):
  return injectable.Dependencies

class DependencyResolver:
  @dataclass
  class Node:
    injectable: type
    dependencies: list
    t_visit: Optional[int] = None

  def __init__(self, injectables):
    self.nodes = {
      injectable: Node(
        injectable,
        [field.type for field in dataclasses.fields(dependencies(injectable))]
      )

      for injectable in injectables
    }

    self.notvisited = set(injectables)
    self.t = 0

    while self.notvisited:
      for node in self.notvisited:
        self.visit(node)
        break

  def visit(self, node):
    try:
      self.notvisited.remove(node)
    except KeyError:
      if node.t_visit is None:
        raise CyclicDependencyError()
      else:
        return
    else:
      for child in node.dependencies:
        self.visit(child)

      node.t_visit = self.t
      self.t += 1

  def __iter__(self):
    dag_order = sorted(self.nodes.values, key = lambda x: x.t_visit)
    return iter( (node.injectable for node in dag_order) )

class Injector:
  def __init__(self):
    # dict mapping injectable classes to its instance
    self.injectables = {}

  def add_tag(self, tag):
    to_add = DependencyResolver(_injectables[tag])
    for injectable in to_add:
      args = {}
      for field in dataclasses.fields(dependencies(injectable)):
        args[field.name] = self.injectables[field.type]

      self.injectables[injectable] = injectable(dependencies(injectable)(**args))

  def pop_tag(self):
    pass

  def copy(self):
    pass
