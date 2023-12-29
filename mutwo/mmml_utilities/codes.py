import typing

from mutwo import core_events
from mutwo import core_utilities
from mutwo import mmml_utilities


__all__ = ("DecoderRegistry", "EncoderRegistry")


class DecoderRegistry(object):
    Decoder: typing.TypeAlias = typing.Callable[
        [typing.Any, ...], core_events.abc.Event
    ]

    def __init__(self):
        self._logger = core_utilities.get_cls_logger(type(self))
        self.__decoder_dict = {}

    def __getitem__(self, key: str):
        return self.__decoder_dict[key]

    def __contains__(self, obj: typing.Any) -> bool:
        return obj in self.__decoder_dict

    def register_decoder(self, function: Decoder, name: typing.Optional[str] = None):
        name = name or function.__name__
        if name in self:
            self._logger.warning(
                f"Decoder '{name}' already exists and is overridden now."
            )
        self.__decoder_dict[name] = function


class EncoderRegistry(object):
    def __init__(self):
        self._logger = core_utilities.get_cls_logger(type(self))
        self.__encoder_dict = {}

    def __getitem__(self, key):
        try:
            return self.__encoder_dict[key]
        except KeyError:
            raise mmml_utilities.NoEncoderExists(key)

    def __contains__(self, obj: typing.Any) -> bool:
        return obj in self.__encoder_dict

    def register_encoder(self, *encoding_type):
        def _(function):
            for t in encoding_type:
                if t in self.__encoder_dict:
                    self._logger.warning(
                        f"Encoder for '{t}' already exists and " "is overridden now."
                    )
                self.__encoder_dict[t] = function

        return _
