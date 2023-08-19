"""Documentation configuration file.

This file is read by the ``sphinx`` documentation builder to generate our documentation.
"""
# ruff: noqa: A001
from __future__ import annotations

import importlib.resources as rsrc
import os
import sys
from datetime import datetime, timezone
from importlib import metadata

# -- Project information ----------------------------------------------------------------

project = 'poetry_plugin_constrain'
copyright = f'2023-{datetime.now(tz=timezone.utc).date().year}, Adam Grant Hendry'
author = 'Adam Grant Hendry'
root_package = project
version = metadata.version(project)
release = version

# -- Path setup -------------------------------------------------------------------------

with rsrc.path(root_package, '__init__.py') as file_:
    root = file_.parent.parent

packages = [
    root / root_package,
    root / r'docs',
    root / r'tests',
]

for pkg in packages:
    # In Python 3.6 and later it is recommended to use os.fspath() instead of str() if
    # you need to do an explicit conversion. This is a little safer as it will raise an
    # error if you accidentally try to convert an object that is not pathlike.
    sys.path.insert(0, os.fspath(pkg.resolve()))

# -- Extensions -------------------------------------------------------------------------

extensions: list[str] = [
    'numpydoc',
    'sphinx_book_theme',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx.ext.githubpages',
    'sphinxcontrib.email',
    'sphinxcontrib.mermaid',
]

# -- General configuration --------------------------------------------------------------

# Paths are relative to ``source``
# templates_path = ['_templates']
# html_static_path = ['_static']

source_suffix = '.rst'
master_doc = 'index'

# List of files relative to ``source`` to ignore when looking for source files
exclude_patterns: list[str] = [
    '_build',
]

# -- HTML Output ------------------------------------------------------------------------

html_baseurl = 'www.poetry-plugin-constrain.com'

# html_logo = r'./_resources/img/template_logo.png'
html_theme = 'sphinx_book_theme'

html_theme_options = {
    'repository_url': 'https://github.com/adam-grant-hendry/poetry_version_constrain',
    'use_repository_button': True,
}

# String appended to project name with hyphen in ``<title>`` tag of individual pages and
# used in the navigation bar as the “topmost” element. It defaults to '<project>
# v<revision> documentation'. Remove so only project name appears in title.
html_title = ''

html_short_title = project

# Removes the "View Source" hyperlink
html_show_sourcelink = False

# Enable figure numbering. If true, figures, tables and code-blocks are automatically
# numbered if they have a caption. The numref role is enabled. Obeyed so far only by
# HTML and LaTeX builders. Default is False.
num_fig = True
