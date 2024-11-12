import json
import pytest
from unittest import mock
from unittest.mock import ANY, MagicMock
from Omni.applications.GDBServer import launch_gdbserver
# from Omni.process_manager.process_manager import create_config_file
import pytest
import pathlib
from pathlib import Path
import shutil
import os

temporary_folder = pathlib.Path("./TempGDBServer")
log_file_path = temporary_folder / "GDBServerLog.txt"


def create_config_file(filename):
    if (check_file_exists(filename) == True):
        _error_msg_file_already_exists(filename)
    else:
        _create_empty_process_file(filename)

def check_file_exists(file_path):
    return os.path.isfile(file_path)


def _error_msg_file_already_exists(filename):
    raise FileExistsError(f"Error: File '{filename}' already exists!")

def _create_empty_process_file(filename):
    with open(filename, "w") as json_file:
        json.dump([], json_file)


@pytest.fixture(scope="session", autouse=True)
def create_temp_folder():
    folder_name = temporary_folder
    folder_name.mkdir(parents=True, exist_ok=True)
    yield


@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_folder():
    yield
    if os.path.exists(temporary_folder):
        shutil.rmtree(temporary_folder)


@pytest.fixture
def mock_gdbserver_process_popen(mocker):
    mock = mocker.patch('subprocess.Popen', spec=True)
    mock.return_value = MagicMock()
    mock.return_value.pid = 1234
    return mock


@pytest.fixture
def create_dummy_process_file():
    process_file_path = temporary_folder / "DummyProcess.json"
    create_config_file(process_file_path)
    yield process_file_path
    os.remove(process_file_path)


@pytest.fixture
def create_bad_format_process_file():
    bad_format_process_file_path = temporary_folder / "my_bad_format_file.json"
    with open(bad_format_process_file_path, 'w') as f:
        f.write('This is a dummy file.')
    yield bad_format_process_file_path
    os.remove(bad_format_process_file_path)


@pytest.fixture
def mock_append_process_data_to_file(mocker):
    mock = mocker.patch(
        'Omni.process_manager.process_manager.append_process_data_to_file', side_effect=None)
    return mock


@pytest.fixture
def mock_gdbserver_process(mocker):
    mock = mocker.patch(
        'subprocess.Popen', spec=True)
    mock.return_value = MagicMock()
    mock.return_value.pid = '1234'
    return mock


def test_launch_gdbserver_raises_exception_if_process_file_dont_exist():
    with pytest.raises(FileNotFoundError):
        launch_gdbserver('not_existing_process_file', gdbserver_log_file=log_file_path, gdbserver_path='JLinkGDBServerCLExe',
                         jlink_interface='USB', device='STM32F407VG', port='2331', board_interface_type='SWD')


def test_launch_gdbserver_raises_exception_if_file_has_bad_format(create_bad_format_process_file):
    bad_format_process_file_path = create_bad_format_process_file
    with pytest.raises(ValueError):
        launch_gdbserver(bad_format_process_file_path, gdbserver_log_file=log_file_path, gdbserver_path='JLinkGDBServerCLExe',
                         jlink_interface='USB', device='STM32F407VG', port='2331', board_interface_type='SWD')


@pytest.mark.parametrize("gdbserver_path, jlink_interface, device, board_interface_type, port,expected_args", [
    ('JLinkGDBServerCLExe', 'USB', 'STM32F407VG', 'SWD', '2331', ['JLinkGDBServerCLExe', '-select', 'USB', '-device', 'STM32F407VG', '-if', 'SWD', '-port', '2331']),
    ('JLinkGDBServerCLExe', 'USB', 'STM32F407VGTX', 'JTAG', '2332', ['JLinkGDBServerCLExe', '-select', 'USB', '-device', 'STM32F407VGTX', '-if', 'JTAG', '-port', '2332'])
])
def test_launch_gdbserver_host_correct_call(mock_gdbserver_process_popen, gdbserver_path, jlink_interface, device, board_interface_type, port, expected_args, create_dummy_process_file):
    dummy_process_file_path = create_dummy_process_file
    launch_gdbserver(dummy_process_file_path, gdbserver_log_file=log_file_path, gdbserver_path=gdbserver_path,
                     jlink_interface=jlink_interface, device=device, port=port, board_interface_type=board_interface_type)
    mock_gdbserver_process_popen.assert_called_once_with(
        expected_args, stdout=ANY, stderr=ANY)


def test_launch_gdbserver_host_correct_call_extra_parameters(mock_gdbserver_process_popen, create_dummy_process_file):
    dummy_process_file_path = create_dummy_process_file
    extra_gdbserver_parameters = "-endian little -speed auto"
    expected_call = ['JLinkGDBServerCLExe', '-select', 'USB', '-device', 'STM32F407VG', '-if', 'SWD', '-port', '2331']+extra_gdbserver_parameters.split(' ')
    launch_gdbserver(dummy_process_file_path, gdbserver_log_file=log_file_path, gdbserver_path='JLinkGDBServerCLExe', jlink_interface='USB', device='STM32F407VG',
                     board_interface_type='SWD', port='2331', extra_parameters=extra_gdbserver_parameters)
    mock_gdbserver_process_popen.assert_called_once_with(
        expected_call, stdout=ANY, stderr=ANY)


def test_launch_gdbserver_host_append_gdbserver_entry_to_log(mock_gdbserver_process, create_dummy_process_file, mock_append_process_data_to_file):
    dummy_process_file_path = create_dummy_process_file
    launch_gdbserver(dummy_process_file_path, gdbserver_log_file=log_file_path, gdbserver_path='JLinkGDBServerCLExe', jlink_interface='USB', device='STM32F407VG',
                     board_interface_type='SWD', port='2331')
    launch_gdbserver_process_data_args = mock_append_process_data_to_file.call_args[0][0]

    assert (
        launch_gdbserver_process_data_args["application"] == "JLinkGDBServerCL")
    assert (launch_gdbserver_process_data_args["pid"]
            == mock_gdbserver_process.return_value.pid)
    assert (
        launch_gdbserver_process_data_args["log_file"] == str(log_file_path))
    assert (
        launch_gdbserver_process_data_args["process_call"] == "JLinkGDBServerCLExe -select USB -device STM32F407VG -if SWD -port 2331")
    assert (launch_gdbserver_process_data_args["port"] == '2331')
    assert (
        launch_gdbserver_process_data_args["pgrep_string"] == "JLinkGDBServerCL")
