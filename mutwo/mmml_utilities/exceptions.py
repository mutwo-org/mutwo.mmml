__all__ = ("MalformedMMML", "NoDecoderExists")


class MalformedMMML(Exception):
    """A malformed MMML expression"""


class NoDecoderExists(Exception):
    """A decoder exists for a given MMML expression"""

    def __init__(self, expression_keyword: str):
        super().__init__(f"No decoder has been defined for expression '{expression_keyword}'.")
