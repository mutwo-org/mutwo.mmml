import typing

from mutwo import core_utilities


__all__ = ("SolverRegistry",)


class SolverRegistry(object):
    def __init__(self):
        self._logger = core_utilities.get_cls_logger(type(self))
        self.__solver_dict = {}
        self.__solver_default_dict = {}

    def __getitem__(self, key: str):
        return self.__solver_dict[key]

    def __contains__(self, obj: typing.Any) -> bool:
        return obj in self.__solver_dict

    def reset_defaults(self):
        self.__solver_default_dict = {}

    def register_solver(
        self, function: typing.Callable, name: typing.Optional[str] = None
    ):
        name = name or function.__name__
        if name in self:
            self._logger.warning(f"Solver '{name}' already exists and is overridden now.")
        self.__solver_dict[name] = self._wrap_solver(name, function)

    def _wrap_solver(self, solver_name: str, function: typing.Callable):
        """Wrap solver so that it uses the previously used values for its args

        With the help of wrapping in the following MMML expression the second
        note also has a volume of 'fff':

            seq
                n 1/1 c fff
                {{! The following note also has 'fff', because }}
                {{! the previous NoteLike set it as its default. }}
                n 1/1 c
        """
        def _(*args):
            self._set_solver_default_args(solver_name, args)
            args = self._get_solver_default_args(solver_name, args)
            return function(*args)

        return _

    def _set_solver_default_args(self, solver_name: str, args: tuple):
        """Set currently defined arguments as new default values for solver"""
        present_default = self.__solver_default_dict.get(solver_name, [])
        if len(args) > len(present_default):
            default = list(args)
        else:
            default = present_default
            for i, v in enumerate(args):
                default[i] = v
        self.__solver_default_dict[solver_name] = default

    def _get_solver_default_args(self, solver_name: str, args: tuple):
        """Add previously used arguments for solver to argument list"""
        arg_list = list(args)
        arg_count = len(arg_list)
        present_default = self.__solver_default_dict[solver_name]
        diff = len(present_default) - arg_count
        for i in range(diff):
            arg_list.append(present_default[arg_count + i])
        return tuple(arg_list)
