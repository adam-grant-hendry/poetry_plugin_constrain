"""Test ``config.py``."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pytest

from poetry_plugin_constrain.config import (
    ConfigurationVariableError,
    TruthValueError,
    _strtobool,
    get_config_variable,
)

if TYPE_CHECKING:
    import sys

    from poetry.poetry import Poetry

    if sys.version_info >= (3, 10):
        from typing import TypeAlias
    else:
        from typing_extensions import TypeAlias

    # See: https://github.com/python/mypy/issues/14158
    if sys.version_info < (3, 10):
        ProjectFactory: TypeAlias = 'Callable[[str | None], Poetry]'
    else:
        ProjectFactory: TypeAlias = Callable[[str | None], Poetry]


def test_strtobool_invalid_value() -> None:
    """Test providing an invalid value to ``_strtobool`` results in a ``ValueError``."""
    with pytest.raises(TruthValueError, match="Invalid truth value 'blah'"):
        _strtobool('blah')


@pytest.mark.parametrize(
    'fixture_toml',
    [
        'test_config_enable_post_hooks_false.toml',
    ],
)
def test_get_config_variable_toml(
    project_factory: ProjectFactory,
    fixture_toml: str,
) -> None:
    """Test ``get_config_variable`` accepts ``toml`` file parameters.

    Parameters
    ----------
    project_factory : ProjectFactory
        A ``poetry_plugin_constrain`` fixture that creates a ``poetry`` project.
    fixture_toml : str
        The input ``pyproject.toml`` file fixture.
    """
    project = project_factory(fixture_toml)

    assert get_config_variable(project, 'enable-post-hooks') is False

    with pytest.raises(
        ConfigurationVariableError,
        match=(
            "'dummy-var' is not a valid 'poetry-plugin-constrain' configuration"
            ' variable.'
        ),
    ):
        get_config_variable(project, 'dummy-var')
