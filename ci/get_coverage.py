"""Prints the test coverage from the last run of the test suite.

This is used to generate a coverage badge in ``test.yml``. The script is designed to be
run in a subshell and the output stored in a temporary environment variable.

Note
----

In GitHub Actions, after checking out a repo, the present working directory (``$PWD``)
is the root of the project. Hence, this file is accessed here using the path
``ci/get_coverage.py``.

Example
-------

Using ``bash`` in a GitHub Actions workflow, this script can be called and the output
stored in an environment variable like so:

$ export TOTAL=$(python ci/get_coverage.py)
$ echo "total_coverage=$TOTAL" >> $GITHUB_OUTPUT
"""

from __future__ import annotations

import json
from pathlib import Path

if __name__ == '__main__':
    with Path('logs/coverage/coverage.json').open(encoding='utf-8') as file:
        coverage = json.load(file)
        print(  # noqa: T201  # Console output is used by GitHub Actions workflows
            coverage['totals']['percent_covered_display'],
        )
