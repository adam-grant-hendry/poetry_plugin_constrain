"""Documentation configuration file.

This file is read by the ``sphinx`` documentation builder to generate our documentation.
"""
# ruff: noqa: A001
from __future__ import annotations

import importlib.resources as rsrc
import os
import subprocess
import sys
from datetime import datetime, timezone
from importlib import metadata
from urllib.parse import urljoin

AUTHOR = 'Adam Grant Hendry'
OWNER_USERNAME = 'adam-grant-hendry'
REPO_NAME = 'poetry_plugin_constrain'

REPO_URL = f'https://github.com/{OWNER_USERNAME}/{REPO_NAME}/'
DOCS_URL = f'https://poetrypluginconstrain.org/'

USE_VERSION_SWITCHER = True
HAS_A_RELEASE = subprocess.run(
    'git describe --tags'.split(),  # noqa: S603  # Command has no user input
    capture_output=True,
    text=True,
).stdout

# Project information
project = REPO_NAME
copyright = f'2023-{datetime.now(tz=timezone.utc).date().year}, {AUTHOR}'
author = AUTHOR
root_package = project
version = metadata.version(project)
release = version

# Path setup
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

# Extensions
extensions: list[str] = [
    'numpydoc',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx.ext.githubpages',
    'sphinxcontrib.email',
    'sphinxcontrib.mermaid',
    'sphinx_copybutton',
]

# General Configuration

# Paths are relative to ``conf.py``
html_static_path = ['_static']
templates_path = ['_templates']

source_suffix = '.rst'
master_doc = 'index'

# List of files relative to ``source`` to ignore when looking for source files
exclude_patterns: list[str] = [
    '_build',
    'build',
]

# HTML Output
version_match = 'stable'
json_url = urljoin(DOCS_URL, f'{version_match}/_static/switcher.json')

html_baseurl = f'poetrypluginconstrain.org'
html_theme = 'sphinx_book_theme'
html_css_files = [
    'css/custom.css',
]
html_theme_options = {
    # 'repository_url': REPO_URL,
    # 'use_repository_button': True,
    # See: https://github.com/pydata/pydata-sphinx-theme/issues/1328
    'logo': {
        'image_light': '_static/logo_light.png',
        'image_dark': '_static/logo_dark.png',
    },
}

if USE_VERSION_SWITCHER and HAS_A_RELEASE:
    version_match = 'stable'
    json_url = urljoin(DOCS_URL, f'{version_match}/_static/switcher.json')
    html_theme_options['switcher'] = {
        'json_url': json_url,
        'version_match': version_match,
    }
    html_theme_options['navbar_start'] = [  # type: ignore[assignment]
        'version-switcher',
    ]
    html_theme_options['show_version_warning_banner'] = True  # type: ignore[assignment]

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
