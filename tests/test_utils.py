"""Test ``utils.py``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Iterable

import pytest
from cleo.io.buffered_io import BufferedIO
from poetry.core.packages.dependency import Dependency
from poetry.installation import Installer
from poetry.installation.executor import Executor as BaseExecutor

from poetry_plugin_constrain.utils import (
    Style,
    _patch_io_writes,
    deep_get,
    line,
    line_error,
    print_group_header,
    run_installer_update,
)

if TYPE_CHECKING:
    import sys

    from cleo.testers.application_tester import ApplicationTester
    from poetry.console.application import Application
    from poetry.core.packages.package import Package
    from poetry.installation.operations.operation import Operation
    from poetry.poetry import Poetry
    from poetry.utils.env import MockEnv
    from pytest_mock import MockerFixture

    if sys.version_info >= (3, 10):
        from typing import TypeAlias
    else:
        from typing_extensions import TypeAlias

    # See: https://github.com/python/mypy/issues/14158
    if sys.version_info < (3, 10):
        InstallerFactory: TypeAlias = 'Callable[[ApplicationTester, Poetry], Installer]'
        PoetryTesterFactory: TypeAlias = 'Callable[[Poetry], ApplicationTester]'
        PoetryFactory: TypeAlias = 'Callable[[Poetry], Application]'
        ProjectFactory: TypeAlias = 'Callable[[str | None], Poetry]'
    else:
        InstallerFactory: TypeAlias = Callable[[ApplicationTester, Poetry], Installer]
        PoetryTesterFactory: TypeAlias = Callable[[Poetry], ApplicationTester]
        PoetryFactory: TypeAlias = Callable[[Poetry], Application]
        ProjectFactory: TypeAlias = Callable[[str | None], Poetry]


class Executor(BaseExecutor):
    """Fake ``Executor` for testing.

    This class extends ``Executor`` by adding getters for the list of installed
    packages, up
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._installs: list[Package] = []
        self._updates: list[Package] = []
        self._uninstalls: list[Package] = []

    @property
    def installations(self) -> list[Package]:
        """Return the installed packages.

        Extends ``Executor`` by providing a getter for testing purposes. This property
        is set in the `_do_execute_operation()` method of this class.

        Returns
        -------
        list[Package]
            The list of installed packages
        """
        return self._installs

    @property
    def updates(self) -> list[Package]:
        """Return the updated packages.

        Extends ``Executor`` by providing a getter for testing purposes. This property
        is set in the `_do_execute_operation()` method of this class.

        Returns
        -------
        list[Package]
            The list of updated packages
        """
        return self._updates

    @property
    def removals(self) -> list[Package]:
        """Return the removed packages.

        Extends ``Executor`` by providing a getter for testing purposes. This property
        is set in the `_do_execute_operation()` method of this class.

        Returns
        -------
        list[Package]
            The list of removed packages
        """
        return self._uninstalls

    def _do_execute_operation(self, operation: Operation) -> int:
        """Extend the ``Executor._do_execute_operation()`` method.

        Extends the ``Executor`` method by recording the packages installed, updated,
        and removed so they may be queried by getters during testing.

        Parameters
        ----------
        operation : Operation
            The operation to be executed

        Returns
        -------
        int
            The (return) status code; 0 if successful, else non-zero
        """
        rc = super()._do_execute_operation(operation)

        if not operation.skipped:
            getattr(self, f'_{operation.job_type}s').append(operation.package)

        return rc

    def _execute_install(
        self,
        operation: Operation,  # noqa: ARG002  # Required signature of base method
    ) -> int:
        """Mock the ``_execute_install`` operation."""
        return 0

    def _execute_update(
        self,
        operation: Operation,  # noqa: ARG002  # Required signature of base method
    ) -> int:
        """Mock the ``_execute_update`` operation."""
        return 0

    def _execute_remove(
        self,
        operation: Operation,  # noqa: ARG002  # Required signature of base method
    ) -> int:
        """Mock the ``_execute_remove`` operation."""
        return 0


@pytest.fixture()
def installer_factory(
    env: MockEnv,
) -> InstallerFactory:
    """Create a new ``poetry`` installer.

    Parameters
    ----------
    tester : ApplicationTester
        A ``cleo`` fixture that returns a tester application instance
    poetry : Poetry
        A ``poetry`` application instance

    Returns
    -------
    InstallerFactory
       A ``poetry`` installer creator.
    """

    def _factory(
        tester: ApplicationTester,
        poetry: Poetry,
    ) -> Installer:
        return Installer(
            io=tester.io,
            env=env,
            package=poetry.package,
            locker=poetry.locker,
            pool=poetry.pool,
            config=poetry.config,
            executor=Executor(
                env,
                poetry.pool,
                poetry.config,
                tester.io,
            ),
        )

    return _factory


@pytest.fixture()
def io() -> BufferedIO:
    """Return a ``BufferedIO`` object for testing.

    Returns
    -------
    BufferedIO
        BufferedIO object
    """
    return BufferedIO()


def _silence(*args: Any, **kwargs: Any) -> None:  # noqa: ARG001
    """Silence write messages."""


def _update_messages_for_dry_run(
    write: Callable[..., None],
    message: str,
    **kwargs: Any,
) -> None:
    """Replace message terminology if command is run with ``dry-run``."""
    message = message.replace('Updating', 'Would update')
    message = message.replace('Installing', 'Checking')
    message = message.replace('Skipped', 'Would skip')

    return write(message, **kwargs)


@pytest.mark.parametrize(
    ('patch_function', 'message', 'expected_output'),
    [
        (
            _silence,
            'Updating cleo',
            '',
        ),
        (
            _update_messages_for_dry_run,
            'Updating cleo',
            'Would update cleo',
        ),
        (
            _update_messages_for_dry_run,
            'Installing cleo',
            'Checking cleo',
        ),
        (
            _update_messages_for_dry_run,
            'Skipped cleo',
            'Would skip cleo',
        ),
    ],
)
def test_patch_io_writes(
    io: BufferedIO,
    patch_function: Callable[..., None],
    message: str,
    expected_output: str,
) -> None:
    """Test the ``patch_io_writes`` function.

    Parameters
    ----------
    io : BufferedIO
        A ``poetry-plugin-constrain`` fixture that returns a ``BufferedIO`` instance.
    patch_function : Callable[..., None]
        The function to patch ``io.write`` and ``io.write_line`` calls with
    message : str
        The message to write
    expected_output : str
        The message expected to be printed to console with the patch function
    """
    with _patch_io_writes(io, patch_function):
        io.write(message)

    assert io.fetch_output() == expected_output


@pytest.mark.parametrize(
    ('data', 'path', 'expected_result'),
    [
        (
            {'a': {'b': {'c': (1, 2)}}},
            ['a', 'b', 'c'],
            (1, 2),
        ),
        (
            {'a': {'b': {'c': (1, 2)}}},
            ['x', 'y', 'z'],
            None,
        ),
    ],
)
def test_deep_get(
    data: dict,
    path: list[str],
    expected_result: Any,
) -> None:
    """Test the ``deep_get`` function.

    Parameters
    ----------
    data : dict
        The nested dictionary to search
    path : list[str]
        A list of keys representing the path to the desired value
    """
    assert deep_get(data, path) == expected_result


@pytest.mark.parametrize(
    ('message', 'style', 'expected_output'),
    [
        (
            'Hello World!\n',
            None,
            'Hello World!\n\n',
        ),
        (
            "Thanks for using 'poetry-plugin-constrain'!\n",
            Style.INFO,
            "Thanks for using 'poetry-plugin-constrain'!\n\n",
        ),
    ],
)
def test_line(
    io: BufferedIO,
    message: str,
    style: Style | None,
    expected_output: str,
) -> None:
    """Test the ``line`` function.

    Parameters
    ----------
    io : BufferedIO
        A ``poetry-plugin-constrain`` fixture that returns a ``BufferedIO`` instance.
    message : str
        The message to be printed.
    expected_output : str
        The expected output console message
    """
    line(io, message, style)

    assert io.fetch_output() == expected_output


@pytest.mark.parametrize(
    ('message', 'style', 'expected_output'),
    [
        (
            'ERROR: Danger Will Robinson!\n',
            None,
            'ERROR: Danger Will Robinson!\n\n',
        ),
        (
            'ERROR: These are not the droids you are looking for!\n',
            Style.ERROR,
            'ERROR: These are not the droids you are looking for!\n\n',
        ),
    ],
)
def test_line_error(
    io: BufferedIO,
    message: str,
    style: Style | None,
    expected_output: str,
) -> None:
    """Test the ``line_error`` function.

    Parameters
    ----------
    io : BufferedIO
        A ``poetry-plugin-constrain`` fixture that returns a ``BufferedIO`` instance.
    message : str
        The message to be printed.
    expected_output : str
        The expected output console message
    """
    line_error(io, message, style)

    assert io.fetch_error() == expected_output


@pytest.mark.parametrize(
    ('group', 'expected_header'),
    [
        ('test', "Group: 'test'\n=============\n"),
        ('doc', "Group: 'doc'\n============\n"),
        ('format', "Group: 'format'\n===============\n"),
        ('type', "Group: 'type'\n=============\n"),
    ],
)
def test_print_group_header(
    io: BufferedIO,
    group: str,
    expected_header: str,
) -> None:
    """Test the ``print_group_header`` function.

    Parameters
    ----------
    io : BufferedIO
        A ``poetry-plugin-constrain`` fixture that returns a ``BufferedIO`` instance for
        testing
    group : str
        The name of the dependency group
    expected_header : str
        The expected header to be printed to the console
    """
    print_group_header(io, group)

    assert io.fetch_output() == expected_header


@pytest.mark.parametrize('dry_run', [True, False])
@pytest.mark.parametrize('lockfile_only', [True, False])
@pytest.mark.parametrize('verbose', [True, False])
@pytest.mark.parametrize('silent', [True, False])
@pytest.mark.parametrize(
    'deps',
    [
        {
            'docs': [
                Dependency(name='Sphinx', constraint='>=3.10'),
            ],
            'main': [
                Dependency(name='python', constraint='>=3.8'),
                Dependency(name='foo', constraint='>=0.1.0'),
            ],
            'test': [
                Dependency(name='coverage', constraint='>=6.4'),
            ],
        },
    ],
)
def test_run_installer_update(
    poetry_tester_factory: PoetryTesterFactory,
    project_factory: ProjectFactory,
    installer_factory: InstallerFactory,
    mocker: MockerFixture,
    *,
    deps: dict[str, Iterable[Dependency]],
    silent: bool,
    verbose: bool,
    lockfile_only: bool,
    dry_run: bool,
) -> None:
    """Test the ``run_installer_update`` method.

    Parameters
    ----------
    poetry_tester_factory : PoetryTesterFactory
        A ``poetry_plugin_constrain`` fixture that creates a ``poetry``
        ``ApplicationTester`` instance.
    project_factory : ProjectFactory
        A ``poetry_plugin_constrain`` fixture that creates a ``poetry`` project.
    installer_factory : InstallerFactory
        _description_
    mocker: MockerFixture
        A ``pytest-mock`` fixture that creates a mock instance
    deps : dict[str, Iterable[Dependency]]
        Dictionary mapping from dependency group names to new_dependencies
    silent : bool
        Whether to run the update silently
    verbose : bool
        Whether to run the update in verbose mode
    lockfile_only : bool
        Whether to also lock the lockfile
    dry_run : bool
        Whether to run the update as a dry run
    """
    project = project_factory('test_constrain_command.toml')  # type: ignore[call-arg]
    poetry_tester = poetry_tester_factory(project)

    installer = installer_factory(  # type: ignore[call-arg]
        poetry_tester,
        project,
    )

    mocker.patch('poetry.installation.installer.Installer.update', return_value=0)

    _lock = mocker.patch('poetry.installation.installer.Installer.lock')

    mocker.patch('poetry.installation.installer.Installer.run', return_value=0)

    run_installer_update(
        poetry=project,
        installer=installer,
        dependencies_by_group=deps,
        poetry_config=project.pyproject.poetry_config,
        dry_run=dry_run,
        lockfile_only=lockfile_only,
        verbose=verbose,
        silent=silent,
    )

    assert installer.is_dry_run() if dry_run else not installer.is_dry_run()
    assert _lock.call_count == 1 if lockfile_only else _lock.call_count == 0
    assert installer.is_verbose() if verbose else not installer.is_verbose()
