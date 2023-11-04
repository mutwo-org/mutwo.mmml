import typing

import chevron

from mutwo import core_converters
from mutwo import core_events
from mutwo import mmml_converters
from mutwo import mmml_utilities

__all__ = ("MMMLExpressionToEvent", "MMMLExpression")


MMMLExpression: typing.TypeAlias = str


class MMMLExpressionToEvent(core_converters.abc.Converter):
    """Convert a MMML expression to a mutwo event.

    **Example:**

    >>> from mutwo import mmml_converters
    >>> c = mmml_converters.MMMLExpressionToEvent()
    >>> mmml = r'''
    ... seq my-melody
    ...     n 1/4 c
    ...     n 1/8 d ff
    ...     n 1/8 e
    ...     n 1/2 d
    ... '''
    >>> c.convert(mmml)
    TaggedSequentialEvent([NoteLike(duration = DirectDuration(duration = 1/4), instrument_list = [], lyric = DirectLyric(phonetic_representation = ), pitch_list = [WesternPitch('c', 4)], tempo_envelope = TempoEnvelope([TempoEvent(curve_shape = 0, duration = DirectDuration(duration = 1), tempo_point = DirectTempoPoint(BPM = 60, reference = 1)), TempoEvent(curve_shape = 0, duration = DirectDuration(duration = 0), tempo_point = DirectTempoPoint(BPM = 60, reference = 1))]), volume = WesternVolume(amplitude = 0.12328467394420659)), NoteLike(duration = DirectDuration(duration = 1/8), instrument_list = [], lyric = DirectLyric(phonetic_representation = ), pitch_list = [WesternPitch('d', 4)], tempo_envelope = TempoEnvelope([TempoEvent(curve_shape = 0, duration = DirectDuration(duration = 1), tempo_point = DirectTempoPoint(BPM = 60, reference = 1)), TempoEvent(curve_shape = 0, duration = DirectDuration(duration = 0), tempo_point = DirectTempoPoint(BPM = 60, reference = 1))]), volume = WesternVolume(amplitude = 0.2848035868435801)), NoteLike(duration = DirectDuration(duration = 1/8), instrument_list = [], lyric = DirectLyric(phonetic_representation = ), pitch_list = [WesternPitch('e', 4)], tempo_envelope = TempoEnvelope([TempoEvent(curve_shape = 0, duration = DirectDuration(duration = 1), tempo_point = DirectTempoPoint(BPM = 60, reference = 1)), TempoEvent(curve_shape = 0, duration = DirectDuration(duration = 0), tempo_point = DirectTempoPoint(BPM = 60, reference = 1))]), volume = WesternVolume(amplitude = 0.2848035868435801)), NoteLike(duration = DirectDuration(duration = 1/2), instrument_list = [], lyric = DirectLyric(phonetic_representation = ), pitch_list = [WesternPitch('d', 4)], tempo_envelope = TempoEnvelope([TempoEvent(curve_shape = 0, duration = DirectDuration(duration = 1), tempo_point = DirectTempoPoint(BPM = 60, reference = 1)), TempoEvent(curve_shape = 0, duration = DirectDuration(duration = 0), tempo_point = DirectTempoPoint(BPM = 60, reference = 1))]), volume = WesternVolume(amplitude = 0.2848035868435801))])
    """

    def convert(self, expression: MMMLExpression, **kwargs) -> core_events.abc.Event:
        """Convert MMML expression to a mutwo event.

        :param expression: A MMML expression.
        :type expression: str
        :param **kwargs: A MMML expression may contain commands of the
            `mustache template language <https://mustache.github.io/mustache.5.html>`_.
            Users can specify data for the mustache parser via
            keyword-arguments.
        :type **kwargs: typing.Any

        **Example with mustache variables:**

        >>> from mutwo import mmml_converters
        >>> c = mmml_converters.MMMLExpressionToEvent()
        >>> expr = "n {{duration}} {{pitch}}"
        >>> c.convert(expr, duration='1/2', pitch='c')
        NoteLike(duration = DirectDuration(duration = 1/2), instrument_list = [], lyric = DirectLyric(phonetic_representation = ), pitch_list = [WesternPitch('c', 4)], tempo_envelope = TempoEnvelope([TempoEvent(curve_shape = 0, duration = DirectDuration(duration = 1), tempo_point = DirectTempoPoint(BPM = 60, reference = 1)), TempoEvent(curve_shape = 0, duration = DirectDuration(duration = 0), tempo_point = DirectTempoPoint(BPM = 60, reference = 1))]), volume = WesternVolume(amplitude = 0.2848035868435801))
        """
        e = chevron.render(expression, dict(**kwargs))
        return process_expression(e)


def process_expression(expression: str) -> core_events.abc.Event:
    header, block = _split_to_header_and_block(expression)
    event = process_header(header)
    process_block(block, event)
    return event


def _split_to_header_and_block(expression: str):
    header, block = None, expression
    while not header:
        if not block:
            raise mmml_utilities.MalformedMMML("No MMML expression found")
        header, _, block = block.partition("\n")
    return header, block


def process_block(block: str, event: core_events.abc.ComplexEvent):
    expression_tuple = _split_to_expression_tuple(block)
    for expression in expression_tuple:
        event.append(process_expression(expression))


def _split_to_expression_tuple(mmml: str) -> tuple[list[str], ...]:
    lines = filter(bool, mmml.split("\n"))

    expression_list = []
    expression_line_list: list[str] = []
    for line in lines:
        # First drop indentation, but check if actually exists. If it
        # doesn't exist it means there is a problem in the expression.
        if not line.startswith(mmml_converters.constants.INDENTATION):
            raise mmml_utilities.MalformedMMML(
                f"Bad line '{line}'. Missing indentation?"
            )
        line = line[len(mmml_converters.constants.INDENTATION) :]

        # Test that first line is a header / has no indentation
        if line.startswith(mmml_converters.constants.INDENTATION):
            if not expression_line_list:
                raise mmml_utilities.MalformedMMML("First line needs to start a block")
            expression_line_list.append(line)
        else:
            if expression_line_list:
                expression_list.append(expression_line_list)
            expression_line_list = [line]
    if expression_line_list:
        expression_list.append(expression_line_list)
    return tuple("\n".join(e) for e in expression_list)


def process_header(header: str) -> core_events.abc.Event:
    data = []
    for n in header.split(" "):
        if n:
            data.extend(n.split("\t"))
    expression_name, *arguments = filter(bool, data)
    try:
        decoder = mmml_converters.constants.DECODER_REGISTRY[expression_name]
    except KeyError:
        raise mmml_utilities.NoDecoderExists(expression_name)
    return decoder(*arguments)
