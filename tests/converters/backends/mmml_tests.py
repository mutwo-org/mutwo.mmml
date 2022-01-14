import fractions
import unittest

from mutwo.core import events

from mutwo.ext.converters import backends
from mutwo.ext import events as ext_events
from mutwo.ext import parameters as ext_parameters


class MMMLSinglePitchConverterTest(unittest.TestCase):
    def test_convert_via_decodex_dict(self):
        def octave_mark_processor(
            converted_pitch: ext_parameters.pitches.WesternPitch, octave_mark: str
        ) -> ext_parameters.pitches.WesternPitch:
            if octave_mark:
                converted_pitch.octave = int(octave_mark)
            return converted_pitch

        decodex_dict = {
            pitch_class: ext_parameters.pitches.WesternPitch(pitch_class)
            for pitch_class in "c d e f g a b".split(" ")
        }
        converter = backends.mmml.MMMLSinglePitchConverter(
            decodex_dict, octave_mark_processor
        )

        self.assertEqual(
            converter.convert("d"),
            ext_parameters.pitches.WesternPitch("d", 4),
        )
        self.assertEqual(
            converter.convert("c:5"),
            ext_parameters.pitches.WesternPitch("c", 5),
        )
        self.assertEqual(
            converter.convert("b:3"),
            ext_parameters.pitches.WesternPitch("b", 3),
        )
        self.assertEqual(
            converter.convert("f"),
            ext_parameters.pitches.WesternPitch("f", 4),
        )
        self.assertEqual(
            converter.convert(backends.mmml_constants.REST_IDENTIFIER),
            None,
        )

    def test_convert_via_decodex_function(self):
        def decodex_function(
            mmml_pitch_class_to_convert: str,
        ) -> ext_parameters.pitches.DirectPitch:
            frequency = float(mmml_pitch_class_to_convert)
            return ext_parameters.pitches.DirectPitch(frequency)

        def octave_mark_processor(
            converted_pitch: ext_parameters.pitches.DirectPitch, octave_mark: str
        ) -> ext_parameters.pitches.DirectPitch:
            if octave_mark:
                converted_pitch = ext_parameters.pitches.DirectPitch(
                    converted_pitch.frequency * (2 ** int(octave_mark))
                )
            return converted_pitch

        converter = backends.mmml.MMMLSinglePitchConverter(
            decodex_function, octave_mark_processor
        )
        self.assertEqual(
            converter.convert("200"),
            ext_parameters.pitches.DirectPitch(200),
        )
        self.assertEqual(
            converter.convert("300:1"),
            ext_parameters.pitches.DirectPitch(600),
        )
        self.assertEqual(
            converter.convert("400.5"),
            ext_parameters.pitches.DirectPitch(400.5),
        )
        self.assertEqual(
            converter.convert("1000:-1"),
            ext_parameters.pitches.DirectPitch(500),
        )
        self.assertEqual(
            converter.convert(backends.mmml_constants.REST_IDENTIFIER),
            None,
        )


class MMMLSingleJIPitchConverterTest(unittest.TestCase):
    def setUp(self):
        self.converter = backends.mmml.MMMLSingleJIPitchConverter()

    def convert(self):
        self.assertEqual(
            self.converter.convert("1"), ext_parameters.pitches.JustIntonationPitch("1/1")
        )
        self.assertEqual(
            self.converter.convert("3"), ext_parameters.pitches.JustIntonationPitch("1/1")
        )
        self.assertEqual(
            self.converter.convert("3+"), ext_parameters.pitches.JustIntonationPitch("3/2")
        )
        self.assertEqual(
            self.converter.convert("3+:1"),
            ext_parameters.pitches.JustIntonationPitch("3/1"),
        )
        self.assertEqual(
            self.converter.convert("3+:-1"),
            ext_parameters.pitches.JustIntonationPitch("3/4"),
        )
        self.assertEqual(
            self.converter.convert("3-"), ext_parameters.pitches.JustIntonationPitch("4/3")
        )
        self.assertEqual(
            self.converter.convert("3--"),
            ext_parameters.pitches.JustIntonationPitch("16/9"),
        )
        self.assertEqual(
            self.converter.convert("13+"),
            ext_parameters.pitches.JustIntonationPitch("13/8"),
        )
        self.assertEqual(
            self.converter.convert("13+11-"),
            ext_parameters.pitches.JustIntonationPitch("13/11"),
        )
        self.assertEqual(
            self.converter.convert("3++7-"),
            ext_parameters.pitches.JustIntonationPitch("9/7"),
        )
        self.assertEqual(
            self.converter.convert("3+5+:2"),
            ext_parameters.pitches.JustIntonationPitch("15/2"),
        )

    def convert_invalid_input(self):
        self.assertRaises(lambda: self.converter.convert("3+3-"))
        self.assertRaises(
            lambda: self.converter.convert("random characters are invalid")
        )


class MMMLPitchesConverterTest(unittest.TestCase):
    def setUp(self):
        def octave_mark_processor(
            converted_pitch: ext_parameters.pitches.WesternPitch, octave_mark: str
        ) -> ext_parameters.pitches.WesternPitch:
            if octave_mark:
                converted_pitch.octave = int(octave_mark)
            return converted_pitch

        decodex_dict = {
            pitch_class: ext_parameters.pitches.WesternPitch(pitch_class)
            for pitch_class in "c d e f g a b".split(" ")
        }
        diatonic_pitch_converter = backends.mmml.MMMLSinglePitchConverter(
            decodex_dict, octave_mark_processor
        )
        self.default_pitch = ext_parameters.pitches.WesternPitch()
        self.default_octave_mark = "6"
        self.converter = backends.mmml.MMMLPitchesConverter(
            diatonic_pitch_converter,
            default_pitch=self.default_pitch,
            default_octave_mark=self.default_octave_mark,
        )

    def test_default_pitch(self):
        self.assertEqual(self.converter.convert([[]]), ((self.default_pitch,),))

    def test_default_octave_mark(self):
        self.assertEqual(
            self.converter.convert("c"),
            ((ext_parameters.pitches.WesternPitch("c", int(self.default_octave_mark)),),),
        )

    def test_chords(self):
        self.assertEqual(
            self.converter.convert("c:5,d:4,e:1 f:4 g:4,a:4"),
            (
                (
                    ext_parameters.pitches.WesternPitch("c", 5),
                    ext_parameters.pitches.WesternPitch("d", 4),
                    ext_parameters.pitches.WesternPitch("e", 1),
                ),
                (ext_parameters.pitches.WesternPitch("f", 4),),
                (
                    ext_parameters.pitches.WesternPitch("g", 4),
                    ext_parameters.pitches.WesternPitch("a", 4),
                ),
            ),
        )

    def test_previous_pitches(self):
        self.assertEqual(
            self.converter.convert(["c:4", None, "f:4,g:4", None]),
            (
                (ext_parameters.pitches.WesternPitch("c", 4),),
                (ext_parameters.pitches.WesternPitch("c", 4),),
                (
                    ext_parameters.pitches.WesternPitch("f", 4),
                    ext_parameters.pitches.WesternPitch("g", 4),
                ),
                (
                    ext_parameters.pitches.WesternPitch("f", 4),
                    ext_parameters.pitches.WesternPitch("g", 4),
                ),
            ),
        )

    def test_previous_octave_mark(self):
        self.assertEqual(
            self.converter.convert("c:2 c"),
            (
                (ext_parameters.pitches.WesternPitch("c", 2),),
                (ext_parameters.pitches.WesternPitch("c", 2),),
            ),
        )

    def test_previous_octave_mark_in_chords(self):
        self.assertEqual(
            self.converter.convert("c:2,d"),
            (
                (
                    ext_parameters.pitches.WesternPitch("c", 2),
                    ext_parameters.pitches.WesternPitch("d", 2),
                ),
            ),
        )

    def test_rests(self):
        self.assertEqual(
            self.converter.convert(["c:4", "r", "f:4"]),
            (
                (ext_parameters.pitches.WesternPitch("c", 4),),
                tuple([]),
                (ext_parameters.pitches.WesternPitch("f", 4),),
            ),
        )
        self.assertEqual(
            self.converter.convert("c:4 r f:4"),
            (
                (ext_parameters.pitches.WesternPitch("c", 4),),
                tuple([]),
                (ext_parameters.pitches.WesternPitch("f", 4),),
            ),
        )


class MMMLEventsConverter(unittest.TestCase):
    def setUp(self):
        self.converter = backends.mmml.MMMLEventsConverter(
            backends.mmml.MMMLPitchesConverter(
                backends.mmml.MMMLSingleJIPitchConverter()
            )
        )

    def test_convert_pitch(self):
        self.assertEqual(
            ext_events.music.NoteLike("3/2", fractions.Fraction(1, 4), "mf"),
            self.converter.convert("3+")[0],
        )

    def test_convert_events(self):
        self.assertEqual(
            events.basic.SequentialEvent(
                [
                    ext_events.music.NoteLike("3/2", fractions.Fraction(1, 2), "mf"),
                    ext_events.music.NoteLike("5/4", fractions.Fraction(1, 4), "f"),
                ]
            ),
            self.converter.convert("3+`2 5+`4*f"),
        )


if __name__ == "__main__":
    unittest.main()
