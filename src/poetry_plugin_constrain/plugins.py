"""Constrain dependency versions in the ``pyproject.toml`` file using specified format."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from cleo.events import console_events
from cleo.events.console_terminate_event import ConsoleTerminateEvent
from cleo.io.inputs.string_input import StringInput
from cleo.io.outputs.output import Verbosity
from poetry.console.application import Application
from poetry.console.commands.add import AddCommand
from poetry.console.commands.check import CheckCommand
from poetry.console.commands.init import InitCommand
from poetry.console.commands.update import UpdateCommand
from poetry.plugins.application_plugin import ApplicationPlugin

from poetry_plugin_constrain.commands import ConstrainCommand
from poetry_plugin_constrain.config import are_post_hooks_enabled
from poetry_plugin_constrain.utils import Style, line

if TYPE_CHECKING:
    from cleo.events.event import Event
    from cleo.events.event_dispatcher import EventDispatcher
    from poetry.console.commands.command import Command

POST_HOOK_COMMANDS = [
    'init',
    'add',
    'check',
    'update',
]

OPTIONS = [opt.name for opt in ConstrainCommand.options]


class ConstrainPlugin(ApplicationPlugin):
    """Constrain dependency versions using a specified format."""

    @property
    def commands(self) -> list[type[Command]]:
        """Commands to register in the command loader.

        ``poetry.ApplicationPlugin`` instances take each ``cleo`` command listed in the
        ``commands`` property and register them with the ``application.command_loader``.

        Returns
        -------
        list[type[Command]]
            The commands registered for the plugin
        """
        return [ConstrainCommand]

    def activate(self, application: Application) -> None:
        """Activate the plugin.

        When the ``poetry.PluginManager`` is ``activate``d (either in
        ``poetry/factory.py`` or ``poetry/console/application.py``), it activates each
        plugin in the ``"poetry.application.plugin"`` group. (See ``python``'s builtin
        ``importlib.metadata`` for more.)

        Parameters
        ----------
        application : Application
            The activated console application
        """
        assert application.event_dispatcher is not None
        application.event_dispatcher.add_listener(
            console_events.TERMINATE,
            self._constrain_hook,
        )
        super().activate(application)

    def _constrain_hook(
        self,
        event: Event,
        event_name: str,  # noqa: ARG002; Required to implement ``Listener``
        dispatcher: EventDispatcher,  # noqa: ARG002; Required to implement ``Listener``
    ) -> None:
        """Post-hook for constrain command.

        This method is called after any of the following ``poetry`` commands are called:

          - ``poetry init``
          - ``poetry add``
          - ``poetry check``
          - ``poetry update``

        The user can disable any of these hooks by adding a table
        ``[tool.poetry-plugin-constrain]`` to the ``pyproject.toml`` file and setting the
        following variables to ``false``:

          - ``post-init-hook``
          - ``post-add-hook``
          - ``post-check-hook``
          - ``post-update-hook``

        all hooks can be simultaneously disabled by setting the following to ``false``:

          - ``enable-post-hooks``

        Alternatively, all of these options are available as environment variables.
        Setting any of these to a non-zero value will have the same effect as setting the
        correpsonding values in the ``pyproject.toml`` file:

          - ``POETRY_PLUGIN_CONSTRAIN_POST_INIT_HOOK``
          - ``POETRY_PLUGIN_CONSTRAIN_POST_ADD_HOOK``
          - ``POETRY_PLUGIN_CONSTRAIN_POST_CHECK_HOOK``
          - ``POETRY_PLUGIN_CONSTRAIN_POST_UPDATE_HOOK``
          - ``POETRY_PLUGIN_CONSTRAIN_POST_ENABLE_POST_HOOKS``

        By default, all post hooks are enabled. Individual hook options take precedence
        over the ``enable-post-hooks`` and
        ``POETRY_PLUGIN_CONSTRAIN_POST_ENABLE_POST_HOOKS`` options so that if you prefer
        to disable, say, all but the ``post-check-hook``, this could be accomplished as
        follows:

        ```toml
        [tool.poetry-plugin-constrain]
        enable-post-hooks = false
        post-check-hook = true
        ```

        Parameters
        ----------
        event : ConsoleTerminateEvent
            The ``poetry`` event that triggered the hook.
        event_name : str
            The name of the event.
        dispatcher : EventDispatcher
            The ``cleo`` application event dispatcher
        """
        assert isinstance(event, ConsoleTerminateEvent)
        io = event.io
        command = event.command

        _skip_hook = "Skip 'poetry-constrain' post-hook"

        if isinstance(command, ConstrainCommand) or not hasattr(command, 'poetry'):
            return

        if not are_post_hooks_enabled(command.poetry):
            line(
                io=io,
                message=f'{_skip_hook} since post-hooks disabled by user.',
                style=Style.INFO,
                verbosity=Verbosity.DEBUG,
            )
            return

        if event.exit_code != 0:
            line(
                io=io,
                message=(
                    f"{_skip_hook} due to 'poetry {command.name}' non-zero exit code."
                ),
                style=Style.INFO,
                verbosity=Verbosity.DEBUG,
            )
            return

        if not isinstance(
            command,
            (InitCommand, AddCommand, CheckCommand, UpdateCommand),
        ):
            commands = [f"'{cmd}'" for cmd in POST_HOOK_COMMANDS]
            line(
                io=io,
                message=(
                    f'{_skip_hook} since command is not'
                    f" {', '.join(commands[:-1])}, or {commands[-1]}."
                ),
                style=Style.INFO,
                verbosity=Verbosity.DEBUG,
            )
            return

        # Grab relevant options from ``poetry`` commands that we transfer to the
        # ``constrain`` command
        dry_run = command.option('dry-run') if io.input.has_option('dry-run') else False

        check = command.option('check') if isinstance(command, CheckCommand) else False
        lock = command.option('lock') if io.input.has_option('lock') else False
        only = ','.join(command.option('only')) if io.input.has_option('only') else None
        without = (
            ','.join(command.option('without'))
            if io.input.has_option('without')
            else None
        )

        argv = (
            'constrain'
            f"{' --check' if check else ''}"
            f"{' --dry-run' if dry_run else ''}"
            f"{' --lock' if lock else ''}"
            f"{f' --only {only}' if only else ''}"
            f"{f' --without {without}' if without else ''}"
        )

        poetry = cast(Application, command.application)

        self._run_with(poetry, argv)

    def _run_with(
        self,
        poetry: Application,
        argv: str,
    ) -> None:  # pragma: no cover
        """Run ``poetry`` with provided input arguments.

        Parameters
        ----------
        poetry : Application
            The ``poetry`` application
        argv : str
            The input arguments
        """
        io = poetry.create_io(input=StringInput(argv))

        poetry._run(io)
