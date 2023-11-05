import unittest

from mutwo import core_events
from mutwo import mmml_converters
from mutwo import mmml_utilities
from mutwo import music_events

n = music_events.NoteLike
seq = core_events.TaggedSequentialEvent
sim = core_events.TaggedSimultaneousEvent


class MMMLExpressionToEventTest(unittest.TestCase):
    def setUp(self):
        self.c = mmml_converters.MMMLExpressionToEvent()
        self.reset = mmml_converters.constants.DECODER_REGISTRY.reset_defaults
        self.reset()

    def test_mustache(self):
        """Test that usage of mustache template language is supported"""

        # Comments
        self.assertTrue(self.c("{{! this is a comment }}\n" "n\n" "{{! comment2 }}"))

    def test_multiple_expressions(self):
        """Test that only one MMML expression is allowed per string"""

        self.assertRaises(mmml_utilities.MalformedMMML, self.c, ("n\n" "n\n"))
        self.assertRaises(
            mmml_utilities.MalformedMMML, self.c, ("seq\n" "    n\n" "n\n")
        )

    def test_bad_indentation(self):
        """Test that bad indentation is forbidden"""
        self.assertRaises(mmml_utilities.MalformedMMML, self.c, ("seq\n" "        n\n"))

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
        self.assertEqual(seq([n(), n()]), self.c("seq\n\n\n    n\n\n\n    n"))

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

    def test_decoder_r(self):
        """Test that builtin decoder 'r' returns NoteLike with correct attr"""

        self.assertEqual(n(), self.c("r"))

        # Set duration
        self.assertEqual(n(duration=2), self.c("r 2"))
        self.assertEqual(n(duration="1/4"), self.c("r 1/4"))

    def test_decoder_seq(self):
        """Test that builtin decoder 'seq' returns TaggedSequentialEvent"""

        self.assertEqual(seq(), self.c("seq"))

        # Set tag
        self.assertEqual(seq(tag="abc"), self.c("seq abc"))
        self.assertEqual(seq(tag="100"), self.c("seq 100"))

        self.reset()

        # Add children
        self.assertEqual(seq([n(), n()]), self.c("seq\n" "    n\n" "    n"))
        #  Nested children
        self.assertEqual(
            seq([n(), seq([n()]), n()]),
            self.c("seq\n" "    n\n" "    seq\n" "        n\n" "    n"),
        )

    def test_decoder_sim(self):
        """Test that builtin decoder 'sim' returns TaggedSimultaneousEvent"""

        self.assertEqual(sim(), self.c("sim"))

        # Set tag
        self.assertEqual(sim(tag="abc"), self.c("sim abc"))


class EventToMMMLExpressionTest(unittest.TestCase):
    def setUp(self):
        self.c = mmml_converters.EventToMMMLExpression()

    def test_note_like(self):
        self.assertEqual(self.c(n("c", "1/4", "ff")), "n 1/4 c4 ff")

    def test_rest(self):
        self.assertEqual(self.c(n()), "r 1")
        self.assertEqual(self.c(n([], "5/4")), "r 5/4")

    def test_sequential_event(self):
        self.assertEqual(self.c(seq()), "seq\n")
        self.assertEqual(self.c(seq(tag="abc")), "seq abc\n")
        self.assertEqual(self.c(seq([n(), n()])), "seq\n\n    r 1\n    r 1\n")
        self.assertEqual(
            self.c(seq([n(), seq([n()])])), "seq\n\n    r 1\n    seq\n\n        r 1\n\n"
        )

    def test_simultaneous_event(self):
        self.assertEqual(self.c(sim()), "sim\n")
        self.assertEqual(self.c(sim(tag="abc")), "sim abc\n")
        self.assertEqual(self.c(sim([n(), n()])), "sim\n\n    r 1\n    r 1\n")
        self.assertEqual(
            self.c(sim([n(), sim([n()])])), "sim\n\n    r 1\n    sim\n\n        r 1\n\n"
        )
