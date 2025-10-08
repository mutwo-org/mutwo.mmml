import typing

from mutwo import core_events
from mutwo import core_parameters
from mutwo.core_utilities import camel_case_to_snake_case
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
    instrument_list=None,
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
        instrument_list=instrument_list or [],
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
    instrument_list=None,
):
    return music_events.NoteLike(
        [],
        duration,
        volume=volume,
        playing_indicator_collection=playing_indicator_collection,
        notation_indicator_collection=notation_indicator_collection,
        lyric=lyric,
        instrument_list=instrument_list or [],
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
    d = _asmmml.duration(n.duration)

    pic = _asmmml.indicator_collection(n.playing_indicator_collection)
    nic = _asmmml.indicator_collection(n.notation_indicator_collection)

    if n.pitch_list:
        p = _asmmml.pitch_list(n.pitch_list)
        v = _asmmml.volume(n.volume)
        header = f"n {d} {p} {v} {pic} {nic}"
    else:
        header = f"r {d} {pic} {nic}"

    if n.grace_note_consecution:
        block = "\n" + _compound_to_block(n.grace_note_consecution)
    else:
        block = ""

    return f"{header}{block}"


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
    tempo = _asmmml.tempo(e.tempo)
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


class __asmmml:
    _cache = {}  # singleton

    def __getattr__(self, param_type):
        try:
            return self._cache[param_type]
        except KeyError:
            v = self._cache[param_type] = getattr(
                mmml_converters.configurations,
                f"DEFAULT_{camel_case_to_snake_case(param_type).upper()}_TO_MMML_STRING",
            )
            return v


_asmmml = __asmmml()
