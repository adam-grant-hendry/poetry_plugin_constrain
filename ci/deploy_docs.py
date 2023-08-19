"""Move docs into proper folders for deployment to GitHub Pages.

So the ``pydata-sphinx-theme`` version switcher dropdown works, this script moves and
archives built documentation into proper subfolders. It also modifies ``switcher.json``
as needed. This script is designed to be called from ``docs/Makefile`` so it runs
automatically whenever

    poetry run make -C docs html

is invoked.
"""
# ruff: noqa: S603  # Commands here have no user input
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urljoin

from jinja2 import Environment, FileSystemLoader

IS_NEW_RELEASE = subprocess.run(
    'git describe --tags --exact-match HEAD 2> /dev/null'.split(),
    capture_output=True,
    text=True,
).stdout

SRC_DIR = Path('../docs/src').resolve()
BUILD_DIR = Path('../docs/build').resolve()

HTML_DIR = Path(f'{BUILD_DIR}/html')
STABLE_DIR = Path(f'{BUILD_DIR}/stable')
DEV_DIR = Path(f'{BUILD_DIR}/dev')

SWITCHER_JSON = Path(f'{STABLE_DIR}/_static/switcher.json')

OWNER_USERNAME = 'adam-grant-hendry'
REPO_NAME = 'poetry_plugin_constrain'
DOCS_URL = f'https://poetrypluginconstrain.org'


def update_landing_page_url() -> bool:
    """Update the URL to the docs landing page.

    If only ``dev`` docs are available, this will be:
        DOCS_URL/dev
    otherwise:
        DOCS_URL/stable

    Returns
    -------
    bool
        ``True`` if ``index.html`` changed, ``False`` otherwise
    """
    env = Environment(loader=FileSystemLoader(SRC_DIR), autoescape=True)
    tmpl = env.get_template('redirect.j2')

    if (STABLE_DIR / 'index.html').is_file():
        _content = tmpl.render(landing_page_url=urljoin(DOCS_URL, 'stable'))
    else:
        _content = tmpl.render(landing_page_url=urljoin(DOCS_URL, 'dev'))

    index = Path(f'{BUILD_DIR}/index.html').resolve()

    if index.is_file() and index.read_text(encoding='utf-8') == _content:
        return False

    index.write_text(_content, encoding='utf-8')
    return True


def update_switcher_json(
    new_version: str,
    old_version: str,
) -> None:
    """Update ``switcher.json`` with new version.

    Parameters
    ----------
    new_version : str
        The version to be added.
    old_version : str
        The previous version.
    """
    with SWITCHER_JSON.open(encoding='utf-8') as file_:
        switcher = json.load(file_)

    for entry in switcher:
        if entry.get('version') == 'stable':
            entry['name'] = new_version
            switcher.append(
                {
                    'version': old_version,
                    'name': urljoin(DOCS_URL, old_version),
                },
            )
            break
    else:
        switcher.append(
            {
                'version': 'stable',
                'name': new_version,
                'url': urljoin(DOCS_URL, 'stable'),
                'preferred': True,
            },
        )

    with SWITCHER_JSON.open(mode='w', encoding='utf-8') as file_:
        json.dump(switcher, file_, indent=4)


if __name__ == '__main__':
    if IS_NEW_RELEASE:
        GIT_REVLIST = 'git rev-list --tags --max-count=1'
        GIT_DESCRIBE = 'git describe --abbrev=0 --tags'

        NEW_TAG = subprocess.run(
            GIT_REVLIST.split(),
            capture_output=True,
            text=True,
        ).stdout.strip()
        OLD_TAG = subprocess.run(
            f'{GIT_REVLIST} --skip=1'.split(),
            capture_output=True,
            text=True,
        ).stdout.strip()
        NEW_VERSION = subprocess.run(
            f'{GIT_DESCRIBE} {NEW_TAG} 2> /dev/null'.split(),
            capture_output=True,
            text=True,
        ).stdout.strip()
        OLD_VERSION = subprocess.run(
            f'{GIT_DESCRIBE} {OLD_TAG} 2> /dev/null'.split(),
            capture_output=True,
            text=True,
        ).stdout.strip()

        if STABLE_DIR.is_dir():
            shutil.rmtree(STABLE_DIR)
        shutil.copytree(src=HTML_DIR, dst=STABLE_DIR)

        new_dir = Path(f'{BUILD_DIR}/{NEW_VERSION}')
        if new_dir.is_dir():
            shutil.rmtree(new_dir)
        shutil.copytree(src=HTML_DIR, dst=new_dir)

        modified_files = f'docs/build/stable docs/build/{NEW_VERSION}'

        old_dir = Path(f'{BUILD_DIR}/{OLD_VERSION}')
        old_zip = Path(f'{BUILD_DIR}/{OLD_VERSION}.zip')

        if OLD_VERSION:
            shutil.make_archive(
                base_name=str(old_zip),
                format='zip',
                root_dir=old_dir,
            )
            modified_files += f' docs/build/{OLD_VERSION} docs/build/{OLD_VERSION}.zip'

        update_switcher_json(
            new_version=NEW_VERSION,
            old_version=OLD_VERSION,
        )
    else:
        if DEV_DIR.is_dir():
            shutil.rmtree(DEV_DIR)

        shutil.copytree(src=HTML_DIR, dst=DEV_DIR)

        modified_files = 'docs/build/dev'

    shutil.rmtree(HTML_DIR)

    if update_landing_page_url():
        modified_files += ' docs/build/index.html'

    print(  # noqa: T201  # stdout is queried in `docs.yml` for `modified_files`
        f'[deploy_docs.py] Modified files: {modified_files}',
    )
