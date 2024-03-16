from mutwo import mmml_utilities

DECODER_REGISTRY = mmml_utilities.DecoderRegistry()
ENCODER_REGISTRY = mmml_utilities.EncoderRegistry()
INDENTATION = r"    "

IGNORE_MAGIC = r"_"
"""If this is used as an argument, it is ignored"""


del mmml_utilities
