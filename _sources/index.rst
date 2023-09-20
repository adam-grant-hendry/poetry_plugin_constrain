#######################
poetry-plugin-constrain
#######################

.. meta::
   :description:
      A poetry plugin and pre-commit hook that lets the user choose the default method for constraining dependency versions.  :keywords: poetry, plugin, dependency, version, constrain

A `poetry`_ plugin and `pre-commit`_ hook that lets the user choose the default method for constraining dependency versions. By default, uses ``>=`` instead of ``^``.

Background
==========

By default, `poetry`_ uses `upper bound constraints`_ (i.e. ``^``) when adding new dependencies, which has has been hotly contested [#]_ [#]_ [#]_. This package permits users to choose the type of constraint to enforce by default and adds hooks to automatically format constraints after ``init``, ``add``, ``check``, or ``update`` are called. The package can also be used as a `pre-commit`_ hook.

Installation
============

``poetry-plugin-constrain`` can be installed with ``pip``, ``pipx``, or ``poetry``.

``pip``
-------

To install, use::

    pip install poetry-plugin-constrain

To verify the plugin is available, run::

    poetry self show plugins

To uninstall, use::

    pip uninstall poetry-plugin-constrain

``pipx``
--------

To install, use::

    pipx inject poetry poetry-plugin-constrain

To verify the plugin is available, run::

    poetry self show plugins

To uninstall, use::

    pipx runpip poetry uninstall poetry-plugin-constrain

``poetry``
----------

To install, use::

    poetry self add poetry-plugin-constrain

To verify the plugin is available, run::

   poetry self show plugins

To uninstall, use::

    poetry self remove poetry-plugin-constrain

Usage
=====

``poetry-plugin-constrain`` is set to run automatically after ``init``, ``add``, ``check``, or ``update`` are called and change ``^`` constraints to ``>=``. However, it can also be called directly from the commandline::

   poetry constrain --help

Options
-------

  * ``--old``: The constraint to replace [**Default**: ``caret`` (i.e. ``^``)]. Must be one of:

    - ``caret`` (``^``)
    - ``tilde`` (``~``)
    - ``ne`` (``!=``)
    - ``ge`` (``>=``)
    - ``gt`` (``>``)
    - ``le`` (``<=``)
    - ``lt`` (``<``)
    - ``exact`` (``==``)

    **Example**:

    To replace ``~`` constraints with ``>=``, use::

      poetry constrain --old tilde

  * ``--new``: The constraint to replace ``old`` with [**Default**: ``ge`` (i.e. ``>=``)]. Must be one of:

    - ``caret`` (``^``)
    - ``tilde`` (``~``)
    - ``ne`` (``!=``)
    - ``ge`` (``>=``)
    - ``gt`` (``>``)
    - ``le`` (``<=``)
    - ``lt`` (``<``)
    - ``exact`` (``==``)

    **Example**:

    To replace ``^`` constraints with ``>`` for all dependencies, use::

      poetry constrain --new gt

  * ``--only``: Only constrain these dependency groups. **Takes precedence over** ``--without``. [**Multiple values allowed, comma-separated**]

  * ``--without``: Don't constrain these dependency groups. [**Multiple values allowed, comma-separated**]

  * ``--dry-run``: Don't format the ``pyproject.toml``. Just check constraints.

  * ``--update``: Update dependencies after changing constraints (equivalent to running ``poetry update``).

  * ``--lock``: Lock the ``poetry.lock`` file after changing constraints (equivalent to running ``poetry lock``).

  * ``--check``: Check the ``poetry.lock`` file for consistency after changing constraints (equivalent to running ``poetry check``).

Help
----

To see help for the command, run::

   poetry constrain --help

Configuration
=============

``poetry-plugin-constrain`` behavior can be configured in a ``pyproject.toml`` file or with environment variables.

.. note::

   ``pyproject.toml`` variables and environment variables accept any of the following as equiavlent to ``true``::

      ``'y'``, ``'yes'``, ``'t'``, ``'true'``, ``'on'``, or ``1``

   and any of the following as equivalent to ``false``::

      ``'n'``, ``'no'``, ``'f'``, ``'false'``, ``'off'``, or ``0``

``pyproject.toml``
------------------

To configure ``poetry-plugin-constrain`` using a ``pyproject.toml`` file, add a ``[tool.poetry-plugin-constrain]`` table and use any of the following settings (below are the default values):

.. code-block:: toml

   [tool.poetry-plugin-constrain]
   post-init-hook = "on"
   post-add-hook = "on"
   post-check-hook = "on"
   post-update-hook = "on"
   enable-post-hooks = "on"
   old = "caret"
   new = "ge"
   only = "<comma_separated_group_names_list>"
   without = "<comma_separated_group_names_list>"
   dry-run = "false"
   update = "false"
   lock = "false"
   check = "false"

Environment Variables
---------------------

All ``poetry-plugin-constrain`` environment variables begin with ``POETRY_PLUGIN_CONSTRAIN`` and are joined with underscores::

   POETRY_PLUGIN_CONSTRAIN_POST_INIT_HOOK=1
   POETRY_PLUGIN_CONSTRAIN_POST_ADD_HOOK=1
   POETRY_PLUGIN_CONSTRAIN_POST_CHECK_HOOK=1
   POETRY_PLUGIN_CONSTRAIN_POST_UPDATE_HOOK=1
   POETRY_PLUGIN_CONSTRAIN_ENABLE_POST_HOOKS=1
   POETRY_PLUGIN_CONSTRAIN_OLD=caret
   POETRY_PLUGIN_CONSTRAIN_NEW=ge
   POETRY_PLUGIN_CONSTRAIN_ONLY=<comma_separated_group_names_list>
   POETRY_PLUGIN_CONSTRAIN_WITHOUT=<comma_separated_group_names_list>
   POETRY_PLUGIN_CONSTRAIN_DRY_RUN=0
   POETRY_PLUGIN_CONSTRAIN_UPDATE=0
   POETRY_PLUGIN_CONSTRAIN_LOCK=0
   POETRY_PLUGIN_CONSTRAIN_CHECK=0

Acknowledgements
================

This package is heavily inspired by `poetry-relax`_ with a few differences:

#. Users can specify which constraint method to use when adding new dependencies (defaults to ``>=``).

#. Users can specify which constraint method to replace (defaults to ``^``)

#. Options for the plugin can be configured in the user ``pyproject.toml`` file or with ``environment variables``.

#. Hooks have been added to run ``poetry constrain`` automatically after ``init``, ``add``, ``check``, or ``update`` are called (see ``opting out of command hooks``.)

#. You can add ``poetry-plugin-constrain`` to your ``.pre-commit-config.yaml`` as a `pre-commit`_ hook.

.. _poetry: https://python-poetry.org/
.. _pre-commit: https://pre-commit.com/
.. _upper bound constraints: https://python-poetry.org/docs/dependency-specification/#caret-requirements
.. _poetry-relax: https://github.com/zanieb/poetry-relax

.. rubric:: References

.. [#] https://github.com/python-poetry/poetry/issues/3747
.. [#] https://github.com/python-poetry/poetry/issues/3427
.. [#] https://github.com/python-poetry/poetry/issues/2731

.. toctree::
   :maxdepth: 2
   :caption: Home Page

.. toctree::
   :maxdepth: 2
   :caption: Contributing

   _pages/contributing


.. toctree::
   :maxdepth: 2
   :caption: Support

   _pages/contact
