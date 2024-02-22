from mutwo import core_converters
from mutwo import core_events
from mutwo import mmml_converters

__all__ = ("EventToMMMLExpression", "encode_event")


class EventToMMMLExpression(core_converters.abc.Converter):
    def convert(self, event: core_events.abc.Event) -> mmml_converters.MMMLExpression:
        return encode_event(event)


def encode_event(event: core_events.abc.Event) -> mmml_converters.MMMLExpression:
    return mmml_converters.constants.ENCODER_REGISTRY[type(event)](event)
