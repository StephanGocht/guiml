import dataclasses
from dataclasses import dataclass
from collections import defaultdict

from typing import Optional
import typing

class Patient:
  @dataclass
  class Dependencies:
    pass

class Injectable:
  def __init__(self, dependencies):
    for field in dataclasses.fields(dependencies):
      setattr(self, field.name, getattr(dependencies, field.name))

    self.on_init()

  def on_init(self):
    pass

_injectables = defaultdict(list)

def injectable(providers):
  if isinstance(providers, str):
    providers = [providers]

  def register(cls):
    for provider in providers:
      _injectables[provider].append(cls)

    return cls

  return register

class CyclicDependencyError(RuntimeError):
  pass

def get_dependency_class(injectable):
  return injectable.Dependencies

def get_dependencies(injectable, with_name = False):
  dependency_class = get_dependency_class(injectable)
  resolved_types = typing.get_type_hints(dependency_class)

  if with_name:
    return [(field.name, resolved_types[field.name]) for field in dataclasses.fields(dependency_class)]
  else:
    return [resolved_types[field.name] for field in dataclasses.fields(dependency_class)]

class DependencyResolver:
  @dataclass
  class Node:
    injectable: type
    dependencies: list
    t_visit: Optional[int] = None

  def __init__(self, injectables):
    self.nodes = {
      injectable: self.Node(injectable, get_dependencies(injectable))
      for injectable in injectables
    }

    self.notvisited = set(injectables)
    self.t = 0

    while self.notvisited:
      for node in self.notvisited:
        self.visit(self.nodes[node])
        break

  def visit(self, node):
    try:
      self.notvisited.remove(node.injectable)
    except KeyError:
      if node.t_visit is None:
        raise CyclicDependencyError()
      else:
        return
    else:
      for child in node.dependencies:
        self.visit(self.nodes[child])

      node.t_visit = self.t
      self.t += 1

  def __iter__(self):
    dag_order = sorted(self.nodes.values(), key = lambda x: x.t_visit)
    return iter( (node.injectable for node in dag_order) )

class Injector:
  def __init__(self):
    # dict mapping injectable classes to its instance
    self.injectables = {}

  def add_tag(self, tag):
    to_add = DependencyResolver(_injectables[tag])
    for injectable in to_add:
      args = {}
      for field_name, field_type in get_dependencies(injectable, with_name = True):
        args[field_name] = self.injectables[field_type]

      self.injectables[injectable] = injectable(get_dependency_class(injectable)(**args))

  def pop_tag(self):
    pass

  def copy(self):
    pass

  def __getitem__(self, key):
    return self.injectables[key]

