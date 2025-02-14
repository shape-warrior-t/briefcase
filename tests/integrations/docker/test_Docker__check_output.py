import os
import sys
from pathlib import Path
from unittest.mock import ANY

import pytest

from briefcase.console import Log


def test_simple_call(mock_docker, tmp_path, capsys):
    """A simple call will be invoked."""
    assert mock_docker.check_output(["hello", "world"]) == "goodbye\n"

    mock_docker._subprocess._subprocess.check_output.assert_called_with(
        [
            "docker",
            "run",
            "--volume",
            f"{tmp_path / 'platform'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/home/brutus/.cache/briefcase:z",
            "--rm",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            "world",
        ],
        text=True,
        encoding=ANY,
    )
    assert capsys.readouterr().out == ""


def test_call_with_arg_and_env(mock_docker, tmp_path, capsys):
    """Extra keyword arguments are passed through as-is; env modifications are
    converted."""
    assert (
        mock_docker.check_output(
            ["hello", "world"],
            env={
                "MAGIC": "True",
                "IMPORTANCE": "super high",
            },
            universal_newlines=True,
        )
        == "goodbye\n"
    )

    mock_docker._subprocess._subprocess.check_output.assert_called_with(
        [
            "docker",
            "run",
            "--volume",
            f"{tmp_path / 'platform'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/home/brutus/.cache/briefcase:z",
            "--rm",
            "--env",
            "MAGIC=True",
            "--env",
            "IMPORTANCE=super high",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            "world",
        ],
        universal_newlines=True,
        encoding=ANY,
    )
    assert capsys.readouterr().out == ""


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_call_with_path_arg_and_env(mock_docker, tmp_path, capsys):
    """Path-based arguments and environment are converted to strings and passed
    in as-is."""
    assert (
        mock_docker.check_output(
            ["hello", tmp_path / "location"],
            env={
                "MAGIC": "True",
                "PATH": f"/somewhere/safe:{tmp_path / 'briefcase' / 'tools'}:{tmp_path / 'platform' / 'location'}",
            },
            cwd=tmp_path / "cwd",
        )
        == "goodbye\n"
    )

    mock_docker._subprocess._subprocess.check_output.assert_called_with(
        [
            "docker",
            "run",
            "--volume",
            f"{tmp_path / 'platform'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/home/brutus/.cache/briefcase:z",
            "--rm",
            "--env",
            "MAGIC=True",
            "--env",
            "PATH=/somewhere/safe:/home/brutus/.cache/briefcase/tools:/app/location",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            os.fsdecode(tmp_path / "location"),
        ],
        cwd=os.fsdecode(tmp_path / "cwd"),
        text=True,
        encoding=ANY,
    )
    assert capsys.readouterr().out == ""


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows paths aren't converted in Docker context"
)
def test_simple_verbose_call(mock_docker, tmp_path, capsys):
    """If verbosity is turned out, there is output."""
    mock_docker.command.logger = Log(verbosity=2)

    assert mock_docker.check_output(["hello", "world"]) == "goodbye\n"

    mock_docker._subprocess._subprocess.check_output.assert_called_with(
        [
            "docker",
            "run",
            "--volume",
            f"{tmp_path / 'platform'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/home/brutus/.cache/briefcase:z",
            "--rm",
            "briefcase/com.example.myapp:py3.X",
            "hello",
            "world",
        ],
        text=True,
        encoding=ANY,
    )
    assert capsys.readouterr().out == (
        "\n"
        ">>> Running Command:\n"
        ">>>     docker run "
        f"--volume {tmp_path / 'platform'}:/app:z "
        f"--volume {tmp_path / 'briefcase'}:/home/brutus/.cache/briefcase:z "
        "--rm "
        "briefcase/com.example.myapp:py3.X "
        "hello world\n"
        ">>> Working Directory:\n"
        f">>>     {Path.cwd()}\n"
        ">>> Command Output:\n"
        ">>>     goodbye\n"
        ">>> Return code: 0\n"
    )
