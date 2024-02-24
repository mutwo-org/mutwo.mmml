import typing

import chevron

from mutwo import core_converters
from mutwo import core_events
from mutwo import mmml_converters
from mutwo import mmml_utilities

__all__ = ("MMMLExpressionToEvent", "MMMLExpression")


MMMLExpression: typing.TypeAlias = str
ExpressionName: typing.TypeAlias = str
HeaderArguments: typing.TypeAlias = tuple[typing.Any, ...]


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
    TaggedSequentialEvent([NoteLike(duration = DirectDuration(duration = 1/4), instrument_list = [], lyric = DirectLyric(phonetic_representation = ), pitch_list = [WesternPitch('c', 4)], tempo_envelope = TempoEnvelope([TempoEvent(curve_shape = 0, duration = DirectDuration(duration = 1), tempo_point = DirectTempoPoint(BPM = 60, reference = 1)), TempoEvent(curve_shape = 0, duration = DirectDuration(duration = 0), tempo_point = DirectTempoPoint(BPM = 60, reference = 1))]), volume = WesternVolume(amplitude = 0.12328467394420653)), NoteLike(duration = DirectDuration(duration = 1/8), instrument_list = [], lyric = DirectLyric(phonetic_representation = ), pitch_list = [WesternPitch('d', 4)], tempo_envelope = TempoEnvelope([TempoEvent(curve_shape = 0, duration = DirectDuration(duration = 1), tempo_point = DirectTempoPoint(BPM = 60, reference = 1)), TempoEvent(curve_shape = 0, duration = DirectDuration(duration = 0), tempo_point = DirectTempoPoint(BPM = 60, reference = 1))]), volume = WesternVolume(amplitude = 0.28480358684358004)), NoteLike(duration = DirectDuration(duration = 1/8), instrument_list = [], lyric = DirectLyric(phonetic_representation = ), pitch_list = [WesternPitch('e', 4)], tempo_envelope = TempoEnvelope([TempoEvent(curve_shape = 0, duration = DirectDuration(duration = 1), tempo_point = DirectTempoPoint(BPM = 60, reference = 1)), TempoEvent(curve_shape = 0, duration = DirectDuration(duration = 0), tempo_point = DirectTempoPoint(BPM = 60, reference = 1))]), volume = WesternVolume(amplitude = 0.28480358684358004)), NoteLike(duration = DirectDuration(duration = 1/2), instrument_list = [], lyric = DirectLyric(phonetic_representation = ), pitch_list = [WesternPitch('d', 4)], tempo_envelope = TempoEnvelope([TempoEvent(curve_shape = 0, duration = DirectDuration(duration = 1), tempo_point = DirectTempoPoint(BPM = 60, reference = 1)), TempoEvent(curve_shape = 0, duration = DirectDuration(duration = 0), tempo_point = DirectTempoPoint(BPM = 60, reference = 1))]), volume = WesternVolume(amplitude = 0.28480358684358004))])
    """

    def __init__(self):
        self._wrapped_decoder_dict = {}
        self.__decoder_default_dict = {}

    def reset_defaults(self):
        self.__decoder_default_dict = {}

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
        NoteLike(duration = DirectDuration(duration = 1/2), instrument_list = [], lyric = DirectLyric(phonetic_representation = ), pitch_list = [WesternPitch('c', 4)], tempo_envelope = TempoEnvelope([TempoEvent(curve_shape = 0, duration = DirectDuration(duration = 1), tempo_point = DirectTempoPoint(BPM = 60, reference = 1)), TempoEvent(curve_shape = 0, duration = DirectDuration(duration = 0), tempo_point = DirectTempoPoint(BPM = 60, reference = 1))]), volume = WesternVolume(amplitude = 0.12328467394420653))
        """
        e = chevron.render(expression, dict(**kwargs))
        return self._process_expression(e)

    def _process_expression(self, expression: str) -> core_events.abc.Event:
        header, block = _split_to_header_and_block(expression)
        expression_name, arguments = self._process_header(header)
        event_tuple = self._process_block(block)
        try:
            wrapped_decoder = self._wrapped_decoder_dict[expression_name]
        except KeyError:
            try:
                decoder = mmml_converters.constants.DECODER_REGISTRY[expression_name]
            except KeyError:
                raise mmml_utilities.NoDecoderExists(expression_name)
            self._wrapped_decoder_dict[
                expression_name
            ] = wrapped_decoder = self._wrap_decoder(expression_name, decoder)
        return wrapped_decoder(event_tuple, *arguments)

    def _process_header(self, header: str) -> tuple[ExpressionName, HeaderArguments]:
        data = []
        for n in header.split(" "):
            if n:
                data.extend(n.split("\t"))
        expression_name, *arguments = filter(bool, data)
        return expression_name, arguments

    def _process_block(self, block: str) -> tuple[core_events.abc.Event, ...]:
        expression_tuple = _split_to_expression_tuple(block)
        return tuple(self._process_expression(e) for e in expression_tuple)

    def _wrap_decoder(self, decoder_name: str, function: typing.Callable):
        """Wrap decoder so that it uses the previously used values for its args

        With the help of wrapping in the following MMML expression the second
        note also has a volume of 'fff':

            seq
                n 1/1 c fff
                {{! The following note also has 'fff', because }}
                {{! the previous NoteLike set it as its default. }}
                n 1/1 c
        """

        def _(*args):
            self._set_decoder_default_args(decoder_name, args)
            args = self._get_decoder_default_args(decoder_name, args)
            return function(*args)

        return _

    def _set_decoder_default_args(self, decoder_name: str, args: tuple):
        """Set currently defined arguments as new default values for decoder"""
        present_default = self.__decoder_default_dict.get(decoder_name, [])
        if len(args) > len(present_default):
            default = list(args)
        else:
            default = present_default
            for i, v in enumerate(args):
                default[i] = v
        self.__decoder_default_dict[decoder_name] = default

    def _get_decoder_default_args(self, decoder_name: str, args: tuple):
        """Add previously used arguments for decoder to argument list"""
        arg_list = list(args)
        arg_count = len(arg_list)
        present_default = self.__decoder_default_dict[decoder_name]
        diff = len(present_default) - arg_count
        for i in range(diff):
            arg_list.append(present_default[arg_count + i])
        return tuple(arg_list)


def _split_to_header_and_block(expression: str):
    header, block = None, expression
    while not header:
        if not block:
            raise mmml_utilities.MalformedMMML("No MMML expression found")
        header, _, block = block.partition("\n")
    return header, block


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
