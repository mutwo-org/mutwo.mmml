"""Module for converting MMML text to Mutwo objects.

MMML is an abbreviation for 'Mutwos Music Markup Language'.
Similarly to `Music Macro Language <https://en.wikipedia.org/wiki/Music_Macro_Language>`_
it is intended to be a easy human readable and writeable plain text encoding
for musical data. The language is inspired by Lilypond, ABC Notation, Guido and Alda.
It differs from the former insofar as that the render engine (frontend) is
unspecified. Furthermore MMML is quite open to different notation specifications for
pitch, volumes and rhythm as long as predefined identifier aren't overridden.

**Example:**

c:0`8 e`4 d`2*ff
r`4 f*p<articulation.name="stacatto"> gs a`1*mf
e`2<tie=True> e`16 :before [ f`8 d`16<glissando=True> ] c`3/4 :after [ f`16 ]
"""

import ast
import configparser
import inspect
import importlib
import io
import typing
import warnings

try:
    import quicktions as fractions  # type: ignore
except ImportError:
    import fractions  # type: ignore

from mutwo import core_converters
from mutwo import core_events
from mutwo import mmml_converters
from mutwo import music_events
from mutwo import music_parameters

___all___ = (
    "MMMLItemsConverter",
    "MMMLSinglePitchConverter",
    "MMMLSingleJIPitchConverter",
    "MMMLPitchesConverter",
    "MMMLSingleRhythmConverter",
    "MMMLRhythmsConverter",
    "MMMLSingleVolumeConverter",
    "MMMLSingleWesternVolumeConverter",
    "MMMLVolumesConverter",
    "MMMLSingleAttributeConverter",
    "MMMLEventsConverter",
    "MMMLConverter",
)


class MMMLItemsConverter(core_converters.abc.Converter):
    """Convert one or multiple MMML items to mutwo objects."""

    def __init__(
        self,
        mmml_single_item_converter: core_converters.abc.Converter,
        default_value: typing.Any,
        default_attribute_tuple: tuple[typing.Any, ...],
    ):
        self._mmml_single_item_converter = mmml_single_item_converter
        self._default_value = default_value
        self._default_attribute_tuple = default_attribute_tuple

    def _convert_mmml_item_to_mutwo_item(
        self,
        mmml_item_to_convert: str,
        previous_attribute_tuple: tuple[typing.Any, ...],
    ) -> tuple[tuple[music_parameters.abc.Pitch, ...], tuple[typing.Any, ...]]:
        return (
            self._mmml_single_item_converter.convert(mmml_item_to_convert),
            previous_attribute_tuple,
        )

    def convert(
        self,
        mmml_items_to_convert: typing.Union[str, typing.Sequence[typing.Optional[str]]],
    ) -> tuple[tuple[music_parameters.abc.Pitch, ...], ...]:
        previous_item = self._default_value
        previous_attribute_tuple = self._default_attribute_tuple

        mmml_items_to_iterate = (
            mmml_items_to_convert.split(mmml_converters.configurations.EVENT_IDENTIFIER)
            if hasattr(mmml_items_to_convert, "split")
            else mmml_items_to_convert
        )

        converted_item_list = []
        for mmml_item_to_convert in mmml_items_to_iterate:
            if mmml_item_to_convert:
                (
                    converted_item,
                    previous_attribute_tuple,
                ) = self._convert_mmml_item_to_mutwo_item(
                    mmml_item_to_convert, previous_attribute_tuple
                )
                previous_item = converted_item
            else:
                converted_item = previous_item
            converted_item_list.append(converted_item)
        return tuple(converted_item_list)


class MMMLSinglePitchConverter(core_converters.abc.Converter):
    """Convert a single MMML pitch string to a mutwo pitch object."""

    def __init__(
        self,
        decodex_or_decodex_function: typing.Union[
            dict[str, music_parameters.abc.Pitch],
            typing.Callable[[str], music_parameters.abc.Pitch],
        ],
        octave_mark_processor: typing.Callable[
            [music_parameters.abc.Pitch, typing.Optional[str]],
            music_parameters.abc.Pitch,
        ] = lambda pitch, _: pitch,
    ):
        self._decodex_or_decodex_function = decodex_or_decodex_function
        self._octave_mark_processor = octave_mark_processor

    def convert(
        self, mmml_pitch_to_convert: str
    ) -> typing.Optional[music_parameters.abc.Pitch]:
        mmml_pitch_class, *mmml_octave_mark = mmml_pitch_to_convert.split(
            mmml_converters.configurations.OCTAVE_IDENTIFIER
        )

        if mmml_pitch_class == mmml_converters.configurations.REST_IDENTIFIER:
            return None

        if mmml_octave_mark:
            mmml_octave_mark = mmml_octave_mark[0]

        if hasattr(self._decodex_or_decodex_function, "__call__"):
            mutwo_pitch = self._decodex_or_decodex_function(mmml_pitch_class)
        else:
            mutwo_pitch = self._decodex_or_decodex_function[mmml_pitch_class]

        mutwo_pitch = self._octave_mark_processor(mutwo_pitch, mmml_octave_mark)
        return mutwo_pitch


class MMMLSingleJIPitchConverter(MMMLSinglePitchConverter):
    def __init__(self):
        super().__init__(self._decodex_function, self._octave_mark_processor)

    @staticmethod
    def _get_and_add_prime_and_exponent_pair(
        prime_to_exponent: dict[int, int],
        element: str,
        current_base: str,
        current_exponent: int,
    ) -> tuple[str, int]:
        base = int(current_base)
        if base in prime_to_exponent:
            message = f"Found duplicate base {base}!"
            raise ValueError(message)
        prime_to_exponent.update({base: current_exponent})
        current_base = element
        current_exponent = 0
        is_separating = False
        return current_base, current_exponent, is_separating

    @staticmethod
    def _split_to_prime_and_exponent_pairs(
        mmml_pitch_class_to_convert: str,
    ) -> tuple[str, ...]:
        is_separating = False
        current_base = ""
        current_exponent = 0
        prime_to_exponent = {}
        for element in mmml_pitch_class_to_convert:
            if element.isdigit():
                if is_separating:
                    (
                        current_base,
                        current_exponent,
                        is_separating,
                    ) = MMMLSingleJIPitchConverter._get_and_add_prime_and_exponent_pair(
                        prime_to_exponent, element, current_base, current_exponent
                    )
                else:
                    current_base += element
            elif (
                element
                == mmml_converters.configurations.JUST_INTONATION_POSITIVE_EXPONENT_IDENTIFIER
            ):
                is_separating = True
                current_exponent += 1
            elif (
                element
                == mmml_converters.configurations.JUST_INTONATION_NEGATIVE_EXPONENT_IDENTIFIER
            ):
                is_separating = True
                current_exponent -= 1
            else:
                message = (
                    f"Found undefined sign {element} in {mmml_pitch_class_to_convert}!"
                )
                raise NotImplementedError(message)

        if is_separating:
            (
                current_base,
                current_exponent,
                is_separating,
            ) = MMMLSingleJIPitchConverter._get_and_add_prime_and_exponent_pair(
                prime_to_exponent, element, current_base, current_exponent
            )

        return prime_to_exponent

    @staticmethod
    def _decodex_function(
        mmml_pitch_class_to_convert: str,
    ) -> music_parameters.JustIntonationPitch:
        prime_to_exponent = (
            MMMLSingleJIPitchConverter._split_to_prime_and_exponent_pairs(
                mmml_pitch_class_to_convert
            )
        )
        numerator = 1
        denominator = 1

        for prime, exponent in prime_to_exponent.items():
            multiplied = prime ** abs(exponent)
            if exponent > 0:
                numerator *= multiplied
            else:
                denominator *= multiplied

        pitch = music_parameters.JustIntonationPitch(f"{numerator}/{denominator}")
        return pitch

    @staticmethod
    def _octave_mark_processor(
        just_intonation_pitch: music_parameters.JustIntonationPitch,
        mmml_octave_mark_to_apply: typing.Optional[str],
    ) -> music_parameters.JustIntonationPitch:
        if mmml_octave_mark_to_apply:
            octave = int(mmml_octave_mark_to_apply)
        else:
            octave = 0
        just_intonation_pitch.register(octave)
        return just_intonation_pitch


class MMMLSingleJIScalePitchConverter(MMMLSinglePitchConverter):
    def __init__(self, ratio_string: str):
        scale = tuple(
            music_parameters.JustIntonationPitch(ratio)
            for ratio in ratio_string.split(" ")
        )
        decodex = {str(number + 1): pitch for number, pitch in enumerate(sorted(scale))}
        super().__init__(decodex, self._octave_mark_processor)

    @staticmethod
    def _octave_mark_processor(
        just_intonation_pitch: music_parameters.JustIntonationPitch,
        mmml_octave_mark_to_apply: typing.Optional[str],
    ) -> music_parameters.JustIntonationPitch:
        if mmml_octave_mark_to_apply:
            octave = int(mmml_octave_mark_to_apply)
        else:
            octave = 0
        return just_intonation_pitch.add(
            music_parameters.JustIntonationPitch("1/1").register(octave), mutate=False
        )


class MMMLSingleDiatonicPitchConverter(MMMLSingleJIScalePitchConverter):
    def __init__(self):
        super().__init__(ratio_string="1/1 9/8 7/6 4/3 3/2 8/5 7/4")


class MMMLSingleChromaticPitchConverter(MMMLSingleJIScalePitchConverter):
    def __init__(
        self,
    ):
        super().__init__(
            ratio_string="1/1 16/15 9/8 7/6 5/4 4/3 7/5 3/2 8/5 5/3 7/4 15/8"
        )


class MMMLPitchesConverter(MMMLItemsConverter):
    """Convert one or multiple MMML pitches to mutwo pitch objects."""

    def __init__(
        self,
        mmml_single_pitch_converter: MMMLSinglePitchConverter = MMMLSinglePitchConverter(
            lambda frequency: music_parameters.DirectPitch(float(frequency)),
            lambda pitch, octave: music_parameters.DirectPitch(
                pitch.frequency * (2 ** int(octave))
            )
            if octave
            else pitch,
        ),
        default_pitch: music_parameters.abc.Pitch = music_parameters.DirectPitch(440),
        default_octave_mark: str = "0",
    ):
        super().__init__(
            mmml_single_pitch_converter, (default_pitch,), (default_octave_mark,)
        )

    @staticmethod
    def _get_octave_mark(mmml_pitch: str) -> typing.Optional[str]:
        _, *mmml_octave_mark = mmml_pitch.split(
            mmml_converters.configurations.OCTAVE_IDENTIFIER
        )
        if mmml_octave_mark:
            return mmml_octave_mark[0]
        return None

    def _convert_mmml_item_to_mutwo_item(
        self,
        mmml_pitch_or_pitch_to_convert_list: str,
        previous_attribute_tuple: tuple[typing.Any, ...],
    ) -> tuple[tuple[music_parameters.abc.Pitch, ...], tuple[typing.Any, ...]]:
        previous_octave_mark, *_ = previous_attribute_tuple
        converted_chord = []
        for mmml_pitch_to_convert in mmml_pitch_or_pitch_to_convert_list.split(
            mmml_converters.configurations.MULTIPLE_PITCHES_IDENTIFIER
        ):
            current_octave_mark = self._get_octave_mark(mmml_pitch_to_convert)
            if current_octave_mark:
                previous_octave_mark = current_octave_mark
            else:
                mmml_pitch_to_convert = (
                    f"{mmml_pitch_to_convert}:{previous_octave_mark}"
                )
            converted_pitch = self._mmml_single_item_converter.convert(
                mmml_pitch_to_convert
            )
            if converted_pitch:
                converted_chord.append(converted_pitch)
        converted_chord = tuple(converted_chord)
        return converted_chord, (previous_octave_mark,)


class MMMLSingleRhythmConverter(core_converters.abc.Converter):
    """Convert a single MMML rhythm string to a Python Fraction object."""

    def convert(self, mmml_rhythm_to_convert: str) -> fractions.Fraction:
        if "/" in mmml_rhythm_to_convert:
            rhythm = fractions.Fraction(mmml_rhythm_to_convert)
        else:
            rhythm = fractions.Fraction(1, int(mmml_rhythm_to_convert))
        return rhythm


class MMMLRhythmsConverter(MMMLItemsConverter):
    """Convert one or multiple MMML rhythms to Python Fraction objects."""

    def __init__(
        self,
        mmml_single_rhythm_converter: MMMLSingleRhythmConverter = MMMLSingleRhythmConverter(),
        default_rhythm=fractions.Fraction(1, 4),
    ):
        super().__init__(mmml_single_rhythm_converter, default_rhythm, tuple([]))


class MMMLSingleVolumeConverter(core_converters.abc.Converter):
    """Convert a single MMML volume string to a mutwo volume object."""

    def __init__(
        self,
        decodex_or_decodex_function: typing.Union[
            dict[str, music_parameters.abc.Pitch],
            typing.Callable[[str], music_parameters.abc.Pitch],
        ],
    ):
        self._decodex_or_decodex_function = decodex_or_decodex_function

    def convert(self, mmml_volume_to_convert: str) -> music_parameters.abc.Volume:
        if hasattr(self._decodex_or_decodex_function, "__call__"):
            mutwo_volume = self._decodex_or_decodex_function(mmml_volume_to_convert)
        else:
            mutwo_volume = self._decodex_or_decodex_function[mmml_volume_to_convert]

        return mutwo_volume


class MMMLSingleWesternVolumeConverter(MMMLSingleVolumeConverter):
    def __init__(self):
        super().__init__(
            {
                dynamic_indicator: music_parameters.WesternVolume(dynamic_indicator)
                for dynamic_indicator in music_parameters.constants.DYNAMIC_INDICATOR_TUPLE
            }
        )


class MMMLVolumesConverter(MMMLItemsConverter):
    """Convert one or multiple MMML volumes to mutwo volume objects."""

    def __init__(
        self,
        mmml_single_volume_converter: MMMLSingleVolumeConverter = MMMLSingleWesternVolumeConverter(),
        default_volume=music_parameters.WesternVolume("mf"),
    ):
        super().__init__(mmml_single_volume_converter, default_volume, tuple([]))


def _find_allowed_name_dict() -> dict:
    def _iterate_module(module_name: str):
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            return {}
        try:
            module_dir = module.__all__
        except AttributeError:
            module_dir = dir(module)
        module_dict = module.__dict__
        class_name_to_class = {}
        for module_or_class_or_different_object_name in module_dir:
            if module_or_class_or_different_object_name[:2] != "__":
                module_or_class_or_different_object = module_dict[
                    module_or_class_or_different_object_name
                ]
                if inspect.ismodule(module_or_class_or_different_object):
                    class_name_to_class.update(
                        _iterate_module(
                            f"{module_name}.{module_or_class_or_different_object_name}"
                        )
                    )
                elif isinstance(
                    module_or_class_or_different_object, (type, typing.Callable)
                ):
                    class_name_to_class.update(
                        {
                            module_or_class_or_different_object_name: module_or_class_or_different_object
                        }
                    )
        return class_name_to_class

    _allowed_name_dict = {}
    for module_name in (
        "mutwo.core_events",
        "mutwo.core_parameters",
        "mutwo.music_events",
        "mutwo.music_parameters",
    ):
        _allowed_name_dict.update(_iterate_module(module_name))
    return _allowed_name_dict


class MMMLSingleAttributeConverter(core_converters.abc.Converter):
    """Convert a single MMML attribute to a function which can be applied on a :class:`~mutwo.music_events.NoteLike`."""

    _allowed_name_dict = _find_allowed_name_dict()

    @staticmethod
    def _evaluate_expression(input_string: str) -> typing.Any:
        """Custom secure eval method which provides mutwo classes."""
        code = compile(input_string, "<string>", "eval")
        for name in code.co_names:
            if name not in MMMLSingleAttributeConverter._allowed_name_dict:
                raise NameError(f"Use of {name} not allowed")
        return eval(
            code, {"__builtins__": {}}, MMMLSingleAttributeConverter._allowed_name_dict
        )

    def convert(
        self, mmml_attribute_to_convert: str
    ) -> typing.Callable[[music_events.NoteLike], None]:
        try:
            assert (
                mmml_attribute_to_convert[-1]
                == mmml_converters.configurations.ATTRIBUTE_END_IDENTIFIER
            )
        except AssertionError:
            message = f"Found malformated attribute tag '{mmml_attribute_to_convert}' "
            message += "which isn't closed with the expected end identifier "
            message += f"{mmml_converters.configurations.ATTRIBUTE_END_IDENTIFIER}'!"
            raise ValueError(message)

        def apply_attributes(note_like: music_events.NoteLike):
            for attribute_to_apply in mmml_attribute_to_convert[:-1].split(
                mmml_converters.configurations.MULTIPLE_ATTRIBUTES_IDENTIFIER
            ):
                try:
                    attribute_names, attribute_value = attribute_to_apply.split(
                        mmml_converters.configurations.ATTRIBUTE_DEFINITION_IDENTIFIER
                    )
                except ValueError:
                    message = (
                        f"Found invalid attribute definition: '{attribute_to_apply}'!"
                    )
                    message += " Did you forget to put the seperator '"
                    message += (
                        mmml_converters.configurations.MULTIPLE_ATTRIBUTES_IDENTIFIER
                    )
                    message += "' between two or more attribute definitions?"
                    message += " Did you forget the attribute name on the left side "
                    message += (
                        "of the definition? Did you forget the attribue argument "
                    )
                    message += "on the right side of the definition?"
                    raise ValueError(message)
                # Remove white space from attribute names
                attribute_names = "".join(
                    filter(lambda character: character != " ", attribute_names)
                )
                # Remove leading white space from attribute itself
                attribute_value = attribute_value.lstrip()
                attribute_name_list = attribute_names.split(".")
                if attribute_name_list[0] in dir(
                    note_like.playing_indicator_collection
                ):
                    indicator_collection = note_like.playing_indicator_collection
                elif attribute_name_list[0] in dir(
                    note_like.notation_indicator_collection
                ):
                    indicator_collection = note_like.notation_indicator_collection
                else:
                    message = f"Found unknown attribute '{attribute_names}' with "
                    message += f"argument '{attribute_value}'."
                    warnings.warn(message)
                    indicator_collection = None
                if indicator_collection:
                    item = indicator_collection
                    for attribute_name in attribute_name_list[:-1]:
                        item = getattr(item, attribute_name)
                    parsed_attribute_value = (
                        MMMLSingleAttributeConverter._evaluate_expression(
                            attribute_value
                        )
                    )
                    setattr(item, attribute_name_list[-1], parsed_attribute_value)

        return apply_attributes


class MMMLAttributesConverter(MMMLItemsConverter):
    """Convert one or multiple MMML volumes to mutwo volume objects."""

    def __init__(
        self,
        mmml_single_attribute_converter: MMMLSingleAttributeConverter = MMMLSingleAttributeConverter(),
    ):
        super().__init__(
            mmml_single_attribute_converter, lambda note_like: None, tuple([])
        )


class MMMLEventsConverter(core_converters.abc.Converter):
    def __init__(
        self,
        mmml_pitches_converter: MMMLPitchesConverter = MMMLPitchesConverter(),
        mmml_rhythms_converter: MMMLRhythmsConverter = MMMLRhythmsConverter(),
        mmml_volumes_converter: MMMLVolumesConverter = MMMLVolumesConverter(),
        mmml_attributes_converter: MMMLAttributesConverter = MMMLAttributesConverter(),
    ):
        self._mmml_pitches_converter = mmml_pitches_converter
        self._mmml_rhythms_converter = mmml_rhythms_converter
        self._mmml_volumes_converter = mmml_volumes_converter
        self._mmml_attributes_converter = mmml_attributes_converter

    def _apply_identifier_list(
        self, mmml_event_to_convert: str, value_dict: dict, position_dict: dict
    ):
        for name, identifier in (
            ("volume", mmml_converters.configurations.DYNAMIC_IDENTIFIER),
            ("duration", mmml_converters.configurations.RHYTHM_IDENTIFIER),
            ("attribute", mmml_converters.configurations.ATTRIBUTE_START_IDENTIFIER),
        ):
            try:
                position = mmml_event_to_convert.index(identifier)
            except ValueError:
                value = None
                position = float("-inf")
                value_dict.update({name: value})
            finally:
                position_dict.update({name: position})

    def _find_pitch_value(
        self, mmml_event_to_convert: str, positive_position_tuple: tuple[int, ...]
    ) -> typing.Optional[str]:
        # Pitch has to be in the first position, because it doesn't
        # have any identifier string
        if 0 not in positive_position_tuple:
            return mmml_event_to_convert[0 : positive_position_tuple[0]]
        else:
            return None

    def _find_attribute_with_identifier_value_dict(
        self,
        mmml_event_to_convert: str,
        position_dict: dict[str, float],
        positive_position_tuple: tuple[int, ...],
    ) -> dict[str, str]:
        value_dict = {}
        for name, position in position_dict.items():
            if position > 0:
                index = positive_position_tuple.index(position)
                value = mmml_event_to_convert[
                    position + 1 : positive_position_tuple[index + 1]
                ]
                value_dict.update({name: value})
        return value_dict

    def _convert_mmml_event(
        self,
        mmml_event_to_convert: str,
        pitch_to_convert_list: list[str],
        duration_to_convert_list: list[str],
        volume_to_convert_list: list[str],
        attribute_to_convert_list: list[str],
    ):
        value_dict = {}
        position_dict = {}

        self._apply_identifier_list(mmml_event_to_convert, value_dict, position_dict)

        position_list = sorted(
            tuple(position_dict.values()) + (len(mmml_event_to_convert),),
        )
        positive_position_tuple = tuple(
            position for position in position_list if position >= 0
        )

        value_dict.update(
            {
                "pitch": self._find_pitch_value(
                    mmml_event_to_convert, positive_position_tuple
                )
            }
        )
        value_dict.update(
            self._find_attribute_with_identifier_value_dict(
                mmml_event_to_convert, position_dict, positive_position_tuple
            )
        )

        for name, attribute_to_convert_list in (
            ("pitch", pitch_to_convert_list),
            ("volume", volume_to_convert_list),
            ("duration", duration_to_convert_list),
            ("attribute", attribute_to_convert_list),
        ):
            attribute_to_convert_list.append(value_dict[name])

    def _build_note_like_sequential_event(
        self,
        pitch_to_convert_list: list[str],
        duration_to_convert_list: list[str],
        volume_to_convert_list: list[str],
        attribute_to_convert_list: list[str],
        grace_note_list_list: list[core_events.SequentialEvent],
        after_grace_note_list_list: list[core_events.SequentialEvent],
    ) -> core_events.SequentialEvent[music_events.NoteLike]:
        converted_pitch_tuple = self._mmml_pitches_converter.convert(
            pitch_to_convert_list
        )
        converted_duration_tuple = self._mmml_rhythms_converter.convert(
            duration_to_convert_list
        )
        converted_volume_tuple = self._mmml_volumes_converter.convert(
            volume_to_convert_list
        )
        converted_attribute_tuple = self._mmml_attributes_converter.convert(
            attribute_to_convert_list
        )

        converted_event_sequential_event = core_events.SequentialEvent([])
        for (
            pitches,
            rhythm,
            volume,
            attribute_function,
            grace_note_sequential_event,
            after_grace_note_sequential_event,
        ) in zip(
            converted_pitch_tuple,
            converted_duration_tuple,
            converted_volume_tuple,
            converted_attribute_tuple,
            grace_note_list_list,
            after_grace_note_list_list,
        ):
            note_like = music_events.NoteLike(
                pitches,
                rhythm,
                volume,
                grace_note_sequential_event=grace_note_sequential_event,
                after_grace_note_sequential_event=after_grace_note_sequential_event,
            )
            attribute_function(note_like)
            converted_event_sequential_event.append(note_like)

        return converted_event_sequential_event

    def convert(
        self, mmml_events_to_convert: str
    ) -> core_events.SequentialEvent[music_events.NoteLike]:
        split_lines = map(
            lambda line_with_whitespace: line_with_whitespace.lstrip(),
            mmml_events_to_convert.split("\n"),
        )
        mmml_lines_to_convert = " ".join(
            map(
                lambda line: line[
                    : line.index(mmml_converters.configurations.COMMENT_IDENTIFIER)
                ]
                if mmml_converters.configurations.COMMENT_IDENTIFIER in line
                else line,
                filter(
                    lambda line: line
                    and line[0] != mmml_converters.configurations.COMMENT_IDENTIFIER,
                    split_lines,
                ),
            )
        )
        mmml_event_or_grace_note_to_convert_iterator = iter(
            filter(
                lambda item: bool(item),
                mmml_lines_to_convert.split(
                    mmml_converters.configurations.EVENT_IDENTIFIER
                ),
            )
        )
        pitch_to_convert_list = []
        duration_to_convert_list = []
        volume_to_convert_list = []
        attribute_to_convert_list = []
        grace_note_list_list = []
        after_grace_note_list_list = []

        def test_note_lists():
            for note_list in (grace_note_list_list, after_grace_note_list_list):
                if len(pitch_to_convert_list) > len(note_list):
                    note_list.append(core_events.SequentialEvent([]))

        while True:
            try:
                mmml_event_or_grace_note_to_convert = next(
                    mmml_event_or_grace_note_to_convert_iterator
                )
            except StopIteration:
                break
            if mmml_event_or_grace_note_to_convert:
                is_grace_note_list, is_after_grace_note_list = False, False
                if (
                    mmml_event_or_grace_note_to_convert[
                        : len(
                            mmml_converters.configurations.BEFORE_GRACE_NOTE_LIST_IDENTIFIER
                        )
                    ]
                    == mmml_converters.configurations.BEFORE_GRACE_NOTE_LIST_IDENTIFIER
                ):
                    is_grace_note_list = True
                elif (
                    mmml_event_or_grace_note_to_convert[
                        : len(
                            mmml_converters.configurations.AFTER_GRACE_NOTE_LIST_IDENTIFIER
                        )
                    ]
                    == mmml_converters.configurations.AFTER_GRACE_NOTE_LIST_IDENTIFIER
                ):
                    is_after_grace_note_list = True

                if not is_grace_note_list and not is_after_grace_note_list:
                    if pitch_to_convert_list:
                        test_note_lists()

                    self._convert_mmml_event(
                        mmml_event_or_grace_note_to_convert,
                        pitch_to_convert_list,
                        duration_to_convert_list,
                        volume_to_convert_list,
                        attribute_to_convert_list,
                    )
                else:
                    grace_note_event_to_convert_list = []
                    start_grace_note_identifier = next(
                        mmml_event_or_grace_note_to_convert_iterator
                    )
                    try:
                        assert (
                            start_grace_note_identifier
                            == mmml_converters.configurations.GRACE_NOTE_LIST_START_IDENTIFIER
                        )
                    except AssertionError:
                        message = f"Found '{start_grace_note_identifier}' instead of start grace "
                        message += f"note list identifier '{mmml_converters.configurations.GRACE_NOTE_LIST_START_IDENTIFIER}'"
                        message += f"after grace note identifier '{mmml_event_or_grace_note_to_convert}'!"
                        raise ValueError(message)

                    while True:
                        grace_note_event_or_stop_identifier = next(
                            mmml_event_or_grace_note_to_convert_iterator
                        )
                        if (
                            grace_note_event_or_stop_identifier
                            == mmml_converters.configurations.GRACE_NOTE_LIST_END_IDENTIFIER
                        ):
                            break
                        else:
                            grace_note_event_to_convert_list.append(
                                grace_note_event_or_stop_identifier
                            )

                    grace_note_list_as_mmml_event = " ".join(
                        grace_note_event_to_convert_list
                    )
                    note_like_sequential_event = self.convert(
                        grace_note_list_as_mmml_event
                    )
                    if is_after_grace_note_list:
                        after_grace_note_list_list.append(note_like_sequential_event)
                    else:
                        grace_note_list_list.append(note_like_sequential_event)

        test_note_lists()
        return self._build_note_like_sequential_event(
            pitch_to_convert_list,
            duration_to_convert_list,
            volume_to_convert_list,
            attribute_to_convert_list,
            grace_note_list_list,
            after_grace_note_list_list,
        )


class MMMLConverter(core_converters.abc.Converter):
    def __init__(
        self, mmml_events_converter: MMMLEventsConverter = MMMLEventsConverter()
    ):
        self._mmml_events_converter = mmml_events_converter

    def convert(
        self, mmml_to_convert: str
    ) -> dict[str, core_events.SequentialEvent[music_events.NoteLike]]:
        if mmml_converters.configurations.VARIABLE_IDENTIFIER in mmml_to_convert:
            parts = {}
            for variable_data in mmml_to_convert.split(
                mmml_converters.configurations.VARIABLE_IDENTIFIER
            ):
                if variable_data and variable_data != "\n":
                    variable_name, events = variable_data.split("\n", 1)
                    parts.update(
                        {variable_name: self._mmml_events_converter.convert(events)}
                    )
            return parts

        else:
            return {"undefined": self._mmml_events_converter.convert(mmml_to_convert)}


class IniFileToMMMLConverter(core_converters.abc.Converter):
    """Convert .ini file to a :class:`MMMLConverter`.

    Default and example ini File:

        [mmml]
        pitch-class = MMMLSingleJIPitchConverter
        rhythm-class = MMMLSingleRhythmConverter
        volume-class = MMMLSingleWesternVolumeConverter
        attribute-class = MMMLSingleAttributeConverter

    If a class has __init__ attributes they can be specified
    by "TYPE-kwargs" (for instance "pitch-kwargs = {...}")
    """

    mmml_section_name = "mmml"

    def convert(
        self, ini_file_path_or_string: str, is_string: bool = False
    ) -> MMMLConverter:
        if is_string:
            config = configparser.ConfigParser(allow_no_value=True)
            config.readfp(io.StringIO(ini_file_path_or_string))
        else:
            config = configparser.ConfigParser()
            config.read(ini_file_path_or_string)
        try:
            section = config[self.mmml_section_name]
        except KeyError:
            section = None
        keyword_arguments = {}
        if section:
            for attribute_name, items_class, keyword in (
                ("pitch", MMMLPitchesConverter, "mmml_pitches_converter"),
                ("rhythm", MMMLRhythmsConverter, "mmml_rhythms_converter"),
                ("volume", MMMLVolumesConverter, "mmml_volumes_converter"),
                ("attribute", MMMLAttributesConverter, "mmml_attributes_converter"),
            ):
                try:
                    class_name = section[f"{attribute_name}-class"]
                except KeyError:
                    pass
                else:
                    class_ = globals()[class_name]
                    try:
                        kwargs = ast.literal_eval(section[f"{attribute_name}-kwargs"])
                    except KeyError:
                        kwargs = {}
                    keyword_arguments.update({keyword: items_class(class_(**kwargs))})

        mmml_events_converter = MMMLEventsConverter(**keyword_arguments)
        return MMMLConverter(mmml_events_converter)
