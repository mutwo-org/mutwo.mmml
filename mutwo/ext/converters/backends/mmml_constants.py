"""Constants for :mod:`mutwo.ext.converters.backends.mmml`."""

EVENT_IDENTIFIER = " "
"""Identifier for a new event."""

OCTAVE_IDENTIFIER = ":"
"""Identifier for indicating the octave."""

MULTIPLE_PITCHES_IDENTIFIER = ","
"""Identifier for multiple pitches (for writing chords)."""

RHYTHM_IDENTIFIER = "`"
"""Identifier for writing rhythms."""

DYNAMIC_IDENTIFIER = "*"
"""Identifier for writing dynamics."""

MULTIPLE_ATTRIBUTES_IDENTIFIER = ";"
"""Identifier for seperating multiple attributes."""

ATTRIBUTE_DEFINITION_IDENTIFIER = "="
"""Identifier between attribute name and attribute value."""

ATTRIBUTE_START_IDENTIFIER = "<"
"""Identifier for setting arguments of attributes.
Inspired by Guido."""

ATTRIBUTE_END_IDENTIFIER = ">"
"""Identifier for setting arguments of attributes.
Inspired by Guido."""

VARIABLE_IDENTIFIER = "$"
"""Identifier to define variables"""

REST_IDENTIFIER = "r"
"""Identifier for writing rests.
Inspired by Lilypond."""

COMMENT_IDENTIFIER = "#"
"""Identifier for writing comments.
Inspired by bash and scripting languages like Python, Perl, etc."""

JUST_INTONATION_POSITIVE_EXPONENT_IDENTIFIER = "+"
"""Identifier for positive exponent when using
:class:`mutwo.converters.backends.mmml.MMMLSingleJIPitchConverter`."""

JUST_INTONATION_NEGATIVE_EXPONENT_IDENTIFIER = "-"
"""Identifier for negative exponent when using
:class:`mutwo.converters.backends.mmml.MMMLSingleJIPitchConverter`."""

AFTER_GRACE_NOTE_LIST_IDENTIFIER = ":after"
"""Identifier to detect a list of after grace notes."""

BEFORE_GRACE_NOTE_LIST_IDENTIFIER = ":before"
"""Identifier to detect a list of grace notes."""

GRACE_NOTE_LIST_START_IDENTIFIER = "["
"""Identifier to start a list of (after) grace notes."""

GRACE_NOTE_LIST_END_IDENTIFIER = "]"
"""Identifier to start a list of (after) grace notes."""
