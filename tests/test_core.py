import pytest


from guiml.core import *


@pytest.mark.parametrize("a,b,result",[
  (None, 1, 1),
  ({"text": None}, {"text": "foo"}, {"text": "foo"}),
  ({"text": None, "baa": False}, {"text": 1, "foo": True}, {"text": 1, "baa": False, "foo": True})

])
def test_merge_data(a, b, result):
  assert(result == merge_data(a, b))