import platform
import time
from os.path import normpath
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from briefcase.integrations.android_sdk import AndroidSDK
from briefcase.platforms.android.gradle import GradleRunCommand


@pytest.fixture
def jdk():
    jdk = MagicMock()
    jdk.java_home = Path("/path/to/java")
    return jdk


@pytest.fixture
def run_command(tmp_path, first_app_config, jdk):
    command = GradleRunCommand(base_path=tmp_path)
    command.mock_adb = MagicMock()
    command.mock_adb.pidof = MagicMock(return_value="777")
    command.android_sdk = AndroidSDK(
        command,
        jdk=jdk,
        root_path=Path("/path/to/android_sdk"),
    )
    command.android_sdk.adb = MagicMock(return_value=command.mock_adb)

    command.os = MagicMock()
    command.os.environ = {}
    command.requests = MagicMock()
    command.subprocess = MagicMock()
    command.sys = MagicMock()
    return command


def test_run_existing_device(run_command, first_app_config):
    """An app can be run on an existing device."""
    # Set up device selection to return a running physical device.
    run_command.android_sdk.select_target_device = MagicMock(
        return_value=("exampleDevice", "ExampleDevice", None)
    )
    # Set up app config to have a `-` in the `bundle`, to ensure it gets
    # normalized into a `_` via `package_name`.
    first_app_config.bundle = "com.ex-ample"

    # Invoke run_app
    run_command.run_app(first_app_config, device_or_avd="exampleDevice")

    # select_target_device was invoked with a specific device
    run_command.android_sdk.select_target_device.assert_called_once_with(
        device_or_avd="exampleDevice"
    )

    # The ADB wrapper is created
    run_command.android_sdk.adb.assert_called_once_with(device="exampleDevice")

    # The adb wrapper is invoked with the expected arguments
    run_command.mock_adb.install_apk.assert_called_once_with(
        run_command.binary_path(first_app_config)
    )
    run_command.mock_adb.force_stop_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
    )

    run_command.mock_adb.start_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
        "org.beeware.android.MainActivity",
    )

    run_command.mock_adb.pidof.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}"
    )
    run_command.mock_adb.logcat.assert_called_once_with("777")


def test_run_slow_start(run_command, first_app_config, monkeypatch):
    run_command.android_sdk.select_target_device = MagicMock(
        return_value=("exampleDevice", "ExampleDevice", None)
    )
    run_command.mock_adb.pidof.side_effect = [None, None, "888"]
    monkeypatch.setattr(time, "sleep", MagicMock())

    run_command.run_app(first_app_config, device_or_avd="exampleDevice")

    assert run_command.mock_adb.pidof.mock_calls == [call("com.example.first_app")] * 3
    assert time.sleep.mock_calls == [call(0.5)] * 2
    run_command.mock_adb.logcat.assert_called_once_with("888")


def test_run_created_emulator(run_command, first_app_config):
    """The user can choose to run on a newly created emulator."""
    # Set up device selection to return a completely new emulator
    run_command.android_sdk.select_target_device = MagicMock(
        return_value=(None, None, None)
    )
    run_command.android_sdk.create_emulator = MagicMock(return_value="newDevice")
    run_command.android_sdk.verify_avd = MagicMock()
    run_command.android_sdk.start_emulator = MagicMock(
        return_value=("emulator-3742", "New Device")
    )

    # Invoke run_app
    run_command.run_app(first_app_config)

    # A new emulator was created
    run_command.android_sdk.create_emulator.assert_called_once_with()

    # No attempt was made to verify the AVD (it is pre-verified through
    # the creation process)
    run_command.android_sdk.verify_avd.assert_not_called()

    # The emulator was started
    run_command.android_sdk.start_emulator.assert_called_once_with("newDevice")

    # The ADB wrapper is created
    run_command.android_sdk.adb.assert_called_once_with(device="emulator-3742")

    # The adb wrapper is invoked with the expected arguments
    run_command.mock_adb.install_apk.assert_called_once_with(
        run_command.binary_path(first_app_config)
    )
    run_command.mock_adb.force_stop_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
    )

    run_command.mock_adb.start_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
        "org.beeware.android.MainActivity",
    )

    run_command.mock_adb.logcat.assert_called_once_with("777")


def test_run_idle_device(run_command, first_app_config):
    """The user can choose to run on an idle device."""
    # Set up device selection to return a new device that has an AVD,
    # but not a device ID.
    run_command.android_sdk.select_target_device = MagicMock(
        return_value=(None, "Idle Device", "idleDevice")
    )

    run_command.android_sdk.create_emulator = MagicMock()
    run_command.android_sdk.verify_avd = MagicMock()
    run_command.android_sdk.start_emulator = MagicMock(
        return_value=("emulator-3742", "Idle Device")
    )

    # Invoke run_app
    run_command.run_app(first_app_config)

    # No attempt was made to create a new emulator
    run_command.android_sdk.create_emulator.assert_not_called()

    # The AVD has been verified
    run_command.android_sdk.verify_avd.assert_called_with("idleDevice")

    # The emulator was started
    run_command.android_sdk.start_emulator.assert_called_once_with("idleDevice")

    # The ADB wrapper is created
    run_command.android_sdk.adb.assert_called_once_with(device="emulator-3742")

    # The adb wrapper is invoked with the expected arguments
    run_command.mock_adb.install_apk.assert_called_once_with(
        run_command.binary_path(first_app_config)
    )
    run_command.mock_adb.force_stop_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
    )

    run_command.mock_adb.start_app.assert_called_once_with(
        f"{first_app_config.package_name}.{first_app_config.module_name}",
        "org.beeware.android.MainActivity",
    )

    run_command.mock_adb.logcat.assert_called_once_with("777")


def test_log_file_extra(run_command, monkeypatch):
    """Android commands register a log file extra to list SDK packages."""
    verify = MagicMock(return_value=run_command.android_sdk)
    monkeypatch.setattr(AndroidSDK, "verify", verify)
    monkeypatch.setattr(AndroidSDK, "verify_emulator", MagicMock())

    # Even if one command triggers another, the sdkmanager should only be run once.
    run_command.update_command.verify_tools()
    run_command.verify_tools()

    sdk_manager = "/path/to/android_sdk/cmdline-tools/latest/bin/sdkmanager"
    if platform.system() == "Windows":
        sdk_manager += ".bat"

    run_command.save_log = True
    run_command.subprocess.check_output.assert_not_called()
    run_command.logger.save_log_to_file(run_command)
    run_command.subprocess.check_output.assert_called_once_with(
        [normpath(sdk_manager), "--list_installed"],
        env={
            "ANDROID_SDK_ROOT": str(run_command.android_sdk.root_path),
            "JAVA_HOME": str(run_command.android_sdk.jdk.java_home),
        },
    )
