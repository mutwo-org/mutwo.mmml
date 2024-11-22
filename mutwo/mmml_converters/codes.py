import typing

from mutwo import core_events
from mutwo import core_parameters
from mutwo import mmml_converters
from mutwo import music_events
from mutwo import music_parameters


__all__ = ("register_decoder", "register_encoder")


register_decoder = mmml_converters.constants.DECODER_REGISTRY.register_decoder
register_encoder = mmml_converters.constants.ENCODER_REGISTRY.register_encoder

EventTuple: typing.TypeAlias = tuple[core_events.abc.Event, ...]


@register_decoder
def n(
    event_tuple: EventTuple,
    duration=1,
    pitch="",
    volume="mf",
    # We use a different order than in 'NoteLike.__init__', because
    # we can't provide grace or after grace notes in the MMML header,
    # therefore we skip them.
    playing_indicator_collection=None,
    notation_indicator_collection=None,
    lyric=music_parameters.DirectLyric(""),
    instrument_list=[],
):
    # In mutwo.music we simply use space for separating between
    # multiple pitches. In a MMML expression this isn't possible,
    # as space indicates a new parameter. So we use commas in MMML,
    # but transform them to space for the 'mutwo.music' parser.
    pitch = pitch.replace(",", " ")
    # mutwo.music <0.26.0 bug: Empty string raises an exception.
    if not pitch:
        pitch = []
    return music_events.NoteLike(
        pitch,
        duration,
        volume=volume,
        playing_indicator_collection=playing_indicator_collection,
        notation_indicator_collection=notation_indicator_collection,
        lyric=lyric,
        instrument_list=instrument_list,
        grace_note_consecution=core_events.Consecution(event_tuple),
    )


@register_decoder
def r(
    event_tuple: EventTuple,
    duration=1,
    # Also add other parameters to rest, because sometimes it's necessary that
    # a rest also has notation or playing indicators
    volume="mf",
    # We use a different order than in 'NoteLike.__init__', because
    # we can't provide grace or after grace notes in the MMML header,
    # therefore we skip them.
    playing_indicator_collection=None,
    notation_indicator_collection=None,
    lyric=music_parameters.DirectLyric(""),
    instrument_list=[],
):
    return music_events.NoteLike(
        [],
        duration,
        volume=volume,
        playing_indicator_collection=playing_indicator_collection,
        notation_indicator_collection=notation_indicator_collection,
        lyric=lyric,
        instrument_list=instrument_list,
        grace_note_consecution=core_events.Consecution(event_tuple),
    )


@register_decoder
def cns(event_tuple: EventTuple, tag=None, tempo=None):
    return core_events.Consecution(event_tuple, tag=tag, tempo=tempo)


@register_decoder
def cnc(event_tuple: EventTuple, tag=None, tempo=None):
    return core_events.Concurrence(event_tuple, tag=tag, tempo=tempo)


@register_encoder(music_events.NoteLike)
def note_like(n: music_events.NoteLike):
    d = _parse_duration(n.duration)

    pic = _parse_indicator_collection(n.playing_indicator_collection)
    nic = _parse_indicator_collection(n.notation_indicator_collection)

    if n.pitch_list:
        p = ",".join([_parse_pitch(p) for p in n.pitch_list])
        v = _parse_volume(n.volume)
        header = f"n {d} {p} {v} {pic} {nic}"
    else:
        header = f"r {d} {pic} {nic}"

    if n.grace_note_consecution:
        block = "\n" + _compound_to_block(n.grace_note_consecution)
    else:
        block = ""

    return f"{header}{block}"


def _parse_duration(duration: core_parameters.abc.Duration):
    match duration:
        case core_parameters.DirectDuration():
            d = duration.beat_count
            if (intd := int(d)) == float(d):
                d = intd
            return str(d)
        case core_parameters.RatioDuration():
            return str(duration.ratio)
        case _:
            raise NotImplementedError(duration)


def _parse_pitch(pitch: music_parameters.abc.Pitch):
    match pitch:
        case music_parameters.WesternPitch():
            return pitch.name
        case music_parameters.ScalePitch():
            return f"{pitch.scale_degree + 1}:{pitch.octave}"
        case music_parameters.JustIntonationPitch():
            r = str(pitch.ratio)
            # Ensure we always render ratios with '/', otherwise
            # the pitch parser of 'mutwo.music' won't be able to
            # re-load them.
            if "/" not in r:
                r = f"{r}/1"
            return r
        case _:
            raise NotImplementedError(pitch)


def _parse_volume(volume: music_parameters.abc.Volume):
    match volume:
        case music_parameters.WesternVolume():
            return volume.name
        case _:
            raise NotImplementedError()


def _parse_indicator_collection(indicator_collection):
    mmml = ""
    for name, indicator in indicator_collection.indicator_dict.items():
        if indicator.is_active:
            # XXX: This needs to be fixed in 'mutwo.music':
            # ottava with 'octave_count=0' must be inactive.
            if getattr(indicator, "octave_count", None) == 0:
                continue
            for k, v in indicator.get_arguments_dict().items():
                if mmml:
                    mmml += ";"
                mmml += f"{name}.{k}={v}"
    return mmml or mmml_converters.constants.IGNORE_MAGIC


@register_encoder(core_events.Consecution)
def consecution(
    cns: core_events.Consecution,
):
    return _compound("cns", cns)


@register_encoder(core_events.Concurrence)
def concurrence(
    cnc: core_events.Concurrence,
):
    return _compound("cnc", cnc)


def _compound(code: str, e: core_events.abc.Compound):
    tempo = _parse_tempo(e.tempo)
    is_default_tempo = _is_default_tempo(e.tempo)
    header = code
    if e.tag and is_default_tempo:
        header = f"{code} {e.tag}"
    elif not is_default_tempo:
        header = f"{code} {e.tag or '_'} {tempo}"
    block = _compound_to_block(e)
    return f"{header}\n{block}"


def _is_default_tempo(tempo: core_parameters.abc.Tempo):
    default_bpm = 60
    match tempo:
        case core_parameters.FlexTempo():
            return tempo.is_static and tempo.bpm == default_bpm
        case _:
            return tempo.bpm == default_bpm


def _parse_tempo(tempo: core_parameters.abc.Tempo):
    match tempo:
        case core_parameters.FlexTempo():
            point_list = list(
                map(
                    list,
                    zip(
                        map(_int, tempo.absolute_time_in_floats_tuple),
                        map(_int, tempo.value_tuple),
                    ),
                )
            )
            return str(point_list).replace(" ", "")
        case _:
            return str(_int(tempo.bpm))


def _int(v: float):
    """Write number without digits if possible"""
    try:
        is_integer = v.is_integer()
    except AttributeError:
        pass
    else:
        if is_integer:
            v = int(v)
    return v


def _compound_to_block(compound: core_events.abc.Compound) -> str:
    if not compound:
        return ""
    block = [""]
    for e in compound:
        expression = mmml_converters.encode_event(e)
        for line in expression.split("\n"):
            line = f"{mmml_converters.constants.INDENTATION}{line}" if line else line
            block.append(line)
    block.append("")
    return "\n".join(block)
