import inspect
from unittest import mock

import pytest
from git import exc as git_exceptions

from briefcase.config import AppConfig
from briefcase.console import Printer

# Stop Rich from inserting line breaks in to long lines of text.
# Rich does this to prevent individual words being split between
# two lines in the terminal...however, these additional line breaks
# cause some tests to fail unexpectedly.
Printer.console.soft_wrap = True


@pytest.fixture
def mock_git():
    git = mock.MagicMock()
    git.exc = git_exceptions

    return git


# alias print() to allow non-briefcase code to use it
_print = print


def monkeypatched_print(*args, **kwargs):
    """Raise an error for calls to print() from briefcase."""
    frame = inspect.currentframe().f_back
    module = inspect.getmodule(frame.f_code)

    # Disallow any use of a bare print() in the briefcase codebase
    if module.__name__.startswith("briefcase."):
        pytest.fail(
            "print() should not be invoked directly. Use Log or Console for printing."
        )

    _print(*args, **kwargs)


@pytest.fixture(autouse=True)
def no_print(monkeypatch):
    """Replace builtin print function for ALL tests."""
    monkeypatch.setattr("builtins.print", monkeypatched_print)


@pytest.fixture
def first_app_config():
    return AppConfig(
        app_name="first",
        bundle="com.example",
        version="0.0.1",
        description="The first simple app",
        sources=["src/first"],
    )


@pytest.fixture
def first_app_unbuilt(first_app_config, tmp_path):
    # The same fixture as first_app_config,
    # but ensures that the bundle for the app exists
    (tmp_path / "tester").mkdir(parents=True, exist_ok=True)
    with (tmp_path / "tester" / "first.dummy").open("w") as f:
        f.write("first.bundle")

    return first_app_config


@pytest.fixture
def first_app(first_app_unbuilt, tmp_path):
    # The same fixture as first_app_config,
    # but ensures that the binary for the app exists
    with (tmp_path / "tester" / "first.dummy.bin").open("w") as f:
        f.write("first.exe")

    return first_app_unbuilt
