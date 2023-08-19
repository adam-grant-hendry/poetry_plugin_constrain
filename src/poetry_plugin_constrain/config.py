"""Configuration options for the plugin."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from poetry_plugin_constrain.utils import deep_get

if TYPE_CHECKING:
    from poetry.poetry import Poetry

TOML_TABLE = 'poetry-plugin-constrain'
TOML_VAR_NAMES = [
    'post-init-hook',
    'post-add-hook',
    'post-check-hook',
    'post-update-hook',
    'enable-post-hooks',
    'old',
    'new',
    'only',
    'without',
    'dry-run',
    'update',
    'lock',
    'check',
]

ENV_VAR_PREFIX = TOML_TABLE.replace('-', '_').upper()
ENV_VAR_NAMES = {name: name.replace('-', '_').upper() for name in TOML_VAR_NAMES}


class TruthValueError(Exception):
    def __init__(
        self,
        value: str | bool,
    ) -> None:
        super().__init__(f'Invalid truth value {value!r}')


class ConfigurationVariableError(Exception):
    def __init__(
        self,
        variable: str,
    ) -> None:
        super().__init__(
            f"'{variable}' is not a valid 'poetry-plugin-constrain' configuration"
            ' variable.',
        )


def _strtobool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value

    value = value.lower()
    if value in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif value in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        raise TruthValueError(value)


def get_config_variable(poetry: Poetry, toml_var_name: str, default: Any = None) -> Any:
    """Get the configuration variable value for the plugin if it exists.

    This method retrieves the configuration variable set for the plugin. It may be an
    environment variable or a variable set in the ``pyproject.toml`` file.

    Parameters
    ----------
    poetry : Poetry
        The ``poetry`` application.
    toml_var_name : str
        The ``pyproject.toml`` configuration variable name for the plugin.
    default : Any
        The default value to use if variable not found, by default ``None``

    Returns
    -------
    Any
        The value of the variable or the default value if not found.
    """
    if toml_var_name not in ENV_VAR_NAMES:
        raise ConfigurationVariableError(toml_var_name)

    pyproject_toml_section = deep_get(poetry.pyproject.data, ['tool', TOML_TABLE])

    if pyproject_toml_section and toml_var_name in pyproject_toml_section:
        return pyproject_toml_section[toml_var_name]

    env_var = '_'.join([ENV_VAR_PREFIX, ENV_VAR_NAMES[toml_var_name]])

    return os.environ.get(env_var, default)


def are_post_hooks_enabled(poetry: Poetry) -> bool:
    """Return whether the plugin post-hooks are enabled.

    Parameters
    ----------
    poetry : Poetry
        The ``poetry`` application

    Returns
    -------
    bool
        ``True`` if ``enable-post-hooks`` is set, else ``False``.
    """
    return _strtobool(
        get_config_variable(
            poetry,
            toml_var_name='enable-post-hooks',
            default=True,
        ),
    )
