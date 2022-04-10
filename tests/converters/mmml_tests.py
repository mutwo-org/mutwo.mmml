import fractions
import unittest

from mutwo import core_events
from mutwo import mmml_converters
from mutwo import music_events
from mutwo import music_parameters


class MMMLSinglePitchConverterTest(unittest.TestCase):
    def test_convert_via_decodex_dict(self):
        def octave_mark_processor(
            converted_pitch: music_parameters.WesternPitch, octave_mark: str
        ) -> music_parameters.WesternPitch:
            if octave_mark:
                converted_pitch.octave = int(octave_mark)
            return converted_pitch

        decodex_dict = {
            pitch_class: music_parameters.WesternPitch(pitch_class)
            for pitch_class in "c d e f g a b".split(" ")
        }
        converter = mmml_converters.MMMLSinglePitchConverter(
            decodex_dict, octave_mark_processor
        )

        self.assertEqual(
            converter.convert("d"),
            music_parameters.WesternPitch("d", 4),
        )
        self.assertEqual(
            converter.convert("c:5"),
            music_parameters.WesternPitch("c", 5),
        )
        self.assertEqual(
            converter.convert("b:3"),
            music_parameters.WesternPitch("b", 3),
        )
        self.assertEqual(
            converter.convert("f"),
            music_parameters.WesternPitch("f", 4),
        )
        self.assertEqual(
            converter.convert(mmml_converters.configurations.REST_IDENTIFIER),
            None,
        )

    def test_convert_via_decodex_function(self):
        def decodex_function(
            mmml_pitch_class_to_convert: str,
        ) -> music_parameters.DirectPitch:
            frequency = float(mmml_pitch_class_to_convert)
            return music_parameters.DirectPitch(frequency)

        def octave_mark_processor(
            converted_pitch: music_parameters.DirectPitch, octave_mark: str
        ) -> music_parameters.DirectPitch:
            if octave_mark:
                converted_pitch = music_parameters.DirectPitch(
                    converted_pitch.frequency * (2 ** int(octave_mark))
                )
            return converted_pitch

        converter = mmml_converters.MMMLSinglePitchConverter(
            decodex_function, octave_mark_processor
        )
        self.assertEqual(
            converter.convert("200"),
            music_parameters.DirectPitch(200),
        )
        self.assertEqual(
            converter.convert("300:1"),
            music_parameters.DirectPitch(600),
        )
        self.assertEqual(
            converter.convert("400.5"),
            music_parameters.DirectPitch(400.5),
        )
        self.assertEqual(
            converter.convert("1000:-1"),
            music_parameters.DirectPitch(500),
        )
        self.assertEqual(
            converter.convert(mmml_converters.configurations.REST_IDENTIFIER),
            None,
        )


class MMMLSingleJIPitchConverterTest(unittest.TestCase):
    def setUp(self):
        self.converter = mmml_converters.MMMLSingleJIPitchConverter()

    def convert(self):
        self.assertEqual(
            self.converter.convert("1"), music_parameters.JustIntonationPitch("1/1")
        )
        self.assertEqual(
            self.converter.convert("3"), music_parameters.JustIntonationPitch("1/1")
        )
        self.assertEqual(
            self.converter.convert("3+"), music_parameters.JustIntonationPitch("3/2")
        )
        self.assertEqual(
            self.converter.convert("3+:1"),
            music_parameters.JustIntonationPitch("3/1"),
        )
        self.assertEqual(
            self.converter.convert("3+:-1"),
            music_parameters.JustIntonationPitch("3/4"),
        )
        self.assertEqual(
            self.converter.convert("3-"), music_parameters.JustIntonationPitch("4/3")
        )
        self.assertEqual(
            self.converter.convert("3--"),
            music_parameters.JustIntonationPitch("16/9"),
        )
        self.assertEqual(
            self.converter.convert("13+"),
            music_parameters.JustIntonationPitch("13/8"),
        )
        self.assertEqual(
            self.converter.convert("13+11-"),
            music_parameters.JustIntonationPitch("13/11"),
        )
        self.assertEqual(
            self.converter.convert("3++7-"),
            music_parameters.JustIntonationPitch("9/7"),
        )
        self.assertEqual(
            self.converter.convert("3+5+:2"),
            music_parameters.JustIntonationPitch("15/2"),
        )

    def convert_invalid_input(self):
        self.assertRaises(lambda: self.converter.convert("3+3-"))
        self.assertRaises(
            lambda: self.converter.convert("random characters are invalid")
        )


class MMMLPitchesConverterTest(unittest.TestCase):
    def setUp(self):
        def octave_mark_processor(
            converted_pitch: music_parameters.WesternPitch, octave_mark: str
        ) -> music_parameters.WesternPitch:
            if octave_mark:
                converted_pitch.octave = int(octave_mark)
            return converted_pitch

        decodex_dict = {
            pitch_class: music_parameters.WesternPitch(pitch_class)
            for pitch_class in "c d e f g a b".split(" ")
        }
        diatonic_pitch_converter = mmml_converters.MMMLSinglePitchConverter(
            decodex_dict, octave_mark_processor
        )
        self.default_pitch = music_parameters.WesternPitch()
        self.default_octave_mark = "6"
        self.converter = mmml_converters.MMMLPitchesConverter(
            diatonic_pitch_converter,
            default_pitch=self.default_pitch,
            default_octave_mark=self.default_octave_mark,
        )

    def test_default_pitch(self):
        self.assertEqual(self.converter.convert([[]]), ((self.default_pitch,),))

    def test_default_octave_mark(self):
        self.assertEqual(
            self.converter.convert("c"),
            ((music_parameters.WesternPitch("c", int(self.default_octave_mark)),),),
        )

    def test_chords(self):
        self.assertEqual(
            self.converter.convert("c:5,d:4,e:1 f:4 g:4,a:4"),
            (
                (
                    music_parameters.WesternPitch("c", 5),
                    music_parameters.WesternPitch("d", 4),
                    music_parameters.WesternPitch("e", 1),
                ),
                (music_parameters.WesternPitch("f", 4),),
                (
                    music_parameters.WesternPitch("g", 4),
                    music_parameters.WesternPitch("a", 4),
                ),
            ),
        )

    def test_previous_pitches(self):
        self.assertEqual(
            self.converter.convert(["c:4", None, "f:4,g:4", None]),
            (
                (music_parameters.WesternPitch("c", 4),),
                (music_parameters.WesternPitch("c", 4),),
                (
                    music_parameters.WesternPitch("f", 4),
                    music_parameters.WesternPitch("g", 4),
                ),
                (
                    music_parameters.WesternPitch("f", 4),
                    music_parameters.WesternPitch("g", 4),
                ),
            ),
        )

    def test_previous_octave_mark(self):
        self.assertEqual(
            self.converter.convert("c:2 c"),
            (
                (music_parameters.WesternPitch("c", 2),),
                (music_parameters.WesternPitch("c", 2),),
            ),
        )

    def test_previous_octave_mark_in_chords(self):
        self.assertEqual(
            self.converter.convert("c:2,d"),
            (
                (
                    music_parameters.WesternPitch("c", 2),
                    music_parameters.WesternPitch("d", 2),
                ),
            ),
        )

    def test_rests(self):
        self.assertEqual(
            self.converter.convert(["c:4", "r", "f:4"]),
            (
                (music_parameters.WesternPitch("c", 4),),
                tuple([]),
                (music_parameters.WesternPitch("f", 4),),
            ),
        )
        self.assertEqual(
            self.converter.convert("c:4 r f:4"),
            (
                (music_parameters.WesternPitch("c", 4),),
                tuple([]),
                (music_parameters.WesternPitch("f", 4),),
            ),
        )


class MMMLEventsConverter(unittest.TestCase):
    def setUp(self):
        self.converter = mmml_converters.MMMLEventsConverter(
            mmml_converters.MMMLPitchesConverter(
                mmml_converters.MMMLSingleJIPitchConverter()
            )
        )

    def test_convert_pitch(self):
        self.assertEqual(
            music_events.NoteLike("3/2", fractions.Fraction(1, 4), "mf"),
            self.converter.convert("3+")[0],
        )

    def test_convert_events(self):
        self.assertEqual(
            core_events.SequentialEvent(
                [
                    music_events.NoteLike("3/2", fractions.Fraction(1, 2), "mf"),
                    music_events.NoteLike("5/4", fractions.Fraction(1, 4), "f"),
                ]
            ),
            self.converter.convert("3+`2 5+`4*f"),
        )


if __name__ == "__main__":
    unittest.main()
