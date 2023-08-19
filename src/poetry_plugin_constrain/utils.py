"""Utility functions for the plugin."""

from __future__ import annotations

import re
from contextlib import contextmanager, suppress
from copy import copy
from enum import Enum
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Generator, Iterable, cast

from cleo.io.outputs.output import Verbosity
from poetry.core.constraints.version import VersionConstraint

if TYPE_CHECKING:
    from cleo.io.io import IO
    from poetry.core.packages.dependency import Dependency
    from poetry.installation.installer import Installer
    from poetry.poetry import Poetry

CONSTRAINT_TYPES: dict[str, str] = {
    'caret': '^',
    'tilde': '~',
    'ne': '!=',
    'ge': '>=',
    'gt': '>',
    'le': '<=',
    'lt': '<',
    'exact': '==',
}


class Style(str, Enum):
    ERROR: str = 'error'
    INFO: str = 'info'
    COMMENT: str = 'comment'
    QUESTION: str = 'question'
    C1: str = 'c1'
    C2: str = 'c2'
    B: str = 'b'


# This following have been copied from ``poetry-relax``:
# https://github.com/zanieb/poetry-relax/blob/main/src/poetry_relax/_core.py
#
#   - AND_CONSTRAINT_SEPARATORS
#   - OR_CONSTRAINT_SEPARATORS
#   - _patch_io_writes
#   - run_installer_update
#   - mutate_constraint

AND_CONSTRAINT_SEPARATORS = re.compile(r'((?<!^)(?<![~=>< ,]) *(?<!-)[, ](?!-) *(?!,|$))')
OR_CONSTRAINT_SEPARATORS = re.compile(r'(\s*\|\|?\s*)')


@contextmanager
def _patch_io_writes(
    io: IO,  # pylint: disable=C0103
    patch_function: Callable,
) -> Generator[None, None, None]:
    """Patches writes to the given IO object to call the ``patch_function``.

    Parameters
    ----------
    io : IO
        The ``cleo`` io object.
    patch_function : Callable
        The function with which to monkeypatch the ``io`` write calls.
    """
    write_line = io.write_line
    write = io.write

    io.write_line = partial(patch_function, write_line)  # type: ignore[method-assign]
    io.write = partial(patch_function, write)  # type: ignore[method-assign]

    try:
        yield
    finally:
        io.write_line = write_line  # type: ignore[method-assign]
        io.write = write  # type: ignore[method-assign]


def run_installer_update(
    poetry: Poetry,
    installer: Installer,
    dependencies_by_group: dict[str, Iterable[Dependency]],
    poetry_config: dict[Any, Any],
    *,
    dry_run: bool,
    lockfile_only: bool,
    verbose: bool,
    silent: bool,
) -> int:
    """Run ``poetry`` installer update.

    Ensures existing dependencies in given groups are replaced with the new ones and are
    whitelisted to be updated during locking.

    Parameters
    ----------
    poetry : Poetry
        The poetry application
    installer : Installer
        The installer for the poetry application
    dependencies_by_group : dict[str, Iterable[Dependency]]
        Dictionary of dependency lists keyed by group name
    poetry_config : dict[Any, Any]
        The contents of the ``[tool.poetry]`` table of the ``pyproject.toml``
    dry_run : bool
        Whether or not this command is run as a dry run
    lockfile_only : bool
        Whether or not to lock the lockfile after running this command
    verbose : bool
        Whether or not to run this command in verbose mode
    silent : bool
        Whether or not to run this command in silent mode

    Returns
    -------
    int
        0 if the command runs successfully, non-zero otherwise.
    """
    whitelist: list[str] = []

    for group_name, dependencies in dependencies_by_group.items():
        group = poetry.package.dependency_group(group_name)

        for dependency in dependencies:
            with suppress(ValueError):
                group.remove_dependency(dependency.name)
            group.add_dependency(dependency)

            whitelist.extend(dependency.name)

    installer.whitelist(whitelist)

    # Refresh the locker
    poetry.set_locker(poetry.locker.__class__(poetry.locker.lock, poetry_config))

    installer.set_locker(poetry.locker)
    installer.only_groups(dependencies_by_group.keys())
    installer.set_package(poetry.package)
    installer.dry_run(dry_run)
    installer.verbose(verbose)

    installer.update()

    if lockfile_only:
        installer.lock()

    def _update_messages_for_dry_run(
        write: Callable[..., None],
        message: str,
        **kwargs: Any,
    ) -> None:  # pragma: no cover
        if dry_run:
            message = message.replace('Updating', 'Would update')
            message = message.replace('Installing', 'Checking')
            message = message.replace('Skipped', 'Would skip')

        return write(message, **kwargs)

    def _silence(*args: Any, **kwargs: Any) -> None:  # noqa: ARG001  # pragma: no cover
        pass

    _cmd: Callable
    if silent:  # noqa: SIM108  # See ``mypy`` issue 14661
        _cmd = _silence
    else:
        _cmd = _update_messages_for_dry_run

    with _patch_io_writes(
        installer._io,
        _cmd,
    ):
        return installer.run()


def mutate_constraint(
    constraints: str,
    callback: Callable[[str], str],
) -> str:
    """Parse constraints, replace with callback results, and rejoin into original string.

    Given a string of constraints, parse into single constraints, replace each one with
    the result of `callback`, then join into the original constraint string.

    Attempts to support modification of parts of constraint strings with minimal
    changes to the original format.

    Trailing and leading whitespace will be stripped.

    Parameters
    ----------
    constraints : str
        The version constraints to mutate.
    callback : Callable[[str], str]
        The method used to mutate the provided ``constraints``

    Returns
    -------
    str
        The mutated constraint
    """
    # If the poetry helpers were used to parse the constraints, the user's constraints
    # can be modified which can be undesirable. For example, ">2.5,!=2.7" would be
    # changed to ">2.5,<2.7 || > 2.7".
    if constraints == '*':
        return callback(constraints)

    # Parse _or_ expressions first
    or_constraints = re.split(OR_CONSTRAINT_SEPARATORS, constraints.strip())

    # NOTE: A capture group was used so ``re.split`` returns the captured separators.
    # We need these to rejoin the string after callbacks are performed. It's easiest to
    # just mutate the lists rather than performing fancy zips
    for i in range(0, len(or_constraints), 2):
        # Parse _and_ expressions
        and_constraints = re.split(
            AND_CONSTRAINT_SEPARATORS,
            # Trailing `,` allowed but not retained — following Poetry internals
            or_constraints[i].rstrip(',').strip(),
        )

        # If there are no _and_ expressions, this will still be called once
        for j in range(0, len(and_constraints), 2):
            and_constraints[j] = callback(and_constraints[j])

        or_constraints[i] = ''.join(and_constraints)

    return ''.join(or_constraints)


def _replace_constraint(
    constraint: str,
    old: str = 'caret',
    new: str = 'ge',
) -> str:
    """Replace ``poetry`` default constraint string with new method.

    Parameters
    ----------
    constraint : str
        The version constraint string
    old : str, optional
        The constraint to search for, by default 'caret'
    new : str, optional
        The constraint to replace ``old``, by default 'ge'

    Note
    ----
    ``ConstrainCommand.handle()`` checks if the ``old`` or ``new`` constraints are
    invalid before they are passed to this function. This is done so the command can
    output a user-friendly error message and return a non-zero exit code.

    Returns
    -------
    str
        The modified version constraint string
    """
    old_marker = CONSTRAINT_TYPES[old]
    new_marker = CONSTRAINT_TYPES[new]

    if constraint.startswith(old_marker):
        return constraint.replace(old_marker, new_marker, 1)

    return constraint


def replace_constraint_from_dependency(
    dependency: Dependency,
    old: str = 'caret',
    new: str = 'ge',
) -> Dependency:
    """Replace the old constraint for the dependency with new one.

    Parameters
    ----------
    dependency : Dependency
        The dependency to update
    old : str, optional
        The old version constraint, by default 'caret'
    new : str, optional
        The new version constraint, by default 'ge'

    Returns
    -------
    Dependency
        The modified dependency
    """
    new_version = mutate_constraint(
        dependency.pretty_constraint,
        partial(_replace_constraint, old=old, new=new),
    )

    # Copy to retain as much info as possible
    new_dependency = copy(dependency)

    # The ``Dependency`` property setter parses this into a proper constraint type
    new_dependency.constraint = cast(VersionConstraint, new_version)

    return new_dependency


def deep_get(data: dict, path: list[str]) -> Any:
    """Get the value from a nested dictionary at the end of a list of keys.

    Since dictionaries return a ``KeyError`` if a key doesn't exist, ``get`` is often
    used to return a default value instead. However, serialization language data (e.g.
    TOML, JSON, YAML, XML, etc.) is read into Python as nested dictionaries, requiring
    multiple calls to ``get``.

    This function traverses a nested dictionary to retrieve a value using a list of keys
    that represent the path to the desired value.

    Args
    ----
        data (dict): The nested dictionary to search
        path (list[str]): A list of keys representing the path to the desired value

    Returns
    -------
        Any: The value at the path, or ``None`` if the path is not found.

    Examples
    --------
        >>> data = {'a': {'b': {'c': (1, 2)}}}
        >>> result = deep_get(data, ['a', 'b', 'c'])
        >>> print(result)
        (1, 2)

        >>> result = deep_get(data, ['x', 'y', 'z'])
        >>> print(result)
        None
    """
    for key in path:
        data = data.get(key, None)
        if data is None:
            return None

    return data


def line(
    io: IO,  # pylint: disable=C0103
    message: str,
    style: Style | None = None,
    verbosity: Verbosity = Verbosity.NORMAL,
) -> None:
    """Print ``cleo`` messages like ``cleo.commands.command.line``."""
    styled = f'<{style}>{message}</>' if style else message

    io.write_line(
        styled,
        verbosity=verbosity,
    )


def line_error(
    io: IO,  # pylint: disable=C0103
    message: str,
    style: Style | None = None,
    verbosity: Verbosity = Verbosity.NORMAL,
) -> None:
    """Print ``cleo`` messages like ``cleo.commands.command.line_error``."""
    styled = f'<{style}>{message}</>' if style else message

    io.write_error_line(
        styled,
        verbosity=verbosity,
    )


def print_group_header(
    io: IO,  # pylint: disable=C0103
    group: str,
) -> None:
    """Pretty print the group name using ``cleo`` semantics."""
    title = f'Group: <c1>{group!r}</c1>'
    title_no_tags = re.sub(r'<.*?>', '', title)

    io.write_line(title)
    io.write_line('=' * len(title_no_tags))
