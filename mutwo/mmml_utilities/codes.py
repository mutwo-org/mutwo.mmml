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
        self.__decoder_default_dict = {}

    def __getitem__(self, key: str):
        return self.__decoder_dict[key]

    def __contains__(self, obj: typing.Any) -> bool:
        return obj in self.__decoder_dict

    def reset_defaults(self):
        self.__decoder_default_dict = {}

    def register_decoder(self, function: Decoder, name: typing.Optional[str] = None):
        name = name or function.__name__
        if name in self:
            self._logger.warning(
                f"Decoder '{name}' already exists and is overridden now."
            )
        self.__decoder_dict[name] = self._wrap_decoder(name, function)

    def _wrap_decoder(self, decoder_name: str, function: typing.Callable):
        """Wrap decoder so that it uses the previously used values for its args

        With the help of wrapping in the following MMML expression the second
        note also has a volume of 'fff':

            seq
                n 1/1 c fff
                {{! The following note also has 'fff', because }}
                {{! the previous NoteLike set it as its default. }}
                n 1/1 c
        """

        def _(*args):
            self._set_decoder_default_args(decoder_name, args)
            args = self._get_decoder_default_args(decoder_name, args)
            return function(*args)

        return _

    def _set_decoder_default_args(self, decoder_name: str, args: tuple):
        """Set currently defined arguments as new default values for decoder"""
        present_default = self.__decoder_default_dict.get(decoder_name, [])
        if len(args) > len(present_default):
            default = list(args)
        else:
            default = present_default
            for i, v in enumerate(args):
                default[i] = v
        self.__decoder_default_dict[decoder_name] = default

    def _get_decoder_default_args(self, decoder_name: str, args: tuple):
        """Add previously used arguments for decoder to argument list"""
        arg_list = list(args)
        arg_count = len(arg_list)
        present_default = self.__decoder_default_dict[decoder_name]
        diff = len(present_default) - arg_count
        for i in range(diff):
            arg_list.append(present_default[arg_count + i])
        return tuple(arg_list)


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
