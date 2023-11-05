from mutwo import core_events
from mutwo import mmml_converters
from mutwo import music_events
from mutwo import music_parameters


__all__ = ("register_decoder", "register_encoder")


register_decoder = mmml_converters.constants.DECODER_REGISTRY.register_decoder
register_encoder = mmml_converters.constants.ENCODER_REGISTRY.register_encoder


@register_decoder
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


@register_decoder
def r(duration=1, *args):
    return music_events.NoteLike([], duration, *args)


@register_decoder
def seq(tag=None):
    return core_events.TaggedSequentialEvent([], tag=tag)


@register_decoder
def sim(tag=None):
    return core_events.TaggedSimultaneousEvent([], tag=tag)


@register_encoder(music_events.NoteLike)
def note_like(n: music_events.NoteLike):
    d = str(n.duration.duration)
    if n.pitch_list:
        p = ",".join([_parse_pitch(p) for p in n.pitch_list])
        v = _parse_volume(n.volume)
        return f"n {d} {p} {v}"
    else:
        return f"r {d}"


def _parse_pitch(pitch: music_parameters.abc.Pitch):
    match pitch:
        case music_parameters.WesternPitch():
            return pitch.name
        case music_parameters.ScalePitch():
            return str(pitch.scale_degree + 1)
        case music_parameters.JustIntonationPitch():
            return str(pitch.ratio)
        case _:
            raise NotImplementedError(pitch)


def _parse_volume(volume: music_parameters.abc.Volume):
    match volume:
        case music_parameters.WesternVolume():
            return volume.name
        case _:
            raise NotImplementedError()


@register_encoder(core_events.SequentialEvent, core_events.TaggedSequentialEvent)
def sequential_event(
    seq: core_events.SequentialEvent | core_events.TaggedSequentialEvent,
):
    tag = getattr(seq, "tag", None)
    header = f"seq {tag}" if tag else "seq"
    block = _complex_event_to_block(seq)
    return f"{header}\n{block}"


@register_encoder(core_events.SimultaneousEvent, core_events.TaggedSimultaneousEvent)
def simultaneous_event(
    sim: core_events.SimultaneousEvent | core_events.TaggedSimultaneousEvent,
):
    tag = getattr(sim, "tag", None)
    header = f"sim {tag}" if tag else "sim"
    block = _complex_event_to_block(sim)
    return f"{header}\n{block}"


def _complex_event_to_block(complex_event: core_events.abc.ComplexEvent) -> str:
    if not complex_event:
        return ""
    block = [""]
    for e in complex_event:
        expression = mmml_converters.encode_event(e)
        for line in expression.split("\n"):
            line = f"{mmml_converters.constants.INDENTATION}{line}" if line else line
            block.append(line)
    block.append("")
    return "\n".join(block)
