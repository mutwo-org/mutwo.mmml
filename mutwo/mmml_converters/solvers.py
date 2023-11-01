from mutwo import core_events
from mutwo import mmml_converters
from mutwo import music_events


__all__ = ("register_solver",)


register_solver = mmml_converters.constants.SOLVER_REGISTRY.register_solver


@register_solver
def n(duration=1, pitch="", *args):
    # In mutwo.music we simply use space for separating between
    # multiple pitches. In a MMML expression this isn't possible,
    # as space indicates a new parameter. So we use commas in MMML,
    # but transform them to space for the 'mutwo.music' parser.
    pitch = pitch.replace(",", " ")
    # mutwo.music <0.26.0 bug: Empty string raises an exception.
    if not pitch:
        pitch = []
    return music_events.NoteLike(pitch, duration, *args)


@register_solver
def r(duration=1, *args):
    return music_events.NoteLike([], duration, *args)


@register_solver
def seq(tag=None):
    return core_events.TaggedSequentialEvent([], tag=tag)


@register_solver
def sim(tag=None):
    return core_events.TaggedSimultaneousEvent([], tag=tag)
