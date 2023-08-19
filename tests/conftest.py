"""Test configuration file."""

from __future__ import annotations

import os
import sys
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

import pytest
from cleo.testers.application_tester import ApplicationTester
from poetry.config.config import Config as BaseConfig
from poetry.config.dict_config_source import DictConfigSource
from poetry.console.application import Application
from poetry.factory import Factory
from poetry.layouts import layout
from poetry.plugins.application_plugin import ApplicationPlugin
from poetry.plugins.plugin_manager import PluginManager
from poetry.poetry import Poetry
from poetry.repositories import Repository
from poetry.utils.env import MockEnv

if TYPE_CHECKING:
    from _pytest.tmpdir import TempPathFactory
    from poetry.utils.env import Env
    from pytest_mock import MockerFixture

    if sys.version_info >= (3, 10):
        from typing import TypeAlias
    else:
        from typing_extensions import TypeAlias

# See: https://github.com/python/mypy/issues/14158
if sys.version_info < (3, 10):
    PoetryTesterFactory: TypeAlias = 'Callable[[Poetry], ApplicationTester]'
    PoetryFactory: TypeAlias = 'Callable[[Poetry], Application]'
    ProjectFactory: TypeAlias = 'Callable[[str | None], Poetry]'
else:
    PoetryTesterFactory: TypeAlias = Callable[[Poetry], ApplicationTester]
    PoetryFactory: TypeAlias = Callable[[Poetry], Application]
    ProjectFactory: TypeAlias = Callable[[str | None], Poetry]

# Exclude certain dirs/files from being collected by the ``pytest`` runner.
collect_ignore: list[str] = ['__init__.py']

# Several of the helpers and fixtures below were adopted from poetry 1.6. Specifically,
# these are located in:
#   - tests/conftest.py
#   - tests/console/conftest.py

CLEO_ENV_VARS = [
    'ANSICON',
    'COLORTERM',
    'SHELL',
    'TERM',
    'TERM_PROGRAM',
]

FIXTURE_PATH = Path(__file__).parent / 'fixtures'

# Used as a mock for latest git revision.
MOCK_DEFAULT_GIT_REVISION = '9cf87a285a2d3fbb0b9fa621997b3acc3631ed24'


class Config(BaseConfig):
    """Fake configuration for injecting configuration and author configuration sources.

    This exposes ``_config_source`` and ``_auth_config_source`` as class variables so they
    may be injected into several getters for testing purposes.
    """

    _config_source: DictConfigSource
    _auth_config_source: DictConfigSource

    def get(self, setting_name: str, default: Any = None) -> Any:
        """Extend the base ``get`` method.

        Injects the ``_config_source`` AND ``_auth_config_source``.

        Parameters
        ----------
        setting_name : str
            The name of the setting to get
        default : Any, optional
            The default value for the setting, by default ``None``

        Returns
        -------
        Any
            The value of the setting.
        """
        self.merge(self._config_source.config)
        self.merge(self._auth_config_source.config)

        return super().get(setting_name, default=default)

    def raw(self) -> dict[str, Any]:
        """Return the raw configuration dictionary.

        Injects the ``_config_source`` AND ``_auth_config_source``.

        Returns
        -------
        dict[str, Any]
            The raw configuration dictionary.
        """
        self.merge(self._config_source.config)
        self.merge(self._auth_config_source.config)

        return super().raw()

    def all(self) -> dict[str, Any]:  # noqa: A003
        """Return the flattened configuration dictionary.

        Injects the ``_config_source`` AND ``_auth_config_source``.

        Returns
        -------
        dict[str, Any]
            The flattened configuration dictionary.
        """
        self.merge(self._config_source.config)
        self.merge(self._auth_config_source.config)

        return super().all()


@pytest.fixture()
def config_cache_dir(tmp_path: Path) -> Path:
    """Fake ``poetry`` configuration cache directory.

    Parameters
    ----------
    tmp_path : Path
        A ``pytest`` fixture that returns a temporary path for testing

    Returns
    -------
    Path
        The fake ``poetry`` configuration cache directory
    """
    path = tmp_path / '.cache' / 'pypoetry'
    path.mkdir(parents=True)
    return path


@pytest.fixture()
def config_source(config_cache_dir: Path) -> DictConfigSource:
    """Return a configuration source.

    Parameters
    ----------
    config_cache_dir : Path
        Path to the configuration cache directory.

    Returns
    -------
    DictConfigSource
        A configuration source
    """
    source = DictConfigSource()
    source.add_property('cache-dir', str(config_cache_dir))

    return source


@pytest.fixture()
def auth_config_source() -> DictConfigSource:
    """Return an author configuration source.

    Returns
    -------
    DictConfigSource
        An author configuration source
    """
    source = DictConfigSource()

    return source


@pytest.fixture(autouse=True)
def config(
    config_source: DictConfigSource,
    auth_config_source: DictConfigSource,
    mocker: MockerFixture,
) -> Config:
    """Return a fake ``poetry`` configuration instance.

    This injects a configuration and author configuration source into the ``Config``
    instance.

    Parameters
    ----------
    config_source : DictConfigSource
        A ``poetry`` fixture that returns a fake configuration source
    auth_config_source : DictConfigSource
        A ``poetry`` fixture that returns a fake author configuration source
    mocker : MockerFixture
        A ``pytest-mock`` fixture that returns a mocker instance.

    Returns
    -------
    Config
        The fake ``poetry`` configuration instance.
    """
    import keyring
    from keyring.backends.fail import Keyring

    keyring.set_keyring(Keyring())  # type: ignore[no-untyped-call]

    c = Config()
    c.merge(config_source.config)
    c.set_config_source(config_source)
    c.set_auth_config_source(auth_config_source)

    mocker.patch('poetry.config.config.Config.create', return_value=c)
    mocker.patch('poetry.config.config.Config.set_config_source')

    return c


@pytest.fixture()
def env(tmp_path: Path) -> MockEnv:
    """Return a mock virtual environment."""
    path = tmp_path / '.venv'
    path.mkdir(parents=True)
    return MockEnv(path=path, is_venv=True)


@pytest.fixture()
def installed() -> Repository:
    """Return a fake installed repository."""
    return Repository('installed')


@pytest.fixture(autouse=True)
def _setup(
    mocker: MockerFixture,
    installed: Repository,
    env: MockEnv,
) -> None:
    # Do not run pip commands of the executor
    mocker.patch('poetry.installation.executor.Executor.run_pip')

    # These installer methods run the solver, which slows test execution significantly
    # and is unnecessary as the repos are mocked
    p = mocker.patch('poetry.installation.installer.Installer._get_installed')
    p.return_value = installed

    p = mocker.patch('poetry.repositories.installed_repository.InstalledRepository.load')
    p.return_value = installed

    # Patch virtual environment creation to do nothing
    mocker.patch('poetry.utils.env.EnvManager.create_venv', return_value=env)


@pytest.fixture(scope='session', autouse=True)
def _unset_env_vars() -> None:
    """Unset ``poetry-plugin-constrain`` environment variables.

    Since these affect the behavior of the plugin, they should be unset for every test
    for the entire test session.
    """
    env_vars = (
        var for var in os.environ if (var.startswith('POETRY_') or var in CLEO_ENV_VARS)
    )
    for var in env_vars:
        os.environ.pop(var)


@pytest.fixture(autouse=True)
def _disable_other_application_plugins(
    monkeypatch,
) -> None:
    """Disables any other poetry application plugins currently installed.

    Only the ``constrain`` application plugin is enabled during testing.

    Parameters
    ----------
    mocker : MockerFixture
        A ``pytest-mock`` fixture that returns a mock instance
    """

    def _entry_points(self, env: Env | None = None) -> list[metadata.EntryPoint]:
        if self._group == ApplicationPlugin.group:
            return [
                metadata.EntryPoint(
                    name='constrain',
                    value='poetry_plugin_constrain.plugins:ConstrainPlugin',
                    group=ApplicationPlugin.group,
                ),
            ]
        else:
            entry_points = metadata.entry_points()

            if entry_points.get(self._group):
                return [
                    ep
                    for ep in entry_points[self._group]
                    if self._is_plugin_candidate(ep, env)
                ]

            return []

    monkeypatch.setattr(
        PluginManager,
        'get_plugin_entry_points',
        _entry_points,
    )


@pytest.fixture(scope='session')
def fixture_dir() -> Path:
    """Return the path to ``pyproject.toml`` test fixture assets.

    These assets are used to test the behavior of this plugin.

    Returns
    -------
    Path
        The path to ``pyproject.toml`` test fixture assets.
    """
    return FIXTURE_PATH


@pytest.fixture()
def project_dir(
    tmp_path_factory: TempPathFactory,
) -> Path:
    """Return the path to the ``poetry`` project directory for the test.

    Parameters
    ----------
    tmp_path_factory : TempPathFactory
        A built-in ``pytest`` fixture that creates a temporary directory for a test

    Returns
    -------
    Path
        The ``Path`` to the ``poetry`` project directory.
    """
    return tmp_path_factory.mktemp('project')


@pytest.fixture()
def cache_dir(
    tmp_path_factory: TempPathFactory,
) -> Path:
    """Return the path to the ``poetry`` cache directory for the test.

    Parameters
    ----------
    tmp_path_factory : TempPathFactory
        A built-in ``pytest`` fixture that creates a temporary directory for a test

    Returns
    -------
    Path
        The ``Path`` to the ``poetry`` cache directory.
    """
    return tmp_path_factory.mktemp('cache')


@pytest.fixture()
def poetry_factory(
    cache_dir: Path,
) -> PoetryFactory:
    """Create a new ``poetry`` application.

    For test isolation, we insist on creating virtual environments in the project root
    directory.

    Parameters
    ----------
    cache_dir : Path
        A ``poetry_plugin_constrain`` fixture that returns the path to the ``poetry``
        application cache folder

    Returns
    -------
    PoetryFactory
        A ``poetry`` application creator.
    """

    def factory(
        poetry: Poetry,
    ) -> Application:
        app = Application()

        app._poetry = poetry
        app._auto_exit = False

        app.poetry.config.merge(
            {
                'cache-dir': str(cache_dir),
                'virtualenvs': {
                    'in-project': True,
                },
            },
        )

        return app

    return factory


@pytest.fixture()
def poetry_tester_factory(
    poetry_factory: PoetryFactory,
) -> PoetryTesterFactory:
    """Create a new ``cleo.testers.ApplicationTester`` instance that uses ``poetry``.

    ``ApplicationTester`` instances use ``BufferedIO`` for their ``io`` attribute so that
    ``fetch_output()`` and ``fetch_error()`` can be called. This can be used to
    compare the output sent to the terminal with the actual output obtained from
    ``pytest.capsys``, or an equivalent fixture to capture ``sys.stdio`` or ``sys.stderr``
    output.

    Returns
    -------
    PoetryTesterFactory
        A ``cleo.testers.ApplicationTester`` creator that uses ``poetry``.
    """

    def factory(poetry: Poetry) -> ApplicationTester:
        app_tester = ApplicationTester(application=poetry_factory(poetry))
        return app_tester

    return factory


@pytest.fixture()
def project_factory(
    project_dir: Path,
    fixture_dir: Path,
) -> ProjectFactory:
    """Create a new ``poetry`` project in a temporary test directory.

    Parameters
    ----------
    project_dir : Path
        A ``poetry-plugin-constrain`` fixture that returns the temporary project
        directory for the test
    fixture_dir : Path
        A ``poetry-plugin-constrain`` fixture that returns the fixture directory

    Returns
    -------
    ProjectFactory
        A ``poetry`` project creator.
    """

    def factory(
        pyproject: str | None = None,
    ) -> Poetry:
        pyproject_file_path = project_dir / 'pyproject.toml'

        if pyproject:
            pyproject_content = (fixture_dir / pyproject).read_text()
            pyproject_file_path.write_text(pyproject_content)
        else:
            layout('src')('test').create(project_dir, with_tests=False)

        poetry = Factory().create_poetry(project_dir)
        return poetry

    return factory
