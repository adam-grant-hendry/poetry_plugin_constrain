"""Implements the version constraining functionality of the plugin."""

# The implementation herein is in heavily inspired by the ``poetry-relax`` and
# ``poetry-plugin-sort`` poetry plugins and depends heavily on the internal
# machinery of ``poetry``. To date, these packages are licensed under the MIT
# license. Their repositories may be found here:
#
# poetry: https://github.com/python-poetry/poetry/tree/master
# poetry-relax: https://github.com/zanieb/poetry-relax/tree/main
# poetry-plugin-sort: https://github.com/andrei-shabanski/poetry-plugin-sort/blob/main/poetry_plugin_sort/plugins.py

from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from cleo.helpers import option
from cleo.io.outputs.output import Verbosity
from poetry.console.commands.installer_command import InstallerCommand
from poetry.core.factory import Factory
from poetry.core.packages.dependency_group import MAIN_GROUP

from poetry_plugin_constrain.config import get_config_variable
from poetry_plugin_constrain.utils import (
    CONSTRAINT_TYPES,
    Style,
    deep_get,
    line,
    line_error,
    print_group_header,
    replace_constraint_from_dependency,
    run_installer_update,
)

if TYPE_CHECKING:
    from cleo.io.inputs.option import Option
    from poetry.core.packages.dependency import Dependency


class Error(IntEnum):
    INVALID_OLD_CONSTRAINT: int = 1
    INVALID_NEW_CONSTRAINT: int = 2
    NO_DEPENDENCIES_FOUND: int = 3
    NO_INSTALLER_FOUND: int = 4
    INSTALLER_UPDATE_FAILED: int = 5


PRETTY_CONSTRAINT_TYPES = '\n'.join(
    f"-'{key}' ({value})" for key, value in CONSTRAINT_TYPES.items()
)


class ConstrainCommand(InstallerCommand):
    """Command to check the version constraints in ``pyproject.toml``."""

    # Inherit from ``InstallerCommand`` (_not_ ``InstallCommand``) to get the
    # ``installer`` property.

    name = 'constrain'
    description = (
        'Constrain dependency versions in <comment>pyproject.toml</> using a given'
        ' method.'
    )

    options: list[Option] = [  # noqa: RUF012  # Instance variable in `Command`
        option(
            'old',
            flag=False,
            default='caret',
            description=f"""The constraint to replace. Must be one of:
{PRETTY_CONSTRAINT_TYPES}""",
        ),
        option(
            'new',
            flag=False,
            default='ge',
            description=f"""The constraint to replace the old one with. Must be one of:
{PRETTY_CONSTRAINT_TYPES}""",
        ),
        option(
            'replace-all',
            flag=True,
            description=(
                "Replace all occurrences of 'to-replace' constraint, else only the first"
                ' and only if the version string begins with it.\n'
            ),
        ),
        option(
            'only',
            flag=False,
            multiple=True,
            description=(
                "Only constrain these groups. When specified, '--without' is ignored."
            ),
        ),
        option(
            'without',
            flag=False,
            multiple=True,
            description="Don't constrain these groups.",
        ),
        option(
            'dry-run',
            flag=True,
            description="Don't format pyproject.toml, just check constraints.",
        ),
        option(
            'update',
            flag=True,
            description="Run 'update' after changing constraints.",
        ),
        option(
            'lock',
            flag=True,
            description="Run 'lock' after changing constraints.",
        ),
        option(
            'check',
            flag=True,
            description="Run 'check' after changing constraints.",
        ),
    ]

    examples = """Examples
  $ poetry constrain  # ^2.0.1 --> >=2.0.1
  $ poetry constrain --dry-run
"""

    help = f"""\
The <b>constrain</b> command replaces the default dependency version constraining method\
 in <b>poetry</b> (caret "^") with one of your choosing.

{examples}
"""  # noqa: A003

    def handle(self) -> int:
        """Constrain versions using user-provided method.

        Returns
        -------
          int
            0 if executes successfully, else non-zero.
        """
        return self._constrain()

    def _constrain(self) -> int:  # noqa: C901; TODO: Split into helper functions
        _old = self.option('old') or get_config_variable(
            poetry=self.poetry,
            toml_var_name='old',
            default='caret',
        )
        _new = self.option('new') or get_config_variable(
            poetry=self.poetry,
            toml_var_name='new',
            default='ge',
        )
        _only = self.option('only') or get_config_variable(
            poetry=self.poetry,
            toml_var_name='only',
            default=set(),
        )
        _without = self.option('not') or get_config_variable(
            poetry=self.poetry,
            toml_var_name='without',
            default=set(),
        )
        _dry_run = self.option('dry-run') or get_config_variable(
            poetry=self.poetry,
            toml_var_name='dry-run',
            default=False,
        )
        _update = self.option('update') or get_config_variable(
            poetry=self.poetry,
            toml_var_name='update',
            default=False,
        )
        _lock = self.option('lock') or get_config_variable(
            poetry=self.poetry,
            toml_var_name='lock',
            default=False,
        )
        _check = self.option('check') or get_config_variable(
            poetry=self.poetry,
            toml_var_name='check',
            default=False,
        )

        if _old not in CONSTRAINT_TYPES:
            line_error(
                io=self.io,
                message=(
                    f"ERROR: 'old' constraint '{_old}' is invalid. Please use one of the"
                    f' following:\n'
                    f'{PRETTY_CONSTRAINT_TYPES}'
                ),
                style=Style.ERROR,
            )
            return Error.INVALID_OLD_CONSTRAINT

        if _new not in CONSTRAINT_TYPES:
            line_error(
                io=self.io,
                message=(
                    f"ERROR: 'new' constraint '{_new}' is invalid. Please use one of the"
                    f' following:\n'
                    f'{PRETTY_CONSTRAINT_TYPES}'
                ),
                style=Style.ERROR,
            )
            return Error.INVALID_NEW_CONSTRAINT

        pyproject = self.poetry.pyproject

        line(
            io=self.io,
            message=f"Using pyproject.toml: '{pyproject.path}'",
            style=Style.INFO,
            verbosity=Verbosity.VERBOSE,
        )

        poetry_config = pyproject.poetry_config

        # Returns 1 if any group not found
        self._validate_group_options(
            {
                'only': _only if _only else set(),
                'without': _without if _without else set(),
            },
        )

        groups = [
            str(group)
            for group in (
                _only
                or sorted(
                    self.poetry.package.dependency_group_names(include_optional=True),
                )
            )
            if group not in _without
        ]

        if not groups:
            line_error(
                io=self.io,
                message="ERROR: No dependencies found in 'pyproject.toml'.",
                style=Style.ERROR,
            )
            return Error.NO_DEPENDENCIES_FOUND

        updated_dependencies: dict[str, list[tuple[str, Dependency]]] = {}

        for group in groups:
            line(
                io=self.io,
                message=f'Checking constraints in group <c1>{group!r}</c1>...',
            )

            if group == MAIN_GROUP:  # pylint: disable=W0160
                group_dependencies_config = poetry_config.get('dependencies')
            else:
                group_dependencies_config = deep_get(
                    poetry_config,
                    ['group', group, 'dependencies'],
                )

            assert group_dependencies_config is not None

            dependencies: list[Dependency] = []
            for name, constraints in group_dependencies_config.items():
                # Support multiple constraint dependencies
                _constraints = (
                    constraints if isinstance(constraints, list) else [constraints]
                )

                for _constraint in _constraints:
                    dependencies.append(  # noqa: PERF401
                        Factory.create_dependency(name, _constraint),
                    )

            if not dependencies:
                line(
                    io=self.io,
                    message=f'Group <c1>{group!r}</c1> has no dependencies.',
                )
                updated_dependencies[group] = []
                continue

            line(
                io=self.io,
                message=(
                    f'Found {len(dependencies)} dependencies in group <c1>{group!r}'
                    '</c1>'
                ),
                style=Style.INFO,
                verbosity=Verbosity.VERBOSE,
            )

            new_dependencies = [
                replace_constraint_from_dependency(
                    dependency=dependency,
                    old=_old,
                    new=_new,
                )
                for dependency in dependencies
            ]

            updated_dependencies[group] = [
                (old_dependency.pretty_constraint, new_dependency)
                for old_dependency, new_dependency in zip(dependencies, new_dependencies)
                if old_dependency.pretty_constraint != new_dependency.pretty_constraint
            ]

            line(
                io=self.io,
                message=(
                    f'Proposing updates to {len(updated_dependencies[group])}'
                    f' dependencies in group <c1>{group!r}</c1>'
                ),
                style=Style.INFO,
                verbosity=Verbosity.VERBOSE,
            )

        num_updates = sum(len(deps) for deps in updated_dependencies.values())
        if not num_updates:
            line(
                io=self.io,
                message='No dependency constraints to change.',
                style=Style.INFO,
            )
            return 0

        line(io=self.io, message='')  # Cosmetic new line

        line(
            io=self.io,
            message=f'Total: Proposing updates to {num_updates} dependencies.',
        )

        line(io=self.io, message='')  # Cosmetic new line

        if any([_check, _update, _lock]):
            for group in groups:
                print_group_header(self.io, group)

                for old_constraint, dependency in updated_dependencies[group]:
                    line(
                        io=self.io,
                        message=(
                            f'  <c1>{dependency.name}</>: <c2>{old_constraint}</> -->'
                            f' <c2>{dependency.pretty_constraint}</>'
                        ),
                        verbosity=Verbosity.VERBOSE,
                    )

                line(io=self.io, message='')  # Cosmetic new line

            should_not_update = _dry_run or not any([_update, _lock])

            if should_not_update:
                line(
                    io=self.io,
                    message='Checking that new dependencies can be solved...',
                    style=Style.INFO,
                )
            else:
                line(
                    io=self.io,
                    message='Running the poetry package installer...',
                    style=Style.INFO,
                )

            line(io=self.io, message='')  # Cosmetic new line

            # Check for a valid installer, otherwise it will be hidden with no message
            try:
                assert self.installer is not None
            except AssertionError:
                line_error(
                    io=self.io,
                    message=(
                        'ERROR: Poetry did not instantiate an installer for'
                        " 'poetry-plugin-constrain'."
                    ),
                    style=Style.ERROR,
                )
                return Error.NO_INSTALLER_FOUND

            try:
                status = run_installer_update(
                    poetry=self.poetry,
                    installer=self.installer,
                    lockfile_only=_lock,
                    dependencies_by_group={
                        group: [d for _, d in deps]
                        for group, deps in updated_dependencies.items()
                        if deps != []
                    },
                    poetry_config=poetry_config,
                    dry_run=should_not_update,
                    verbose=self.io.is_verbose(),
                    silent=(should_not_update and not self.io.is_verbose()),
                )
            except Exception as exc:  # noqa: BLE001 # pylint: disable=W0718
                # Catch-all for unexpected errors
                line_error(
                    io=self.io,
                    message=str(exc),
                    style=Style.ERROR,
                )
                return Error.INSTALLER_UPDATE_FAILED
            else:
                if _check:
                    line(io=self.io, message='\nDependency check successful.')
        else:
            if not _check:
                line(
                    io=self.io,
                    message='Skipping version check.',
                    style=Style.INFO,
                )

            status = 0

        line(io=self.io, message='')  # Cosmetic new line

        for group in groups:
            if group == MAIN_GROUP:  # pylint: disable=W0160
                group_dependencies_config = poetry_config.get('dependencies')
            else:
                group_dependencies_config = deep_get(
                    poetry_config,
                    ['group', group, 'dependencies'],
                )

            if group_dependencies_config is None or not updated_dependencies[group]:
                continue

            print_group_header(self.io, group)

            for old_constraint, dependency in updated_dependencies[group]:
                name = dependency.pretty_name
                new_constraint = dependency.pretty_constraint

                constraints = group_dependencies_config[name]

                # Support multiple constraint dependencies
                if isinstance(constraints, list):
                    for ndx, _constraint in enumerate(constraints):
                        if isinstance(_constraint, dict):
                            _old_constraint = group_dependencies_config[name][ndx][
                                'version'
                            ]
                            if _old_constraint != old_constraint:
                                continue
                            group_dependencies_config[name][ndx][
                                'version'
                            ] = new_constraint
                        else:
                            _old_constraint = group_dependencies_config[name][ndx]
                            if _old_constraint != old_constraint:
                                continue
                            group_dependencies_config[name][ndx] = new_constraint
                else:
                    if isinstance(constraints, dict):
                        group_dependencies_config[name]['version'] = new_constraint
                    else:
                        group_dependencies_config[name] = new_constraint

                line(
                    io=self.io,
                    message=(
                        f'Updated <c1>{name}</>: {old_constraint} --> {new_constraint}'
                    ),
                    style=Style.INFO,
                )

            line(io=self.io, message='')  # Cosmetic new line

        if status == 0 and not _dry_run:
            pyproject.save()
            line(
                io=self.io,
                message='Updated pyproject.toml with new constraints.',
                style=Style.INFO,
            )
        else:
            line(
                io=self.io,
                message='Skipped modifying pyproject.toml due to dry-run flag.',
                style=Style.INFO,
            )

        return status
