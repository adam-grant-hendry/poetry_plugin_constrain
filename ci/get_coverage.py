"""Prints the test coverage from the last run of the test suite.

This is used to generate a coverage badge in ``test.yml``. The script is designed to be
run in a subshell and the output stored in a temporary environment variable.

Example
-------

In ``bash``, the output of this script could be stored in an environment variable
``TOTAL`` as follows:

$ export TOTAL=$(python ../../ci/get_coverage.py)
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
