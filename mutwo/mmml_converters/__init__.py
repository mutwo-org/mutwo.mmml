"""Convert MMML expressions to mutwo events.

MMML is an abbreviation for 'Mutwos Music Markup Language'.
Similarly to `Music Macro Language <https://en.wikipedia.org/wiki/Music_Macro_Language>`_
it is intended to be a easy human readable and writeable plain text encoding
for musical data.

A MMML expression is composed of

$head
    $block

where $head is

    $expression_name $arg0 $arg1 ... $argN

where $block is

    $mmmlexpression0
    $mmmlexpression1
    ...
    $mmmlexpressionN

Each expression is solved into a :class:`mutwo.core_events.abc.Event`.
Decoders are responsible for the conversion. Decoders are defined with
:func:`mutwo.mmml_converters.register_decoder`.

**Example of a MMML expression:**

seq melody
    n 1/4 c
    n 1/8 d pp
    n 1/8 e

    sim
        n 1/4 c,d ff
        n 1/4 g   p

    n 1/2 f
    n 1/8
"""


from . import constants
from . import configurations

from .codes import *
from .frontends import *
from .backends import *
