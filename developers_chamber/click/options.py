import click


class RequiredIfNotEmpty(click.Option):

    def __init__(self, *args, **kwargs):
        self.required_if_not_empty = kwargs.pop('required_if_empty')
        if not self.required_if_not_empty:
            raise ValueError('"required_if_not_empty" argument is required for "RequiredIfNotEmpty" option')
        kwargs['help'] += ' NOTE: This option is required with {}'.format(self.required_if_not_empty)

        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.required_if_not_empty in opts:
            if self.name not in opts:
                raise click.UsageError(
                    'Illegal usage: {} is required with {}'.format(self.name, self.required_if_not_empty)
                )
            else:
                self.prompt = None

        return super().handle_parse_result(ctx, opts, args)


class ContainerDirToCopyType(click.ParamType):

    def convert(self, value, param, ctx):
        try:
            container_name, container_dir, host_dir = value.split(':')
            return container_name, container_dir, host_dir
        except ValueError:
            self.fail(
                'Invalid value "{}" format must be "DOCKER_CONTAINER_NAME:CONTAINER_DIRECTORY:HOST_DIRECTORY"'.format(
                    value
                ),
                param,
                ctx,
            )


class ContainerCommandType(click.ParamType):

    def convert(self, value, param, ctx):
        try:
            container_name, command = value.split(':')
            return container_name, command
        except ValueError:
            self.fail(
                'Invalid value "{}" format must be "DOCKER_CONTAINER_NAME:COMMAND"'.format(
                    value
                ),
                param,
                ctx,
            )
