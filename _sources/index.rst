#######################
poetry-plugin-constrain
#######################

.. meta::
   :description:
      A poetry plugin and pre-commit hook that lets the user choose the default method for constraining dependency versions.  :keywords: poetry, plugin, dependency, version, constrain

A `poetry`_ plugin and `pre-commit`_ hook that lets the user choose the default method for constraining dependency versions. By default, uses ``>=`` instead of ``^``.

Background
==========

By default, `poetry`_ uses `upper bound constraints`_ (i.e. ``^``) when adding new dependencies, which has has been hotly contested [#]_ [#]_ [#]_.

Acknowledgements
================

This package is heavily inspired by `poetry-relax`_ with a few differences:

#. Users can specify which constraint method to use when adding new dependencies (defaults to ``>=``).

#. Users can specify which constraint method to replace (defaults to ``^``)

#. Options for the plugin can be configured in the user ``pyproject.toml`` file or with ``environment variables``.

#. Hooks have been added to run ``poetry constrain`` automatically after ``init``, ``add``, ``check``, or ``update`` are called (see ``opting out of command hooks``.)

#. You can add ``poetry-plugin-constrain`` to your ``.pre-commit-config.yaml`` as a `pre-commit`_ hook.

+------------+---------+-----------------------------------+
| Method     | Marker  | Command                           |
+============+=========+===================================+
|| ``caret`` || ``^``  || ``poetry constrain --new=caret`` |
|| ``tilde`` || ``~``  || ``poetry constrain --new=tilde`` |
|| ``ne``    || ``!=`` || ``poetry constrain --new=ne``    |
|| ``ge``    || ``>=`` || ``poetry constrain --new=ge``    |
|| ``gt``    || ``>``  || ``poetry constrain --new=gt``    |
|| ``le``    || ``<=`` || ``poetry constrain --new=le``    |
|| ``lt``    || ``<``  || ``poetry constrain --new=lt``    |
|| ``exact`` || ``==`` || ``poetry constrain --new=exact`` |
+------------+---------+-----------------------------------+


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
