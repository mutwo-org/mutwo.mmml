# mutwo.mmml

[![Build Status](https://circleci.com/gh/mutwo-org/mutwo.mmml.svg?style=shield)](https://circleci.com/gh/mutwo-org/mutwo.mmml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PyPI version](https://badge.fury.io/py/mutwo.mmml.svg)](https://badge.fury.io/py/mutwo.mmml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

MMML (mutwos music markup language) extension for event based library [mutwo](https://github.com/mutwo-org/mutwo).

This extension implements:

- `mutwo.mmml_converters`

### Installation

mutwo.mmml is available on [pypi](https://pypi.org/project/mutwo.mmml/) and can be installed via pip:

```sh
pip3 install mutwo.mmml
```


### Example usage

MMML expressions represent exactly one mutwo event.
But the event can be nested:

```
{{! We can write comments using mustache. }}
{{! (We can also add variables using mustache) }}

{{! Let's express one simultaneous event that contains our music. }}

sim music


    {{! It contains two sequences: a violin and a cello voice. }}

    seq violin

        {{! 'n' is used to express a note. }}

        n 1/4 a5 p
        n 1/4 bf5
        n 1/4 a5

        {{! 'r' is used to express a rest. }}

        r 1/4

        n 1/4 a5 mf
        n 1/4 bf5 mp
        n 1/4 a5
        r 1/4


    seq cello

        n 1/2 c3 p
        r 1/2

        n 1/2 d3 p
        r 1/2
```
