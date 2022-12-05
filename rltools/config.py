import typing
import abc
import re
import argparse
import dataclasses

from ruamel.yaml import YAML

_ValidType = typing.Union[int, float, bool, str, list, tuple]
_INVALID_TYPE_MSG = "Flat and homogeneous types " \
                    f"are only supported: {typing.get_args(_ValidType)}"


# TODO: freeze it but with types conversion; add kw_only later.
@dataclasses.dataclass
class Config(abc.ABC):
    """Config object with all the hyperparameters.

    Config avoids nested and heterogeneous types,
    so only a subset of containers are supported: list, tuple, set.
    Fancy Union types are handled by the first option. Optional is supported.
    Docstring is used to derive help msg for ArgumentParser.
    """

    def save(self, file_path: str) -> None:
        """Save as YAML in a specified path."""
        yaml = YAML(typ="safe", pure=True)
        with open(file_path, "w", encoding="utf-8") as config_file:
            yaml.dump(dataclasses.asdict(self), config_file)

    @classmethod
    def load(cls, file_path: str, **kwargs) -> "Config":
        """Load config from a YAML. Then values are updated by kwargs."""
        yaml = YAML(typ="safe", pure=True)
        with open(file_path, "r", encoding="utf-8") as config_file:
            config_dict = yaml.load(config_file)
        config_dict.update(kwargs)

        known_names = tuple(
            map(lambda field: field.name, dataclasses.fields(cls))
        )
        config_dict = {k: v for k, v in config_dict.items() if k in known_names}
        return cls(**config_dict)

    def __post_init__(self) -> None:
        """Casts fields to declared types."""
        valid_types = tuple(map(_topy, typing.get_args(_ValidType)))
        for field in dataclasses.fields(self):
            ftype = _strip_union(field.type)
            fdtype = _topy(ftype)
            # Validate
            if fdtype not in valid_types:
                raise TypeError(field.type, _INVALID_TYPE_MSG)

            value = getattr(self, field.name)
            args = typing.get_args(ftype)
            if args:  # Assuming flatness.
                dtype = args[0]  # Assuming homogeneity.
                value = _topy(map(_topy(dtype), value))

            is_optional = typing.get_origin(field.type) == typing.Union
            if is_optional and value is None:
                setattr(self, field.name, None)
            else:
                setattr(self, field.name, fdtype(value))

    @classmethod
    def from_entrypoint(cls,
                        parser: typing.Optional[argparse.ArgumentParser] = None,
                        ) -> "Config":
        """Populate commandline kwargs with a config fields."""
        if parser is None:
            parser = argparse.ArgumentParser()

        def _add_argument(field: dataclasses.Field) -> typing.Dict[str, str]:
            """Extract all the possible information from the instance."""
            action = dict(dest=field.name, default=field.default)

            # Parse docstring.
            help_ = re.search(fr"\s{field.name}: (.*)\n", cls.__doc__)
            if help_ is not None:
                help_ = help_[1]
            action["help"] = help_

            # Infer dtype.
            ftype = _strip_union(field.type)
            args = typing.get_args(ftype)
            dtype = _topy(ftype)
            if dtype is bool:
                action["action"] = argparse.BooleanOptionalAction
            if args:
                dtype = _topy(args[0])
                action["nargs"] = "+"
            action["type"] = dtype
            return action

        known_args = []
        for fd in dataclasses.fields(cls):
            known_args.append(fd.name)
            action = _add_argument(fd)
            parser.add_argument(f"--{fd.name}", **action)
        args, _ = parser.parse_known_args()
        kwargs = {k: v for k, v in vars(args).items() if k in known_args}
        return cls(**kwargs)


def _topy(dtype: typing.Union[typing.GenericAlias, type]) -> type:
    """To support both typing hints and GenericAliases."""
    return typing.get_origin(dtype) or dtype


def _strip_union(dtype):
    """Strip Union and Optional in unsafe manner."""
    if typing.get_origin(dtype) == typing.Union:
        dtype = typing.get_args(dtype)[0]
    return dtype
