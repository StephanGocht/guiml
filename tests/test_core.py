import pytest

from dataclasses import dataclass, field

from guiml.core import *

from typing import Optional


@pytest.mark.parametrize("a,b,result", [(None, 1, 1),
                                        ({
                                            "text": None
                                        }, {
                                            "text": "foo"
                                        }, {
                                            "text": "foo"
                                        }),
                                        ({
                                            "text": None,
                                            "baa": False
                                        }, {
                                            "text": 1,
                                            "foo": True
                                        }, {
                                            "text": 1,
                                            "baa": False,
                                            "foo": True
                                        })])
def test_merge_data(a, b, result):
    assert (result == merge_data(a, b))


@dataclass
class DummyDataClass:
    val1: int = 1
    val2: str = field(default_factory=lambda: "baa")


@dataclass
class DummyDataClass2:
    val: Optional[DummyDataClass]


@pytest.mark.parametrize("data,data_type,expected", [
    ({}, DummyDataClass, DummyDataClass()),
    ({
        "val1": 2
    }, DummyDataClass, DummyDataClass(val1=2)),
    ({
        "val": None
    }, DummyDataClass2, DummyDataClass2(val=None)),
    ({
        "val": {}
    }, DummyDataClass2, DummyDataClass2(val=DummyDataClass())),
])
def test_structure(data, data_type, expected):
    assert (structure(data, data_type) == expected)
