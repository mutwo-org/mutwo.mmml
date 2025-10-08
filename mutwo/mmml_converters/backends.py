from mutwo import core_converters
from mutwo import core_events
from mutwo import core_parameters
from mutwo import mmml_converters
from mutwo import music_parameters

__all__ = (
    "EventToMMMLExpression",
    "encode_event",
    "DurationToMMMLString",
    "TempoToMMMLString",
    "PitchToMMMLString",
    "PitchListToMMMLString",
    "PitchIntervalToMMMLString",
    "VolumeToMMMLString",
    "IndicatorCollectionToMMMLString",
)


class EventToMMMLExpression(core_converters.abc.Converter):
    def convert(self, event: core_events.abc.Event) -> mmml_converters.MMMLExpression:
        return encode_event(event)


def encode_event(event: core_events.abc.Event) -> mmml_converters.MMMLExpression:
    return mmml_converters.constants.ENCODER_REGISTRY[type(event)](event)


# NOTE Parameter parsers inverse '<Param>.from_any'


class DurationToMMMLString(core_converters.abc.Converter):
    def convert(self, duration: core_parameters.abc.Duration) -> str:
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


class TempoToMMMLString(core_converters.abc.Converter):
    def convert(self, tempo: core_parameters.abc.Tempo) -> str:
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


class PitchToMMMLString(core_converters.abc.Converter):
    def convert(self, pitch: music_parameters.abc.Pitch) -> str:
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


class PitchListToMMMLString(core_converters.abc.Converter):
    def __init__(self, parse_pitch=PitchToMMMLString()):
        self._parse_pitch = parse_pitch

    def convert(self, pitch_list: music_parameters.abc.PitchList) -> str:
        return ",".join([self._parse_pitch(p) for p in pitch_list])


class PitchIntervalToMMMLString(core_converters.abc.Converter):
    def convert(self, pitch_interval: music_parameters.abc.PitchInterval) -> str:
        match pitch_interval:
            case music_parameters.JustIntonationPitch():
                r = str(pitch_interval.ratio)
                # Ensure we always render ratios with '/', otherwise
                # the pitch parser of 'mutwo.music' won't be able to
                # re-load them.
                if "/" not in r:
                    r = f"{r}/1"
                return r
            case music_parameters.WesternPitchInterval():
                return pitch_interval.name
            case _:
                return str(pitch_interval.cents)


class VolumeToMMMLString(core_converters.abc.Converter):
    def convert(self, volume: music_parameters.abc.Volume) -> str:
        match volume:
            case music_parameters.WesternVolume():
                return volume.name
            case _:
                raise NotImplementedError()


class IndicatorCollectionToMMMLString(core_converters.abc.Converter):
    def convert(
        self, indicator_collection: music_parameters.abc.IndicatorCollection
    ) -> str:
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
