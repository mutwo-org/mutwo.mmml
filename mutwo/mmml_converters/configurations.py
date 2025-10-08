from functools import cached_property
import sys

from mutwo.core_utilities import camel_case_to_snake_case


class configurations(sys.modules[__name__].__class__):
    @cached_property
    def mmml_converters(self):
        from mutwo import mmml_converters

        return mmml_converters


_types = "Duration Tempo Pitch PitchList Volume IndicatorCollection".split(" ")
__all__ = tuple(f"DEFAULT_{camel_case_to_snake_case(t).upper()}_TO_MMML_STRING" for t in _types)


def cached_converter(t):
    def _(self):
        return getattr(self.mmml_converters, t)()

    return cached_property(_)


for t, name in zip(_types, __all__):
    t = f"{t}ToMMMLString"
    prop = cached_converter(t)
    setattr(configurations, name, prop)
    prop.__set_name__(configurations, name)


# configurations = _configurations("configurations")
sys.modules[__name__].__class__ = configurations
del cached_converter, camel_case_to_snake_case, name, prop, t, _types, sys
