import click


class RequiredIfNotEmpty(click.Option):

    def __init__(self, *args, **kwargs):
        self.required_if_not_empty = kwargs.pop("required_if_empty")
        if not self.required_if_not_empty:
            raise ValueError(
                '"required_if_not_empty" argument is required for "RequiredIfNotEmpty" option'
            )
        kwargs["help"] += " NOTE: This option is required with {}".format(
            self.required_if_not_empty
        )

        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.required_if_not_empty in opts:
            if self.name not in opts:
                raise click.UsageError(
                    "Illegal usage: {} is required with {}".format(
                        self.name, self.required_if_not_empty
                    )
                )
            else:
                self.prompt = None

        return super().handle_parse_result(ctx, opts, args)


class CommaSeparatedType(click.types.StringParamType):
    """
    Plain string option whose environment variable holds a comma separated list.

    Click splits the value of the environment variable by ``envvar_list_splitter`` before it
    converts the items, so a repeatable option accepts both several occurrences on the command
    line and one comma separated environment variable.
    """

    name = "text"
    envvar_list_splitter = ","


class CommaSeparatedPathType(click.Path):
    """Path option whose environment variable holds a comma separated list."""

    envvar_list_splitter = ","


COMMA_SEPARATED = CommaSeparatedType()


class SeparatedFieldsType(click.ParamType):
    """
    Base class of the types whose value is a fixed number of fields joined with a separator.

    The separator and the field names are declared once and both directions are derived from
    them, therefore the parsing in ``convert`` and the encoding of the configuration files in
    ``encode`` cannot drift apart.
    """

    separator = ":"
    fields = ()
    envvar_list_splitter = ","

    @property
    def format_hint(self):
        return self.separator.join(self.fields)

    def convert(self, value, param, ctx):
        parts = value.split(self.separator)
        if len(parts) != len(self.fields):
            self.fail(
                'Invalid value "{}" format must be "{}"'.format(
                    value, self.format_hint
                ),
                param,
                ctx,
            )
        return tuple(parts)


def encode_field(value, name):
    """Turn a single field of a structured configuration value into its string form."""
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError('"{}" must be a string'.format(name))
    return str(value)


class ContainerDirToCopyType(SeparatedFieldsType):

    name = "container_dir_to_copy"
    fields = ("DOCKER_CONTAINER_NAME", "CONTAINER_DIRECTORY", "HOST_DIRECTORY")

    @classmethod
    def encode(cls, value):
        """Encode {container: {container directory: host directory}} into the value items."""
        if isinstance(value, (str, list, tuple)):
            return value
        if not isinstance(value, dict):
            raise ValueError(
                "must be an object of container name to an object of container directory "
                "to host directory"
            )
        items = []
        for container_name, dirs in value.items():
            if not isinstance(dirs, dict):
                raise ValueError(
                    'container "{}" must be an object of container directory to host '
                    "directory".format(container_name)
                )
            items.extend(
                cls.separator.join(
                    (
                        str(container_name),
                        str(container_dir),
                        encode_field(host_dir, container_dir),
                    )
                )
                for container_dir, host_dir in dirs.items()
            )
        return items


class ContainerCommandType(SeparatedFieldsType):

    name = "container_command_type"
    fields = ("DOCKER_CONTAINER_NAME", "COMMAND")

    @classmethod
    def encode(cls, value):
        """Encode {container: command} into the value items."""
        if isinstance(value, (str, list, tuple)):
            return value
        if not isinstance(value, dict):
            raise ValueError("must be an object of container name to command")
        return [
            cls.separator.join(
                (str(container_name), encode_field(command, container_name))
            )
            for container_name, command in value.items()
        ]


class ContainerEnvironment(click.ParamType):

    name = "container_environment"
    separator = " "
    assignment = "="
    format_hint = "NAME=VALUE [NAME2=VALUE2]"

    def convert(self, value, param, ctx):
        variables = {}
        for variable in value.split(self.separator):
            name, assignment, item = variable.partition(self.assignment)
            if not assignment:
                self.fail(
                    'Invalid value "{}" format must be "{}"'.format(
                        value, self.format_hint
                    ),
                    param,
                    ctx,
                )
            variables[name] = item
        return variables

    @classmethod
    def encode(cls, value):
        """Encode {variable name: value} into the whole value of the setting."""
        if isinstance(value, str):
            return value
        if not isinstance(value, dict):
            raise ValueError("must be an object of variable name to value")
        return cls.separator.join(
            cls.assignment.join((str(name), encode_field(item, name)))
            for name, item in value.items()
        )
