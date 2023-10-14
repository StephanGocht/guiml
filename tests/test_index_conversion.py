import pytest


def byte_index_to_str_index(text, index):
    acc = 0
    i = 0
    for i, char in enumerate(text):
        if acc >= index:
            break

        char_size = len(char.encode('utf-8'))
        acc += char_size

    return i


def str_index_to_byte_index(text, index):
    return len(text[:index].encode('utf-8'))


@pytest.mark.parametrize("text, index", [('asdf', 3), ('asädfa', 5)])
def test_inversion(text, index):
    assert (index == byte_index_to_str_index(
        text, str_index_to_byte_index(text, index)))
