import unittest

from mutwo import core_events
from mutwo import mmml_converters
from mutwo import mmml_utilities
from mutwo import music_events

n = music_events.NoteLike
cns = core_events.Consecution
cnc = core_events.Concurrence


class MMMLExpressionToEventTest(unittest.TestCase):
    def setUp(self):
        self.c = mmml_converters.MMMLExpressionToEvent(use_defaults=True)
        self.reset = self.c.reset_defaults

    def test_mustache(self):
        """Test that usage of mustache template language is supported"""

        # Comments
        self.assertTrue(self.c("{{! this is a comment }}\n" "n\n" "{{! comment2 }}"))

    def test_multiple_expressions(self):
        """Test that only one MMML expression is allowed per string"""

        self.assertRaises(mmml_utilities.MalformedMMML, self.c, ("n\n" "n\n"))
        self.assertRaises(
            mmml_utilities.MalformedMMML, self.c, ("cns\n" "    n\n" "n\n")
        )

    def test_bad_indentation(self):
        """Test that bad indentation is forbidden"""
        self.assertRaises(mmml_utilities.MalformedMMML, self.c, ("cns\n" "        n\n"))

    def test_no_expression(self):
        """Test that no expression is forbidden"""
        self.assertRaises(mmml_utilities.MalformedMMML, self.c, (""))

    def test_space_between_arguments(self):
        """Test that any space between arguments is ignored"""

        # more than 1 space
        self.assertEqual(n("c", "1/4"), self.c("n    1/4   c"))
        # tabs
        self.assertEqual(n("c", "1/4"), self.c("n\t\t1/4\tc"))

    def test_empty_lines(self):
        """Test that empty lines are ignored"""

        # first line
        self.assertEqual(n(), self.c("\n\n\nn"))

        # last line
        self.assertEqual(n(), self.c("n\n\n\n"))

        # line in between
        self.assertEqual(cns([n(), n()]), self.c("cns\n\n    n\n    \n    n"))

        # empty but with tabs or space
        self.assertEqual(cns(), self.c("cns\n    \n     \n\t\n\t  \t"))

    def test_ignore_comments(self):
        mmml = """
# this is a comment

             # this is a comment
# this is also a comment
cns

    # this is also a comment
"""
        self.assertEqual(self.c(mmml), core_events.Consecution())

    def test_decoder_n(self):
        """Test that builtin decoder 'n' returns NoteLike with correct attr"""

        self.assertEqual(n(), self.c("n"))

        # Set duration
        self.assertEqual(n(duration=2), self.c("n 2"))
        self.assertEqual(n(duration="1/4"), self.c("n 1/4"))

        # Set pitch
        self.assertEqual(n("c4"), self.c("n 1 c4"))
        #  multiple pitches
        self.assertEqual(n("c4 ds3"), self.c("n 1 c4,ds3"))
        #  just intonation pitches
        self.assertEqual(n("4/3 3/2"), self.c("n 1 4/3,3/2"))

        # Set volume
        self.assertEqual(n("c4", volume="f"), self.c("n 1 c4 f"))

        # Set grace notes
        mmml = """
n 1 c4 mf
    n 1/4 c4 mf
    n 1/4 d4 mf
"""
        self.assertEqual(
            self.c(mmml),
            n(
                "c4",
                duration=1,
                grace_note_consecution=core_events.Consecution(
                    [n("c", "1/4"), n("d", "1/4")]
                ),
            ),
        )

    def test_decoder_r(self):
        """Test that builtin decoder 'r' returns NoteLike with correct attr"""

        self.assertEqual(n(), self.c("r"))

        # Set duration
        self.assertEqual(n(duration=2), self.c("r 2"))
        self.assertEqual(n(duration="1/4"), self.c("r 1/4"))

    def test_decoder_cns(self):
        """Test that builtin decoder 'cns' returns Consecution"""

        self.assertEqual(cns(), self.c("cns"))

        # Set tag
        self.assertEqual(cns(tag="abc"), self.c("cns abc"))
        self.assertEqual(cns(tag="100"), self.c("cns 100"))

        self.reset()

        # Set tempo
        self.assertEqual(cns(tempo=20), self.c("cns _ 20"))
        self.assertEqual(cns(tempo=[[0, 20], [1, 30]]), self.c("cns _ [[0,20],[1,30]]"))

        self.reset()

        # Add children
        self.assertEqual(cns([n(), n()]), self.c("cns\n" "    n\n" "    n"))
        #  Nested children
        self.assertEqual(
            cns([n(), cns([n()]), n()]),
            self.c("cns\n" "    n\n" "    cns\n" "        n\n" "    n"),
        )

    def test_decoder_cnc(self):
        """Test that builtin decoder 'cnc' returns Concurrence"""

        self.assertEqual(cnc(), self.c("cnc"))

        # Set tag
        self.assertEqual(cnc(tag="abc"), self.c("cnc abc"))

        # Set tempo
        self.assertEqual(cnc(tempo=20), self.c("cnc _ 20"))
        self.assertEqual(cnc(tempo=[[0, 20], [1, 30]]), self.c("cnc _ [[0,20],[1,30]]"))

        self.reset()

    def test_empty_argument(self):
        """Ensure that MMML takes the decoders default value if magic '_' is given as an argument"""
        self.assertEqual(n(volume="pppp"), self.c("n _ _ pppp"))
        self.assertEqual(n(volume="pppp", duration="5/4"), self.c("n 5/4 _ pppp"))


class EventToMMMLExpressionTest(unittest.TestCase):
    def setUp(self):
        self.c = mmml_converters.EventToMMMLExpression()

    def test_note_like(self):
        self.assertEqual(self.c(n("c", "1/4", "ff")), "n 1/4 c4 ff _ _")

    def test_note_like_with_indicator_collection(self):
        note = n("c", "1/4", "ff")
        note.playing_indicator_collection.fermata.type = "fermata"
        note.playing_indicator_collection.arpeggio.direction = "up"
        self.assertEqual(
            self.c(note), "n 1/4 c4 ff arpeggio.direction=up;fermata.type=fermata _"
        )

        note = n("c", "1/4", "ff")
        note.notation_indicator_collection.clef.name = "bass"

        self.assertEqual(self.c(note), "n 1/4 c4 ff _ clef.name=bass")

    def test_note_like_with_grace_note_consecution(self):
        note = n("d", "1/4", "p")
        note.grace_note_consecution.append(n("c", "1/4", "p"))
        self.assertEqual(self.c(note), "n 1/4 d4 p _ _\n\n    n 1/4 c4 p _ _\n")

    def test_note_like_just_intonation_pitch_1_1(self):
        """Ensure 1/1 JI pitch is rendered as '1/1' and not as '1',
        because otherwise the 'MMMLExpressionToEvent' converter
        won't be able to re-load the MMML expression."""
        self.assertEqual(self.c(n("1/1", "1/4", "ff")), "n 1/4 1/1 ff _ _")

    def test_rest(self):
        self.assertEqual(self.c(n()), "r 1 _ _")
        self.assertEqual(self.c(n([], "5/4")), "r 5/4 _ _")

    def test_consecution(self):
        self.assertEqual(self.c(cns()), "cns\n")
        self.assertEqual(self.c(cns(tag="abc")), "cns abc\n")
        self.assertEqual(self.c(cns([n(), n()])), "cns\n\n    r 1 _ _\n    r 1 _ _\n")
        self.assertEqual(
            self.c(cns([n(), cns([n()])])),
            "cns\n\n    r 1 _ _\n    cns\n\n        r 1 _ _\n\n",
        )
        self.assertEqual(self.c(cns(tempo=20)), "cns _ 20\n")
        self.assertEqual(
            self.c(cns(tempo=[[0, 20], [1, 30]])), "cns _ [[0,20],[1,30]]\n"
        )

    def test_concurrence(self):
        self.assertEqual(self.c(cnc()), "cnc\n")
        self.assertEqual(self.c(cnc(tag="abc")), "cnc abc\n")
        self.assertEqual(self.c(cnc([n(), n()])), "cnc\n\n    r 1 _ _\n    r 1 _ _\n")
        self.assertEqual(
            self.c(cnc([n(), cnc([n()])])),
            "cnc\n\n    r 1 _ _\n    cnc\n\n        r 1 _ _\n\n",
        )
