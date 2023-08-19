"""Test the ``ConstrainCommand``."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest import mock

import pytest
from cleo.io.outputs.output import Verbosity

from tests.helpers import print_output

DEBUG = False
COMMANDS_NAMESPACE = 'poetry.console.commands'

if TYPE_CHECKING:

    from pytest_mock import MockerFixture

    from .conftest import PoetryTesterFactory, ProjectFactory


@pytest.mark.parametrize(
    ('argv', 'hook_argv'),
    [
        ('init', 'constrain'),
        ('init --name=test --description=dummy', 'constrain'),
        ('add foobar', 'constrain'),
        ('add foobar --dry-run', 'constrain --dry-run'),
        ('add foobar --lock', 'constrain --lock'),
        ('update', 'constrain'),
        ('update --dry-run', 'constrain --dry-run'),
        ('update --lock', 'constrain --lock'),
        ('update --only=baz', 'constrain --only baz'),
        ('update --without=buz', 'constrain --without buz'),
        ('check', 'constrain'),
        ('check --lock', 'constrain --lock'),
    ],
)
@pytest.mark.parametrize(
    'enable_post_hooks',
    [
        None,
        'Y',
        'Yes',
        't',
        'TRUE',
        'On',
        '1',
    ],
)
def test_post_hooks_called(
    poetry_tester_factory: PoetryTesterFactory,
    project_factory: ProjectFactory,
    mocker: MockerFixture,
    enable_post_hooks: str | None,
    argv: str,
    hook_argv: str,
) -> None:
    """Test that ``ConstrainCommand`` is called after a hook command is called.

    The hook can be any of:

        - ``init``
        - ``add``
        - ``update``
        - ``check``

    Parameters
    ----------
    poetry_tester_factory : PoetryTesterFactory
        A ``poetry_plugin_constrain`` fixture that creates a ``poetry``
        ``ApplicationTester`` instance.
    project_factory : ProjectFactory
        A ``poetry_plugin_constrain`` fixture that creates a ``poetry`` project.
    mocker: MockerFixture
        A ``pytest-mock`` fixture that creates a mock instance
    enable_post_hooks : str | None
        The plugin ``enable_post_hooks`` configuration
    argv : str
        Commandline arguments
    hook_argv : str
        Arguments passed to ``constrain`` when the hook is called
    """
    _environ = (
        {
            'POETRY_PLUGIN_CONSTRAIN_ENABLE_POST_HOOKS': enable_post_hooks,
        }
        if enable_post_hooks
        else {}
    )

    with mock.patch.dict('os.environ', _environ):
        _cmd_name = argv.split(' ')[0]
        _cmd_class = _cmd_name.title() + 'Command'

        mocker.patch(
            f'{COMMANDS_NAMESPACE}.{_cmd_name}.{_cmd_class}.handle',
            return_value=0,
        )
        mock_run_with = mocker.patch(
            'poetry_plugin_constrain.plugins.ConstrainPlugin._run_with',
        )

        project = project_factory()  # type: ignore[call-arg]
        poetry_tester = poetry_tester_factory(project)

        poetry_tester.execute(
            args=argv,
            interactive=False,
        )

        if DEBUG:
            print_output(poetry_tester)

        mock_run_with.assert_called_once_with(poetry_tester.application, hook_argv)


@pytest.mark.parametrize(
    ('argv', 'debug_message'),
    [
        ('constrain', ''),
        ('constrain --lock', ''),
        ('constrain --check', ''),
        ('constrain --dry-run', ''),
        ('constrain --only foo', ''),
        ('constrain --without buz', ''),
        ('constrain --glarp', ''),
        (
            'init --glarp',
            "Skip 'poetry-constrain' post-hook due to 'poetry init' non-zero exit "
            'code.',
        ),
        (
            'about',
            "Skip 'poetry-constrain' post-hook since command is not 'init', 'add',"
            " 'check', or 'update'.",
        ),
    ],
)
@pytest.mark.parametrize(
    'enable_post_hooks',
    [
        None,
        'Y',
        'Yes',
        't',
        'TRUE',
        'On',
        '1',
    ],
)
def test_post_hooks_not_called(
    poetry_tester_factory: PoetryTesterFactory,
    project_factory: ProjectFactory,
    mocker: MockerFixture,
    enable_post_hooks: str | None,
    argv: str,
    debug_message: str,
) -> None:
    """Test the command does not constrain versions when disabled.

    Parameters
    ----------
    poetry_tester_factory : PoetryTesterFactory
        A ``poetry_plugin_constrain`` fixture that creates a ``poetry``
        ``ApplicationTester`` instance.
    project_factory : ProjectFactory
        A ``poetry_plugin_constrain`` fixture that creates a ``poetry`` project.
    fixture_dir : Path
        A ``poetry_plugin_constrain`` fixture that returns the ``Path`` to the
        ``pyproject.toml`` file fixtures.
    mocker: MockerFixture
        A ``pytest-mock`` fixture that creates a mock instance
    enable_post_hooks : str | None
        The plugin ``enable_post_hooks`` configuration
    argv : str
        Commandline arguments
    debug_message : str
        The expected debug message
    """
    _environ = (
        {
            'POETRY_PLUGIN_CONSTRAIN_ENABLE_POST_HOOKS': enable_post_hooks,
        }
        if enable_post_hooks
        else {}
    )

    with mock.patch.dict('os.environ', _environ):
        _cmd_name = argv.split(' ')[0]

        if _cmd_name != 'constrain':
            _cmd_class = _cmd_name.title() + 'Command'

            mocker.patch(
                f'{COMMANDS_NAMESPACE}.{_cmd_name}.{_cmd_class}.handle',
                return_value=0,
            )

        mock_run_with = mocker.patch(
            'poetry_plugin_constrain.plugins.ConstrainPlugin._run_with',
        )

        project = project_factory()  # type: ignore[call-arg]
        poetry_tester = poetry_tester_factory(project)

        poetry_tester.execute(
            args=argv,
            interactive=False,
            verbosity=Verbosity.DEBUG,
        )

        if DEBUG:
            print_output(poetry_tester)

        assert debug_message in poetry_tester.io.fetch_output()
        assert mock_run_with.call_count == 0


@pytest.mark.parametrize(
    'argv',
    [
        'init',
        'init --name=test --description=dummy',
        'init --glarp',
        'add foobar',
        'add foobar --dry-run',
        'add foobar --lock',
        'update',
        'update --dry-run',
        'update --lock',
        'update --only=baz',
        'update --without=buz',
        'check',
        'check --lock',
        'about',
    ],
)
@pytest.mark.parametrize(
    'enable_post_hooks',
    [
        'N',
        'No',
        'f',
        'FALSE',
        'oFf',
        '0',
    ],
)
def test_post_hooks_disabled_with_environment_variable(
    poetry_tester_factory: PoetryTesterFactory,
    project_factory: ProjectFactory,
    mocker: MockerFixture,
    enable_post_hooks: str | None,
    argv: str,
) -> None:
    """Test the command does not constrain versions when the plugin is disabled.

    Parameters
    ----------
    poetry_tester_factory : PoetryTesterFactory
        A ``poetry_plugin_constrain`` fixture that creates a ``poetry``
        ``ApplicationTester`` instance.
    project_factory : ProjectFactory
        A ``poetry_plugin_constrain`` fixture that creates a ``poetry`` project.
    fixture_dir : Path
        A ``poetry_plugin_constrain`` fixture that returns the ``Path`` to the
        ``pyproject.toml`` file fixtures.
    mocker: MockerFixture
        A ``pytest-mock`` fixture that creates a mock instance
    enable_post_hooks : str | None
        The plugin ``enable_post_hooks`` configuration
    argv : str
        Commandline arguments
    """
    _environ = (
        {
            'POETRY_PLUGIN_CONSTRAIN_ENABLE_POST_HOOKS': enable_post_hooks,
        }
        if enable_post_hooks
        else {}
    )

    with mock.patch.dict('os.environ', _environ):
        _cmd_name = argv.split(' ')[0]
        _cmd_class = _cmd_name.title() + 'Command'

        mocker.patch(
            f'{COMMANDS_NAMESPACE}.{_cmd_name}.{_cmd_class}.handle',
            return_value=0,
        )

        mock_run_with = mocker.patch(
            'poetry_plugin_constrain.plugins.ConstrainPlugin._run_with',
        )

        project = project_factory()  # type: ignore[call-arg]
        poetry_tester = poetry_tester_factory(project)

        poetry_tester.execute(
            args=argv,
            interactive=False,
            verbosity=Verbosity.DEBUG,
        )

        if DEBUG:
            print_output(poetry_tester)

        debug_message = (
            "Skip 'poetry-constrain' post-hook since post-hooks disabled by user."
        )

        assert debug_message in poetry_tester.io.fetch_output()
        assert mock_run_with.call_count == 0
