# mutwo.mmml

[![Build Status](https://circleci.com/gh/mutwo-org/mutwo.mmml.svg?style=shield)](https://circleci.com/gh/mutwo-org/mutwo.mmml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PyPI version](https://badge.fury.io/py/mutwo.mmml.svg)](https://badge.fury.io/py/mutwo.mmml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This package adds parsers and specifications for the 'mutwo music markup language' (short: MMML).
With this language it's easy, fast and convenient to write music in a text file.
MMML consist of expressions that can be converted to [mutwo](https://mutwo-org.github.io) events.
The package also adds reverse parsers, to convert [mutwo](https://mutwo-org.github.io) events back to MMML.

## Installation

mutwo.mmml is available on [pypi](https://pypi.org/project/mutwo.mmml/) and can be installed via pip:

```sh
pip3 install mutwo.mmml
```

## The rules

MMML is a very simple and minimalistic file format with few, but quite strict rules.

### 1 MMML expression <=> 1 event

1. A MMML string consist of only one MMML expression.
2. Each MMML expression consist of exactly 1 event.
3. But an event can have children events (it can be nested).

### An MMML expression = head + block

4. An MMML expression has two parts: a head and a block.
5. The head tells what type of event we have with which arguments.
6. The block defines all children events that our main event has.

```
$HEAD
    $BLOCK
```

### The head: main event (= container) definition

7. An MMML expression head is defined across exactly one line in a text.
8. It consist of different parts that are separated by one or more white spaces.
9. The first part of a head declares the event type, all other parts are arguments for the event. All arguments are optional.

```
$EVENT_TYPE $ARG_0 $ARG_1 ... $ARG_N
```

### The block: children events definitions

10. To start a block after a head, we need to increase the indentation of +4 white spaces compared to the indentation level of the head.
11. A block is composed of one or more MMML expressions.
12. In this way we can define on or more events that are part of the main event that's defined in the head.


```
$HEAD
    $MMML_EXPRESSION_0
    $MMML_EXPRESSION_1
    $MMML_EXPRESSION_2
    ...
    $MMML_EXPRESSION_N
```

## Builtin head / event types

`mutwo.mmml` provides few builtin events:

### `cns $tag $tempo`

Renders to [Consecution](https://mutwo-org.github.io/api/mutwo.core_events.html#mutwo.core_events.Consecution).

### `cnc $tag $tempo`

Renders to [Concurrence](https://mutwo-org.github.io/api/mutwo.core_events.html#mutwo.core_events.Concurrence).

### `n $duration $pitch $volume $playing_indicator_collection $notation_indicator_collection $lyric $instument_list`

Renders to [NoteLike](https://mutwo-org.github.io/api/mutwo.music_events.html#mutwo.music_events.NoteLike).

### `r $duration $volume $playing_indicator_collection $notation_indicator_collection $lyric $instument_list`

Renders to [NoteLike](https://mutwo-org.github.io/api/mutwo.music_events.html#mutwo.music_events.NoteLike).
Same like `n`, but without the option to specify pitches.

## Extra rules

Besides the basic rules, MMML has a few extra rules to make using the language more convenient.
They generally aim to be easily implementable and not making the language too complex.

1. Empty lines are ignored. Empty means 'only white space or tabs' or 'nothing at all'.
2. Any line, where the first character (that's not white space) is '#', is also ignored. Such a line is regarded as a comment.
3. The special head argument `_` is always skipped. In this way it's possible to define for instance the fourth argument of an event [without necessarily having to declare all three previous arguments](https://github.com/mutwo-org/mutwo.mmml/commit/134ceda96986395887958946aaf4f1d253ade75a).

## Example


```
# We can write comments when starting a line with '#'

        # whitespace at the beggining is ignored for comments

# Let's express one simultaneous event that contains our music.

cnc music


    # It contains two sequences: a violin and a cello voice.

    cns violin

        # 'n' is used to express a note.

        n 1/4 a5 p
        n 1/4 bf5
        n 1/4 a5

        # We can skip arguments with _

        n 1/8 _ _ fermata.type=fermata

        # 'r' is used to express a rest.

        r 1/4

        n 1/4 a5 mf
        n 1/4 bf5 mp
        n 1/4 a5
        r 1/4


    cns cello

        n 1/2 c3 p
        r 1/2

        n 1/2 d3 p
        r 1/2
```


## Extending `mutwo.mmml`

`mutwo.mmml` can easily be appended by new event types.
Already given event types can also be overridden.
For this purpose `mutwo.mmml` uses a registry as a API.
To understand how this can be used [simply check the respective source code](https://github.com/mutwo-org/mutwo.mmml/blob/main/mutwo/mmml_converters/codes.py).
