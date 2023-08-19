"""Test the plugin command."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from poetry_plugin_constrain.commands import PRETTY_CONSTRAINT_TYPES, Error
from tests.helpers import print_output

DEBUG = False

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture

    from .conftest import PoetryTesterFactory, ProjectFactory


@pytest.mark.parametrize(
    ('argv', 'fixture_toml', 'expected_toml', 'expected_status_code'),
    [
        (
            'constrain',
            'test_constrain_command.toml',
            'test_constrain_command_expected.toml',
            0,
        ),
    ],
)
def test_constrain_modifies_pyproject_toml(
    poetry_tester_factory: PoetryTesterFactory,
    project_factory: ProjectFactory,
    fixture_dir: Path,
    argv: str,
    fixture_toml: str,
    expected_toml: str,
    expected_status_code: int,
) -> None:
    """Test the ``pyproject.toml`` output by the ``poetry constrain`` command.

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
    argv : str
        Commandline arguments
    fixture_toml : str
        The input ``pyproject.toml`` file fixture.
    expected_toml : str
        The expected ``pyproject.toml`` file after ``poetry constrain`` is run.
    expected_status_code : int
        The expected status code after ``poetry constrain`` is run.
    """
    project = project_factory(fixture_toml)
    poetry_tester = poetry_tester_factory(project)

    status_code = poetry_tester.execute(argv)

    if DEBUG:
        print_output(poetry_tester)

    assert status_code == expected_status_code

    constrained_pyproject_toml = project.file.path.read_text()
    expected_pyproject_toml = (fixture_dir / expected_toml).read_text()

    assert constrained_pyproject_toml == expected_pyproject_toml


@pytest.mark.parametrize(
    ('argv', 'fixture_toml', 'expected_toml', 'expected_status_code'),
    [
        (
            'constrain --dry-run',
            'test_constrain_command.toml',
            'test_constrain_command.toml',
            0,
        ),
    ],
)
def test_constrain_does_not_modify_pyproject_toml(
    poetry_tester_factory: PoetryTesterFactory,
    project_factory: ProjectFactory,
    fixture_dir: Path,
    argv: str,
    fixture_toml: str,
    expected_toml: str,
    expected_status_code: int,
) -> None:
    """Test the ``pyproject.toml`` output by the ``poetry constrain`` command.

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
    argv : str
        Commandline arguments
    fixture_toml : str
        The input ``pyproject.toml`` file fixture.
    expected_toml : str
        The expected ``pyproject.toml`` file after ``poetry constrain`` is run.
    expected_status_code : int
        The expected status code after ``poetry constrain`` is run.
    """
    project = project_factory(fixture_toml)
    poetry_tester = poetry_tester_factory(project)

    status_code = poetry_tester.execute(argv)

    if DEBUG:
        print_output(poetry_tester)

    assert status_code == expected_status_code

    constrained_pyproject_toml = project.file.path.read_text()
    expected_pyproject_toml = (fixture_dir / expected_toml).read_text()

    assert constrained_pyproject_toml == expected_pyproject_toml


@pytest.mark.parametrize(
    ('argv', 'fixture_toml', 'expected_error_message', 'expected_status_code'),
    [
        (
            'constrain --old pound',
            'test_constrain_command.toml',
            (
                "ERROR: 'old' constraint 'pound' is invalid. Please use one of the"
                f' following:\n{PRETTY_CONSTRAINT_TYPES}'
            ),
            Error.INVALID_OLD_CONSTRAINT,
        ),
        (
            'constrain --new pound',
            'test_constrain_command.toml',
            (
                "ERROR: 'new' constraint 'pound' is invalid. Please use one of the"
                f' following:\n{PRETTY_CONSTRAINT_TYPES}'
            ),
            Error.INVALID_NEW_CONSTRAINT,
        ),
    ],
)
def test_invalid_constraint_type_arguments(
    poetry_tester_factory: PoetryTesterFactory,
    project_factory: ProjectFactory,
    argv: str,
    fixture_toml: str,
    expected_error_message: str,
    expected_status_code: int,
) -> None:
    """Test invalid constraint arguments result in an error.

    Parameters
    ----------
    poetry_tester_factory : PoetryTesterFactory
        A ``poetry_plugin_constrain`` fixture that creates a ``poetry``
        ``ApplicationTester`` instance.
    project_factory : ProjectFactory
        A ``poetry_plugin_constrain`` fixture that creates a ``poetry`` project.
    argv : str
        Commandline arguments
    fixture_toml : str
        The input ``pyproject.toml`` file fixture.
    expected_error_message : str
        The expected error message emitted when the error is encountered.
    expected_status_code : int
        The expected status code after ``poetry constrain`` is run.
    """
    project = project_factory(fixture_toml)
    poetry_tester = poetry_tester_factory(project)

    status_code = poetry_tester.execute(argv)

    if DEBUG:
        print_output(poetry_tester)

    assert status_code == expected_status_code
    assert expected_error_message in poetry_tester.io.fetch_error()


@pytest.mark.parametrize(
    ('argv', 'fixture_toml', 'expected_error_message', 'expected_status_code'),
    [
        (
            'constrain',
            'test_no_dependencies.toml',
            "ERROR: No dependencies found in 'pyproject.toml'.",
            Error.NO_DEPENDENCIES_FOUND,
        ),
    ],
)
def test_no_dependencies_found(
    poetry_tester_factory: PoetryTesterFactory,
    project_factory: ProjectFactory,
    argv: str,
    fixture_toml: str,
    expected_error_message: str,
    expected_status_code: int,
) -> None:
    """Test that a ``pyproject.toml`` without dependencies results in an error.

    Parameters
    ----------
    poetry_tester_factory : PoetryTesterFactory
        A ``poetry_plugin_constrain`` fixture that creates a ``poetry``
        ``ApplicationTester`` instance.
    project_factory : ProjectFactory
        A ``poetry_plugin_constrain`` fixture that creates a ``poetry`` project.
    argv : str
        Commandline arguments
    fixture_toml : str
        The input ``pyproject.toml`` file fixture.
    expected_error_message : str
        The expected error message emitted when the error is encountered.
    expected_status_code : int
        The expected status code after ``poetry constrain`` is run.
    """
    project = project_factory(fixture_toml)
    poetry_tester = poetry_tester_factory(project)

    status_code = poetry_tester.execute(argv)

    if DEBUG:
        print_output(poetry_tester)

    assert status_code == expected_status_code
    assert expected_error_message in poetry_tester.io.fetch_error()


@pytest.mark.parametrize(
    ('argv', 'fixture_toml', 'expected_error_message', 'expected_status_code'),
    [
        (
            'constrain --update',
            'test_constrain_command.toml',
            (
                'ERROR: Poetry did not instantiate an installer for'
                " 'poetry-plugin-constrain'."
            ),
            Error.NO_INSTALLER_FOUND,
        ),
    ],
)
def test_no_installer_found(
    poetry_tester_factory: PoetryTesterFactory,
    project_factory: ProjectFactory,
    mocker: MockerFixture,
    argv: str,
    fixture_toml: str,
    expected_error_message: str,
    expected_status_code: int,
) -> None:
    """Test if the command has no installer that an error results.

    Parameters
    ----------
    poetry_tester_factory : PoetryTesterFactory
        A ``poetry_plugin_constrain`` fixture that creates a ``poetry``
        ``ApplicationTester`` instance.
    project_factory : ProjectFactory
        A ``poetry_plugin_constrain`` fixture that creates a ``poetry`` project.
    mocker: MockerFixture
        A ``pytest-mock`` fixture that creates a mock instance
    argv : str
        Commandline arguments
    fixture_toml : str
        The input ``pyproject.toml`` file fixture.
    expected_error_message : str
        The expected error message emitted when the error is encountered.
    expected_status_code : int
        The expected status code after ``poetry constrain`` is run.
    """
    project = project_factory(fixture_toml)
    poetry_tester = poetry_tester_factory(project)

    mocker.patch(
        'poetry_plugin_constrain.commands.ConstrainCommand.installer',
        new=None,
    )

    status_code = poetry_tester.execute(argv)

    if DEBUG:
        print_output(poetry_tester)

    assert status_code == expected_status_code
    assert expected_error_message in poetry_tester.io.fetch_error()


@pytest.mark.parametrize(
    ('argv', 'fixture_toml', 'expected_status_code'),
    [
        (
            'constrain --only foobar',
            'test_empty_group.toml',
            1,  # Returned from ``_validate_group_options()``
        ),
    ],
)
def test_non_existent_group(
    poetry_tester_factory: PoetryTesterFactory,
    project_factory: ProjectFactory,
    argv: str,
    fixture_toml: str,
    expected_status_code: int,
) -> None:
    """Test that a ``pyproject.toml`` with an empty group results in expected message.

    Parameters
    ----------
    poetry_tester_factory : PoetryTesterFactory
        A ``poetry_plugin_constrain`` fixture that creates a ``poetry``
        ``ApplicationTester`` instance.
    project_factory : ProjectFactory
        A ``poetry_plugin_constrain`` fixture that creates a ``poetry`` project.
    argv : str
        Commandline arguments
    fixture_toml : str
        The input ``pyproject.toml`` file fixture.
    expected_status_code : int
        The expected status code after ``poetry constrain`` is run.
    """
    project = project_factory(fixture_toml)
    poetry_tester = poetry_tester_factory(project)

    status_code = poetry_tester.execute(argv)

    if DEBUG:
        print_output(poetry_tester)

    assert status_code == expected_status_code


@pytest.mark.parametrize(
    ('argv', 'fixture_toml', 'expected_message', 'expected_status_code'),
    [
        (
            'constrain',
            'test_empty_group.toml',
            "Group 'test' has no dependencies.",
            0,
        ),
    ],
)
def test_empty_group(
    poetry_tester_factory: PoetryTesterFactory,
    project_factory: ProjectFactory,
    argv: str,
    fixture_toml: str,
    expected_message: str,
    expected_status_code: int,
) -> None:
    """Test that a ``pyproject.toml`` with an empty group results in expected message.

    Parameters
    ----------
    poetry_tester_factory : PoetryTesterFactory
        A ``poetry_plugin_constrain`` fixture that creates a ``poetry``
        ``ApplicationTester`` instance.
    project_factory : ProjectFactory
        A ``poetry_plugin_constrain`` fixture that creates a ``poetry`` project.
    argv : str
        Commandline arguments
    fixture_toml : str
        The input ``pyproject.toml`` file fixture.
    expected_message : str
        The expected message emitted when an empty group is encountered.
    expected_status_code : int
        The expected status code after ``poetry constrain`` is run.
    """
    project = project_factory(fixture_toml)
    poetry_tester = poetry_tester_factory(project)

    status_code = poetry_tester.execute(argv)

    if DEBUG:
        print_output(poetry_tester)

    assert status_code == expected_status_code
    assert expected_message in poetry_tester.io.fetch_output()
