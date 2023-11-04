__all__ = ("MalformedMMML", "NoDecoderExists", "NoEncoderExists")


class MalformedMMML(Exception):
    """A malformed MMML expression"""


class NoDecoderExists(Exception):
    """A decoder exists for a given MMML expression"""

    def __init__(self, expression_keyword: str):
        super().__init__(
            f"No decoder has been defined for expression '{expression_keyword}'."
        )


class NoEncoderExists(Exception):
    """No encoder exists for a given event"""

    def __init__(self, event_type):
        super().__init__(f"No encoder has been defined for '{event_type}'.")
