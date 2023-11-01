__all__ = ("MalformedMMML", "NoSolverExists")


class MalformedMMML(Exception):
    """A malformed MMML expression"""


class NoSolverExists(Exception):
    """A solver exists for a given MMML expression"""

    def __init__(self, expression_keyword: str):
        super().__init__(f"No solver has been defined for expression '{expression_keyword}'.")
