"""Helpers for testing."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cleo.testers.application_tester import ApplicationTester


def print_output(
    tester: ApplicationTester,
) -> None:
    """Print output of the ``ApplicationTester``.

    Parameters
    ----------
    tester : ApplicationTester
        The application tester
    """
    stdout = tester.io.fetch_output()
    stderr = tester.io.fetch_error()

    if stdout:
        print('Output')  # noqa: T201  # Debugging only
        print('======')  # noqa: T201  # Debugging only
        print(stdout)  # noqa: T201  # Debugging only
    else:
        print('No output')  # noqa: T201  # Debugging only
    if stderr:
        print('Error')  # noqa: T201  # Debugging only
        print('=====')  # noqa: T201  # Debugging only
        print(stderr)  # noqa: T201  # Debugging only
    else:
        print('No errors')  # noqa: T201  # Debugging only
