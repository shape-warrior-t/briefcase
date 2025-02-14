from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import MissingToolError, NetworkFailure
from briefcase.integrations.rcedit import RCEdit


@pytest.fixture
def mock_command(tmp_path):
    command = MagicMock()
    command.host_arch = "wonky"
    command.tools_path = tmp_path / "tools"
    command.tools_path.mkdir()

    return command


def test_verify_exists(mock_command, tmp_path):
    """If RCEdit already exists, verification doesn't download."""
    rcedit_path = tmp_path / "tools" / "rcedit-x64.exe"

    # Mock the existence of an install
    rcedit_path.touch()

    # Create a rcedit wrapper by verification
    rcedit = RCEdit.verify(mock_command)

    # No download occurred
    assert mock_command.download_file.call_count == 0
    assert mock_command.os.chmod.call_count == 0

    # The build command retains the path to the downloaded file.
    assert rcedit.rcedit_path == rcedit_path


def test_verify_does_not_exist_dont_install(mock_command, tmp_path):
    """If RCEdit doesn't exist, and install=False, it is *not* downloaded."""
    # Mock a successful download
    mock_command.download_file.return_value = "new-downloaded-file"

    # True to create a rcedit wrapper by verification.
    # This will fail because it doesn't exist, but installation was disabled.
    with pytest.raises(MissingToolError):
        RCEdit.verify(mock_command, install=False)

    # No download occurred
    assert mock_command.download_file.call_count == 0
    assert mock_command.os.chmod.call_count == 0


def test_verify_does_not_exist(mock_command, tmp_path):
    """If RCEdit doesn't exist, it is downloaded."""
    rcedit_path = tmp_path / "tools" / "rcedit-x64.exe"

    # Mock a successful download
    def side_effect_create_mock_appimage(*args, **kwargs):
        rcedit_path.touch()
        return "new-downloaded-file"

    mock_command.download_file.side_effect = side_effect_create_mock_appimage

    # Create a rcedit wrapper by verification
    rcedit = RCEdit.verify(mock_command)

    # A download is invoked
    mock_command.download_file.assert_called_with(
        url="https://github.com/electron/rcedit/"
        "releases/download/v1.1.1/rcedit-x64.exe",
        download_path=tmp_path / "tools",
        role="RCEdit",
    )

    # The build command retains the path to the downloaded file.
    assert rcedit.rcedit_path == rcedit_path


def test_verify_rcedit_download_failure(mock_command, tmp_path):
    """If RCEdit doesn't exist, but a download failure occurs, an error is
    raised."""
    mock_command.download_file.side_effect = NetworkFailure("mock")

    with pytest.raises(NetworkFailure, match="Unable to mock"):
        RCEdit.verify(mock_command)

    # A download was invoked
    mock_command.download_file.assert_called_with(
        url="https://github.com/electron/rcedit/"
        "releases/download/v1.1.1/rcedit-x64.exe",
        download_path=tmp_path / "tools",
        role="RCEdit",
    )
