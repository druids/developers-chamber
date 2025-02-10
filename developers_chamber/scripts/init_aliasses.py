import os
import json

from developers_chamber.scripts import cli
from developers_chamber.click.alias import AliasCommand


for k, v in json.loads(os.environ.get("ALIASES", "{}")).items():
    cli.add_command(
        AliasCommand(
            commands=v,
            name=k,
            context_settings=dict(ignore_unknown_options=True, allow_extra_args=True),
        )
    )
