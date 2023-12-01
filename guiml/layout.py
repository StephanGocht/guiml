from dataclasses import dataclass


class Layout:
    """
    Abstract base class for layouts.
    """

    @dataclass
    class Properties():
        """
        Properties that can be set on the component that uses this layout.
        """

        pass

    @dataclass
    class ChildProperties():
        """
        Properties that can be set on childs of the component that uses this
        layout.
        """

        pass

    def __init__(self, component):
        pass

    def compute_recommended_size(self, children):
        raise NotImplementedError()

    def layout(self, children):
        raise NotImplementedError()
