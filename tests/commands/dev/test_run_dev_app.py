import sys
from subprocess import CalledProcessError

import pytest

from briefcase.exceptions import BriefcaseCommandError


def test_subprocess_running_successfully(dev_command, first_app, tmp_path):
    env = dict(a=1, b=2, c=3)
    dev_command.run_dev_app(first_app, env)
    dev_command.subprocess.run.assert_called_once_with(
        [
            sys.executable,
            "-c",
            (
                "import runpy, sys;"
                "sys.path.pop(0);"
                'runpy.run_module("first", run_name="__main__", alter_sys=True)'
            ),
        ],
        env=env,
        cwd=dev_command.home_path,
        check=True,
    )


def test_subprocess_throws_error(dev_command, first_app, tmp_path):
    env = dict(a=1, b=2, c=3)
    dev_command.subprocess.run.side_effect = CalledProcessError(returncode=2, cmd="cmd")
    with pytest.raises(
        BriefcaseCommandError, match="Unable to start application 'first'"
    ):
        dev_command.run_dev_app(first_app, env)
    dev_command.subprocess.run.assert_called_once_with(
        [
            sys.executable,
            "-c",
            (
                "import runpy, sys;"
                "sys.path.pop(0);"
                'runpy.run_module("first", run_name="__main__", alter_sys=True)'
            ),
        ],
        env=env,
        cwd=dev_command.home_path,
        check=True,
    )
