import subprocess
import pytest
from Omni.robotlibraries.gdb.gdb_control import *
import json
import os
import shutil

current_file_path = os.path.abspath(__file__)
test_dir = os.path.dirname(current_file_path)
responses_dir = os.path.join(test_dir, "gdb_responses")
temp_folder_path = os.path.join(test_dir, "TempGDB")


def remove_temp_file(file_path):
    if os.path.isfile(file_path):
        os.remove(file_path)


def read_from_json(file):
    with open(file, 'r') as input_data_file:
        data = json.load(input_data_file)
    return data


def setup_session():
    if not os.path.exists(temp_folder_path):
        os.makedirs(temp_folder_path)
    else:
        shutil.rmtree(temp_folder_path)
        os.makedirs(temp_folder_path)


def teardown_session():
    if os.path.exists(temp_folder_path):
        shutil.rmtree(temp_folder_path)


valid_response_mapping = {
    "-gdb-set mi-async on": "mi_async_on_cmd.json",
    "pwd": "pwd.json",
    "-file-exec-and-symbols": "mi_load_cmd_found.json",
    "-gdb-set logging file": "mi_set_log_file_cmd.json",
    "-target-select extended-remote": "mi_connect_cmd.json",
    "monitor version": "monitor_version_openocd.json",
    "monitor help": "monitor_help_segger_gdbserver.json",
    "-target-download": "mi_load_open_ocd.json",
    "-exec-continue": "mi_continue.json",
    "monitor version": "monitor_version_openocd.json",
    "monitor reset halt": "mi_monitor_reset_halt_openocd.json",
    "-exec-interrupt": "mi_exec_interrupt.json",
    "info program": "info_program_running.json",
    "-break-insert": "mi_break_insert.json",
    "-break-list": "mi_bp_list.json",
    "cd": "cd_dir.json",
    "-break-delete":  "mi_bp_del_all.json",
    "-exec-next":  "next_rsp1.json",
    "print /d my_var":  "print_var_dec.json",
    "print /x my_var":  "print_var_hex.json",
    "print /t my_var":  "print_var_bin.json",
    "print /x my_bad_payload_var":  "print_var_bad_payload.json",
    "print /x non_existent_var":  "print_var_symbol_n_found.json",
    "print /x no_exist_struct":  "print_struct_bad2.json",
    "print /x my_struct":  "print_struct_hex.json",
    "my_command":  "my_command.json",
    "-gdb-set logging on":  "mi_set_log_file_cmd.json",
    "-gdb-set logging off":  "mi_set_log_file_cmd.json",
}

response_mapping = dict(valid_response_mapping)


@pytest.fixture(scope="function")
def reset_response_mapping():
    global response_mapping
    response_mapping = dict(valid_response_mapping)
    yield
    response_mapping = dict(valid_response_mapping)


def gdb_write_responses(mi_cmd_to_write, timeout_sec=1, *args, **kwargs):
    for key, filename in response_mapping.items():
        if (key in mi_cmd_to_write):
            responses_file_path = os.path.join(responses_dir, filename)
            return read_from_json(responses_file_path)
    raise Exception("ERROR IN STUB for param: "+mi_cmd_to_write)


@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown():
    setup_session()
    yield
    teardown_session()


@pytest.fixture
def mock_gdb_controller(mocker):
    mock_instance = mocker.MagicMock()
    mock_instance.get_gdb_response.return_value = read_from_json(
        os.path.join(responses_dir, "initial_resp.json"))
    mock_instance.write.side_effect = gdb_write_responses
    mocker.patch('Omni.robotlibraries.gdb.gdb_control.GdbController',
                 return_value=mock_instance)
    yield mock_instance


@pytest.fixture
def gdb_not_installed_mock(mocker):
    side_effect = subprocess.CalledProcessError(
        1, "arm-none-eabi-gdb", "Command 'arm-none-eabi-gdb --version' failed")
    mock_call = mocker.patch('subprocess.check_call', side_effect=side_effect)
    yield mock_call


@pytest.fixture
def gdb_installed_mock(mocker):
    mock_call = mocker.patch('subprocess.check_call', return_value=0)
    yield mock_call


def test_gdb_not_installed_raise_exception(mock_gdb_controller, gdb_not_installed_mock):
    with pytest.raises(FileNotFoundError):
        gdb()


def test_gdb_installed_no_except(mock_gdb_controller, gdb_installed_mock):
    gdb()


def test_gdb_saves_version(mock_gdb_controller, gdb_installed_mock):
    my_instance = gdb()
    assert my_instance.version == "10.3-2021.10"


def test_gdb_saves_working_dir(mock_gdb_controller, gdb_installed_mock):
    my_instance = gdb()
    assert my_instance.working_dir == "/home/erick/Desktop/EITF"


def test_gdb_sets_mi_async_on(mock_gdb_controller, gdb_installed_mock):
    gdb()
    mock_gdb_controller.write.assert_called_with("-gdb-set mi-async on")


def test_gdb_sets_log_file_path(mock_gdb_controller, gdb_installed_mock):
    my_instance = gdb()
    path = "/path/to/log/file"
    my_instance.set_log_file_path(path)
    mock_gdb_controller.write.assert_called_with(
        "-gdb-set logging file "+path)
    assert my_instance.logfile_path == path
    assert my_instance.logfile_dir == os.path.dirname(path)


def test_gdb_sets_log_file_raise_exception_if_error_msg_received(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-gdb-set logging file"] = "mi_set_log_on_cmd_malformed.json"
    my_instance = gdb()
    path = "/path/to/log/file"
    with pytest.raises(GdbResponseError, match=r".*Error on set_log_file_path message from gdb.*"):
        my_instance.set_log_file_path(path)
    mock_gdb_controller.write.assert_called_with(
        "-gdb-set logging file "+path)


def test_gdb_sets_log_file_raise_exception_if_response_malformed(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-gdb-set logging file"] = "mi_set_log_on_cmd_malformed_no_message.json"
    my_instance = gdb()
    path = "/path/to/log/file"
    with pytest.raises(GdbResponseError, match=r".*Unexpected GDB response in set_log_file_path.*"):
        my_instance.set_log_file_path(path)
    mock_gdb_controller.write.assert_called_with(
        "-gdb-set logging file "+path)


def test_gdb_loads_elf(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    path = "/path/to/elf/file"
    my_instance.load_elf_file(path)
    mock_gdb_controller.write.assert_called_with(
        "-file-exec-and-symbols "+path, 10)


def test_gdb_load_elf_raise_exception_if_file_not_valid(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-file-exec-and-symbols"] = "mi_load_cmd_not_found.json"
    my_instance = gdb()
    path = "not/valid/path"
    with pytest.raises(FileNotFoundError, match=r".*No such file or directory..*"):
        my_instance.load_elf_file(path)


def test_gdb_loads_rcv_malformed_msg_raises_and_saves_rsp(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-file-exec-and-symbols"] = "mi_load_cmd_malformed.json"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    path = "/path/to/elf/file"
    with pytest.raises(GdbResponseError, match=r".*Unexpected GDB response in load_elf_file.*"):
        my_instance.load_elf_file(path)
    assert os.path.isfile(temp_folder_path+'/malformed_load_elf_file.json')


def test_gdb_connect(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    mock_gdb_controller.write.assert_any_call(
        "-target-select extended-remote localhost:3333")


def test_gdb_connect_to_openocd(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["monitor version"] = "monitor_version_openocd.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    assert my_instance.connected_to_server == True
    assert my_instance.server == "Open On-Chip Debugger"


def test_gdb_connect_to_segger_gdbserver(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["monitor version"] = "monitor_version_segger_gdbserver.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    assert my_instance.connected_to_server == True
    assert my_instance.server == "SEGGER J-Link GDB Server"


def test_gdb_connect_malformed_msg_raise_exception_and_saves_rsp(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-target-select extended-remote"] = "mi_connect_cmd_generic_error.json"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    with pytest.raises(GdbResponseError, match=r".*Unexpected GDB response in connect.*"):
        my_instance.connect("localhost", "3333")
    assert os.path.isfile(temp_folder_path+'/malformed_connect.json')


def test_gdb_connect_timeout_raise_exception(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    mock_gdb_controller.write.side_effect = GdbTimeoutError(ValueError)
    with pytest.raises(ConnectionError, match=r".*Timeout connecting to localhost:3333.*"):
        my_instance.connect("localhost", "3333")


def test_gdb_flash(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    mock_gdb_controller.write.assert_any_call(
        "-target-download")


def test_gdb_flash_raise_exception_if_not_connected(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.load_elf_file("/path/to/elf/file")
    with pytest.raises(ConnectionError, match=r".*GDBclient is not connected to any server.*"):
        my_instance.flash()


def test_gdb_flash_raise_exception_if_elf_not_loaded(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    with pytest.raises(GdbFlashError, match=r".*No ELF file loaded in GDBclient.*"):
        my_instance.flash()


def test_gdb_flash_malformed_msg_raise_exception_and_saves_rsp(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-target-download"] = "mi_load_cmd_malformed.json"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    with pytest.raises(GdbResponseError, match=r".*Unexpected GDB response in flash.*"):
        my_instance.flash()
    assert os.path.isfile(temp_folder_path+'/malformed_load_elf_file.json')


def test_gdb_continue(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.continue_execution()
    mock_gdb_controller.write.assert_any_call(
        "-exec-continue")


def test_gdb_continue_raise_exception_if_not_connected(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.load_elf_file("/path/to/elf/file")
    with pytest.raises(ConnectionError, match=r".*GDBclient is not connected to any server.*"):
        my_instance.continue_execution()


def test_gdb_continue_raise_exception_if_elf_not_loaded(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    with pytest.raises(GdbFlashError, match=r".*No ELF file loaded in GDBclient.*"):
        my_instance.continue_execution()


def test_gdb_continue_malformed_msg_raise_exception_and_saves_rsp(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_malformed.json"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    with pytest.raises(GdbResponseError, match=r".*Unexpected GDB response in continue_execution.*"):
        my_instance.continue_execution()
    assert os.path.isfile(
        temp_folder_path+'/malformed_continue_execution.json')


def test_gdb_monitor_reset_halt_openocd(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.reset_halt()
    mock_gdb_controller.write.assert_any_call(
        "monitor reset halt")


def test_gdb_monitor_reset_halt_gdbserver_raises_exception(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["monitor version"] = "monitor_version_segger_gdbserver.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    with pytest.raises(NotImplementedError, match=r".*monitor reset halt not implemented for SEGGER J-Link GDB Server.*"):
        my_instance.reset_halt()


def test_gdb_monitor_reset_halt_raise_exception_if_not_connected(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    with pytest.raises(ConnectionError, match=r".*GDBclient is not connected to any server.*"):
        my_instance.reset_halt()


def test_gdb_reset_halt_malformed_msg_raise_exception_and_saves_rsp(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["monitor reset halt"] = "mi_monitor_reset_halt_openocd_malformed.json"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    with pytest.raises(GdbResponseError, match=r".*Unexpected GDB response in reset_halt.*"):
        my_instance.reset_halt()
    assert os.path.isfile(
        temp_folder_path+'/malformed_reset_halt.json')


def test_gdb_pause_correct_call(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.continue_execution()
    my_instance.pause()
    mock_gdb_controller.write.assert_any_call("-exec-interrupt")


def test_gdb_pause_malformed_msg_raise_exception_and_saves_rsp(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-interrupt"] = "mi_monitor_reset_halt_openocd_malformed.json"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.continue_execution()
    with pytest.raises(GdbResponseError, match=r".*Unexpected GDB response in pause.*"):
        my_instance.pause()
    assert os.path.isfile(
        temp_folder_path+'/malformed_pause.json')


def test_gdb_get_program_state_running(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.continue_execution()
    assert my_instance.get_program_state() == "running"


def test_gdb_get_program_state_stopped(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["info program"] = "info_program_stopped.json"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.pause()
    assert my_instance.get_program_state() == "stopped"


def test_gdb_get_program_state_malformed_msg_raise_exception_and_saves_rsp(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["info program"] = "info_program_malformed.json"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.pause()
    with pytest.raises(GdbResponseError, match=r".*Unexpected GDB response in get_program_state.*"):
        my_instance.get_program_state()
    assert os.path.isfile(
        temp_folder_path+'/malformed_get_program_state.json')


def test_gdb_info_program_not_connected_raises_exception(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    with pytest.raises(ConnectionError, match=r".*GDBclient is not connected to any server.*"):
        my_instance.get_program_state()


def test_gdb_set_breakpoint(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    mock_gdb_controller.write.assert_any_call(
        "-break-insert --source MySourceFile.cpp --line 20")
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 21)
    mock_gdb_controller.write.assert_any_call(
        "-break-insert --source MySourceFile.cpp --line 21")


def test_gdb_set_breakpoint_relative_path(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    current_working_directory = os.getcwd()
    source_file_path = test_dir+"/gdb_responses/MySourceFile.cpp"
    source_file_relative_path = os.path.relpath(
        source_file_path, current_working_directory)
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        source_file_relative_path, 20)
    my_instance.insert_breakpoint(
        source_file_relative_path, 21)
    mock_gdb_controller.write.assert_any_call(
        "-break-insert --source MySourceFile.cpp --line 20")
    mock_gdb_controller.write.assert_any_call(
        "-break-insert --source MySourceFile.cpp --line 21")


def test_gdb_set_breakpoint_with_tag(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    source_file_path = test_dir+"/gdb_responses/MySourceFile.cpp"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        source_file_path, tag="TEST TAG A")
    my_instance.insert_breakpoint(
        source_file_path, tag="TEST TAG B")
    mock_gdb_controller.write.assert_any_call(
        "-break-insert --source MySourceFile.cpp --line 16")
    mock_gdb_controller.write.assert_any_call(
        "-break-insert --source MySourceFile.cpp --line 18")


def test_gdb_set_breakpoint_with_tag_and_line(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    source_file_path = test_dir+"/gdb_responses/MySourceFile.cpp"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        source_file_path, tag="TEST TAG A", line_number=16)
    my_instance.insert_breakpoint(
        source_file_path, tag="TEST TAG B", line_number=18)
    mock_gdb_controller.write.assert_any_call(
        "-break-insert --source MySourceFile.cpp --line 16")
    mock_gdb_controller.write.assert_any_call(
        "-break-insert --source MySourceFile.cpp --line 18")


def test_gdb_set_breakpoint_with_tag_and_line_raise_exception_if_tag_and_line_do_not_match(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    source_file_path = test_dir+"/gdb_responses/MySourceFile.cpp"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    with pytest.raises(ValueError, match=r".*Line 29 does not contain \"TEST TAG A\".*"):
        my_instance.insert_breakpoint(
            test_dir+"/gdb_responses/MySourceFile.cpp", tag="TEST TAG A", line_number=29)


def test_gdb_set_breakpoint_with_tag_src_not_found(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    with pytest.raises(FileNotFoundError, match=r".*does not exist.*"):
        my_instance.insert_breakpoint(
            "NotExistingFile.cpp", tag="TEST TAG A")


def test_gdb_set_breakpoint_raises_exception_if_src_not_a_path(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    with pytest.raises(FileNotFoundError, match=r".* or is not a file.*"):
        my_instance.insert_breakpoint(
            "NotAFile", tag="TEST TAG A")


def test_gdb_set_breakpoint_tag_not_found(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    source_file_path = test_dir+"/gdb_responses/MySourceFile.cpp"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    with pytest.raises(TagNotFoundError, match=r".*Tag \"Non Existing Tag\" not found in file.*"):
        my_instance.insert_breakpoint(
            source_file_path, tag="Non Existing Tag")


def test_gdb_set_breakpoint_raises_exception_if_tag_and_line_are_not_set(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    source_file_path = test_dir+"/gdb_responses/MySourceFile.cpp"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    with pytest.raises(ValueError, match=r".*Invalid arguments. line_number or tag or both must be defined.*"):
        my_instance.insert_breakpoint(source_file_path)


def test_gdb_set_breakpoint_raises_exception_if_tag_found_twice_or_more(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    source_file_path = test_dir+"/gdb_responses/MyBadSourceFile.cpp"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    with pytest.raises(TagError, match=r".*Tag \"TEST TAG A\" defined more than once in file.*"):
        my_instance.insert_breakpoint(
            source_file_path, tag="TEST TAG A")


def test_gdb_set_breakpoint_source_file_unkown_by_elf_raise_exception(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-break-insert"] = "mi_break_insert_wrong_file.json"
    source_file_path = test_dir+"/gdb_responses/MyNotUsedSource.cpp"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    with pytest.raises(GdbResponseError, match=r".*No source file named.*defined in the elf file"):
        my_instance.insert_breakpoint(
            source_file_path, 20)


def test_gdb_set_breakpoint_bad_lineNumber_raise_exception(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-break-insert"] = "mi_break_insert_bad_line.json"
    source_file_path = test_dir+"/gdb_responses/MyBadSourceFile.cpp"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    with pytest.raises(GdbResponseError, match=r".*No line 300 in file \".*\". defined in the elf file.*"):
        my_instance.insert_breakpoint(
            source_file_path, 300)


def test_gdb_set_breakpoint_malformed_result_msg_raise_exception(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-break-insert"] = "mi_break_insert_malformed_rsp.json"
    source_file_path = test_dir+"/gdb_responses/MyBadSourceFile.cpp"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    with pytest.raises(GdbResponseError, match=r".*Unexpected result_msg in insert_breakpoint.*"):
        my_instance.insert_breakpoint(
            source_file_path, 10)
    assert os.path.isfile(temp_folder_path+'/malformed_bp_cmd_response.json')


def test_gdb_set_breakpoint_malformed_gdb_response_raise_exception(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-break-insert"] = "mi_break_insert_malformed_gdb_rsp.json"
    source_file_path = test_dir+"/gdb_responses/MyBadSourceFile.cpp"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    with pytest.raises(GdbResponseError, match=r".*Unexpected GDB response in insert_breakpoint.*"):
        my_instance.insert_breakpoint(source_file_path, 20)
    assert os.path.isfile(temp_folder_path+'/malformed_insert_bp.json')


def test_gdb_set_breakpoint_hw(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20, break_type="hardware")
    mock_gdb_controller.write.assert_any_call(
        "-break-insert --source MySourceFile.cpp --line 20 -h")


def test_gdb_set_breakpoint_temp(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20, break_type="temporary")
    mock_gdb_controller.write.assert_any_call(
        "-break-insert --source MySourceFile.cpp --line 20 -t")


def test_gdb_set_breakpoint_invalid_type(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    with pytest.raises(ValueError, match=r".*Invalid break_type argument.*"):
        my_instance.insert_breakpoint(
            test_dir+"/gdb_responses/MySourceFile.cpp", 20, break_type="InvalidType")


def test_gdb_change_directory_changes_working_dir(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.change_working_dir("/a/test/working/dir")
    mock_gdb_controller.write.assert_any_call(
        "cd "+"/a/test/working/dir")
    assert my_instance.working_dir == "/a/test/working/dir"


def test_gdb_change_directory_raise_exception_if_dir_does_not_exist(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["cd"] = "cd_bad_dir.json"
    my_instance = gdb()
    with pytest.raises(FileNotFoundError, match=r".*No such file or directory.*"):
        my_instance.change_working_dir("/a/bad/dir")


def test_gdb_change_directory_malformed_msg_raise_exception_and_saves_rsp(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["cd"] = "cd_malformed.json"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    with pytest.raises(GdbResponseError, match=r".*Unexpected GDB response in change_working_dir.*"):
        my_instance.change_working_dir("/a/bad/dir")
    assert os.path.isfile(
        temp_folder_path+'/malformed_change_working_dir.json')


def test_gdb_continue_until_breakpoint_hit_on_read(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_no_hit_write.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    mock_gdb_controller.get_gdb_response.return_value = read_from_json(
        os.path.join(responses_dir, "mi_continue_stop_break_hit_read.json"))
    my_instance.continue_until_breakpoint(timeout_sec=5)
    mock_gdb_controller.write.assert_any_call(
        "-exec-continue")
    mock_gdb_controller.get_gdb_response.assert_any_call(
        5, True)


def test_gdb_continue_until_breakpoint_hit_on_write(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_hit_write.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    my_instance.continue_until_breakpoint(timeout_sec=5)
    mock_gdb_controller.write.assert_any_call(
        "-exec-continue")
    mock_gdb_controller.get_gdb_response.assert_called_once()


def test_gdb_continue_until_breakpoint_malformed_msg_raise_exception_and_saves_rsp(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_no_hit_write.json"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    mock_gdb_controller.get_gdb_response.return_value = read_from_json(
        os.path.join(responses_dir, "mi_continue_stop_break_no_hit_read_malformed.json"))
    with pytest.raises(GdbResponseError, match=r".*Unexpected GDB response in continue_until_breakpoint.*"):
        my_instance.continue_until_breakpoint(timeout_sec=5)
        assert os.path.isfile(temp_folder_path +
                              '/malformed_continue_until_breakpoint.json')


def test_gdb_continue_until_breakpoint_raise_exception_if_timeout(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_no_hit_write.json"
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    mock_gdb_controller.get_gdb_response.side_effect = GdbTimeoutError
    with pytest.raises(GdbTimeoutError):
        my_instance.continue_until_breakpoint(timeout_sec=1)


def test_gdb_stopped_at_breakpoint_raises_exception_if_not_stopped(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.logfile_dir = temp_folder_path
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    my_instance.continue_execution()
    with pytest.raises(GdbBreakpointNotStopped, match=r".*Program is not stopped at breakpoint.*"):
        my_instance.stopped_at_breakpoint_with_tag(
            test_dir+"/gdb_responses/MySourceFile.cpp", "TEST TAG A")


def test_gdb_stopped_at_breakpoint_with_tag_returns_true_if_tag_hit_breakpoint_index_1(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_no_hit_write.json"
    response_mapping["info program"] = "info_prog_stoped_bp.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    mock_gdb_controller.get_gdb_response.return_value = read_from_json(
        os.path.join(responses_dir, "mi_continue_stop_break_hit_read.json"))
    my_instance.continue_until_breakpoint(timeout_sec=5)
    tag_hit = my_instance.stopped_at_breakpoint_with_tag(
        test_dir+"/gdb_responses/MySourceFile.cpp", "TEST TAG A")
    assert tag_hit == True


def test_gdb_stopped_at_breakpoint_with_tag_returns_true_if_tag_hit_breakpoint_index_2(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_no_hit_write.json"
    response_mapping["info program"] = "info_prog_stoped_bp2.json"
    response_mapping["-break-list"] = "mi_bp_list2.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    mock_gdb_controller.get_gdb_response.return_value = read_from_json(
        os.path.join(responses_dir, "mi_continue_stop_break_hit_read.json"))
    my_instance.continue_until_breakpoint(timeout_sec=5)
    tag_hit = my_instance.stopped_at_breakpoint_with_tag(
        test_dir+"/gdb_responses/MySourceFile.cpp", "TEST TAG E")
    assert tag_hit == True


def test_gdb_stopped_at_breakpoint_with_tag_raise_exception_if_invalid_index(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_no_hit_write.json"
    response_mapping["info program"] = "info_prog_stoped_bp3.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    mock_gdb_controller.get_gdb_response.return_value = read_from_json(
        os.path.join(responses_dir, "mi_continue_stop_break_hit_read.json"))
    my_instance.continue_until_breakpoint(timeout_sec=5)
    with pytest.raises(GdbResponseError, match=r".*Invalid breakpoint index.*in breakpoints list.*"):
        my_instance.stopped_at_breakpoint_with_tag(
            test_dir+"/gdb_responses/MySourceFile.cpp", "TEST TAG E")


def test_gdb_stopped_at_breakpoint_with_tag_raises_exception_if_tag_not_found(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_no_hit_write.json"
    response_mapping["info program"] = "info_prog_stoped_bp.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", tag="TEST TAG A")
    mock_gdb_controller.get_gdb_response.return_value = read_from_json(
        os.path.join(responses_dir, "mi_continue_stop_break_hit_read.json"))
    my_instance.continue_until_breakpoint(timeout_sec=1)
    with pytest.raises(TagNotFoundError):
        my_instance.stopped_at_breakpoint_with_tag(
            test_dir+"/gdb_responses/MySourceFile.cpp", "MY WRONG TAG")


def test_gdb_delete_all_bp_deletes_all_breakpoints(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", tag="TEST TAG A")
    my_instance.delete_all_breakpoints()


def test_gdb_delete_all_bp_deletes_malformed_msg_raise_exception_and_saves_rsp(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-break-delete"] = "mi_bp_del_all_malformed.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", tag="TEST TAG A")
    with pytest.raises(GdbResponseError, match=r".*Unexpected GDB response in delete_all_breakpoints.*"):
        my_instance.delete_all_breakpoints()
        assert os.path.isfile(
            temp_folder_path + '/malformed_delete_all_breakpoints.json')


def test_gdb_executes_next(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", tag="TEST TAG A")
    my_instance.next()
    mock_gdb_controller.write.assert_called_with('-exec-next')


def test_gdb_next_malformed_msg_raise_exception_and_saves_rsp(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_no_hit_write.json"
    response_mapping["info program"] = "info_prog_stoped_bp.json"
    response_mapping["-exec-next"] = "next_rsp_malformed.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    mock_gdb_controller.get_gdb_response.return_value = read_from_json(
        os.path.join(responses_dir, "mi_continue_stop_break_hit_read.json"))
    my_instance.continue_until_breakpoint(timeout_sec=5)
    my_instance.stopped_at_breakpoint_with_tag(
        test_dir+"/gdb_responses/MySourceFile.cpp", "TEST TAG A")
    with pytest.raises(GdbResponseError, match=r".*Unexpected GDB response in next.*"):
        my_instance.next()
        assert os.path.isfile(temp_folder_path + '/malformed_next.json')


def test_gdb_next_raises_exception_if_gdb_rsp_malformed_not_end_stepping_range(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_no_hit_write.json"
    response_mapping["info program"] = "info_prog_stoped_bp.json"
    response_mapping["-exec-next"] = "next_rsp_malformed2.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    mock_gdb_controller.get_gdb_response.return_value = read_from_json(
        os.path.join(responses_dir, "mi_continue_stop_break_hit_read.json"))
    my_instance.continue_until_breakpoint(timeout_sec=5)
    my_instance.stopped_at_breakpoint_with_tag(
        test_dir+"/gdb_responses/MySourceFile.cpp", "TEST TAG A")
    with pytest.raises(GdbResponseError, match=r".*Unexpected GDB response in next.*"):
        my_instance.next()
        assert os.path.isfile(temp_folder_path + '/malformed_next.json')


def test_gdb_next_does_not_raise_exception_if_notify_msg_is_in_other_position(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-next"] = "next_rsp2.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", tag="TEST TAG A")
    my_instance.next()
    mock_gdb_controller.write.assert_called_with('-exec-next')


def test_gdb_get_variable_dec_value_correct_call(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_no_hit_write.json"
    response_mapping["info program"] = "info_prog_stoped_bp.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    mock_gdb_controller.get_gdb_response.return_value = read_from_json(
        os.path.join(responses_dir, "mi_continue_stop_break_hit_read.json"))
    my_instance.continue_until_breakpoint(timeout_sec=5)
    my_instance.stopped_at_breakpoint_with_tag(
        test_dir+"/gdb_responses/MySourceFile.cpp", "TEST TAG A")
    a = my_instance.get_variable_value("my_var", "dec")
    mock_gdb_controller.write.assert_called_with('print /d my_var')


def test_gdb_get_variable_hex_value_correct_call(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_no_hit_write.json"
    response_mapping["info program"] = "info_prog_stoped_bp.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    mock_gdb_controller.get_gdb_response.return_value = read_from_json(
        os.path.join(responses_dir, "mi_continue_stop_break_hit_read.json"))
    my_instance.continue_until_breakpoint(timeout_sec=5)
    my_instance.stopped_at_breakpoint_with_tag(
        test_dir+"/gdb_responses/MySourceFile.cpp", "TEST TAG A")
    a = my_instance.get_variable_value("my_var", "hex")
    mock_gdb_controller.write.assert_called_with('print /x my_var')


def test_gdb_get_variable_bin_value_correct_call(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_no_hit_write.json"
    response_mapping["info program"] = "info_prog_stoped_bp.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    mock_gdb_controller.get_gdb_response.return_value = read_from_json(
        os.path.join(responses_dir, "mi_continue_stop_break_hit_read.json"))
    my_instance.continue_until_breakpoint(timeout_sec=5)
    my_instance.stopped_at_breakpoint_with_tag(
        test_dir+"/gdb_responses/MySourceFile.cpp", "TEST TAG A")
    a = my_instance.get_variable_value("my_var", "bin")
    mock_gdb_controller.write.assert_called_with('print /t my_var')


def test_gdb_get_variable_invalid_format_raise_exception(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_no_hit_write.json"
    response_mapping["info program"] = "info_prog_stoped_bp.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    mock_gdb_controller.get_gdb_response.return_value = read_from_json(
        os.path.join(responses_dir, "mi_continue_stop_break_hit_read.json"))
    my_instance.continue_until_breakpoint(timeout_sec=5)
    my_instance.stopped_at_breakpoint_with_tag(
        test_dir+"/gdb_responses/MySourceFile.cpp", "TEST TAG A")
    with pytest.raises(ValueError):
        my_instance.get_variable_value("my_var", "Not_Valid_Value")


def test_gdb_get_variable_return_dec_value(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_no_hit_write.json"
    response_mapping["info program"] = "info_prog_stoped_bp.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    mock_gdb_controller.get_gdb_response.return_value = read_from_json(
        os.path.join(responses_dir, "mi_continue_stop_break_hit_read.json"))
    my_instance.continue_until_breakpoint(timeout_sec=5)
    my_instance.stopped_at_breakpoint_with_tag(
        test_dir+"/gdb_responses/MySourceFile.cpp", "TEST TAG A")
    variable_my_var = my_instance.get_variable_value("my_var", "dec")
    assert '3' == variable_my_var


def test_gdb_get_variable_return_hex_value(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_no_hit_write.json"
    response_mapping["info program"] = "info_prog_stoped_bp.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    mock_gdb_controller.get_gdb_response.return_value = read_from_json(
        os.path.join(responses_dir, "mi_continue_stop_break_hit_read.json"))
    my_instance.continue_until_breakpoint(timeout_sec=5)
    my_instance.stopped_at_breakpoint_with_tag(
        test_dir+"/gdb_responses/MySourceFile.cpp", "TEST TAG A")
    variable_my_var = my_instance.get_variable_value("my_var", "hex")
    assert '0x3' == variable_my_var


def test_gdb_get_variable_return_bin_value(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_no_hit_write.json"
    response_mapping["info program"] = "info_prog_stoped_bp.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    mock_gdb_controller.get_gdb_response.return_value = read_from_json(
        os.path.join(responses_dir, "mi_continue_stop_break_hit_read.json"))
    my_instance.continue_until_breakpoint(timeout_sec=5)
    my_instance.stopped_at_breakpoint_with_tag(
        test_dir+"/gdb_responses/MySourceFile.cpp", "TEST TAG A")
    variable_my_var = my_instance.get_variable_value("my_var", "bin")
    assert '11' == variable_my_var


def test_gdb_get_variable_raise_exception_empty_payload(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_no_hit_write.json"
    response_mapping["info program"] = "info_prog_stoped_bp.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    mock_gdb_controller.get_gdb_response.return_value = read_from_json(
        os.path.join(responses_dir, "mi_continue_stop_break_hit_read.json"))
    my_instance.continue_until_breakpoint(timeout_sec=5)
    my_instance.stopped_at_breakpoint_with_tag(
        test_dir+"/gdb_responses/MySourceFile.cpp", "TEST TAG A")
    with pytest.raises(GdbResponseError, match=r".*Unexpected GDB response in get_variable_value. Invalid payload format*"):
        my_instance.get_variable_value("my_bad_payload_var", "hex")


def test_gdb_get_variable_raise_exception_symbol_not_found(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_no_hit_write.json"
    response_mapping["info program"] = "info_prog_stoped_bp.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    mock_gdb_controller.get_gdb_response.return_value = read_from_json(
        os.path.join(responses_dir, "mi_continue_stop_break_hit_read.json"))
    my_instance.continue_until_breakpoint(timeout_sec=5)
    my_instance.stopped_at_breakpoint_with_tag(
        test_dir+"/gdb_responses/MySourceFile.cpp", "TEST TAG A")
    with pytest.raises(GdbResponseError, match=r".*Unexpected GDB response in get_variable_value. Invalid payload format*"):
        my_instance.get_variable_value("non_existent_var", "hex")


def test_gdb_get_variable_raise_exception_symbol_not_found_for_structures(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_no_hit_write.json"
    response_mapping["info program"] = "info_prog_stoped_bp.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    mock_gdb_controller.get_gdb_response.return_value = read_from_json(
        os.path.join(responses_dir, "mi_continue_stop_break_hit_read.json"))
    my_instance.continue_until_breakpoint(timeout_sec=5)
    my_instance.stopped_at_breakpoint_with_tag(
        test_dir+"/gdb_responses/MySourceFile.cpp", "TEST TAG A")
    with pytest.raises(GdbResponseError, match=r".*Unexpected GDB response in get_variable_value. Invalid payload format*"):
        my_instance.get_variable_value("no_exist_struct", "hex")


def test_gdb_get_struct_as_hex_return_struct(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-exec-continue"] = "mi_continue_stop_break_no_hit_write.json"
    response_mapping["info program"] = "info_prog_stoped_bp.json"
    my_instance = gdb()
    my_instance.connect("localhost", "3333")
    my_instance.load_elf_file("/path/to/elf/file")
    my_instance.flash()
    my_instance.insert_breakpoint(
        test_dir+"/gdb_responses/MySourceFile.cpp", 20)
    mock_gdb_controller.get_gdb_response.return_value = read_from_json(
        os.path.join(responses_dir, "mi_continue_stop_break_hit_read.json"))
    my_instance.continue_until_breakpoint(timeout_sec=5)
    my_instance.stopped_at_breakpoint_with_tag(
        test_dir+"/gdb_responses/MySourceFile.cpp", "TEST TAG A")
    variable_my_var = my_instance.get_variable_value("my_struct", "hex")
    assert '{var1 = 0x3, var2 = 0xc, var3 = 0x40020c00}' == variable_my_var


def test_gdb_creates_json(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    file_path = './my_command_generated.json'
    my_instance = gdb()
    my_instance.send_command("my_command", "my_command_generated.json")
    mock_gdb_controller.write.assert_any_call("my_command")
    assert os.path.exists(file_path), f"File '{file_path}' does not exist."
    os.remove(file_path)


def test_gdb_send_command_creates_json_with_eq_content(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    file_path = './my_command_generated.json'
    my_instance = gdb()
    my_instance.send_command("my_command", "my_command_generated.json")
    mock_gdb_controller.write.assert_any_call("my_command")
    assert os.path.exists(file_path), f"File '{file_path}' does not exist."
    os.remove(file_path)


def test_gdb_log_file_change_name_correct_call(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    log_file_path = temp_folder_path+'/my_log_file.txt'
    my_instance = gdb()
    my_instance.set_log_file_path(log_file_path)
    mock_gdb_controller.write.assert_any_call(
        "-gdb-set logging file "+log_file_path)


def test_gdb_log_file_raise_exception_on_error(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-gdb-set logging file"] = "mi_set_log_file_cmd_malformed.json"
    log_file_path = temp_folder_path+'/my_log_file.txt'
    my_instance = gdb()
    with pytest.raises(GdbResponseError, match=r".*Unexpected GDB response in set_log_file_path*"):
        my_instance.set_log_file_path(log_file_path)


def test_gdb_log_file_start_log(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    log_file_path = temp_folder_path+'/my_log_file.txt'
    my_instance = gdb()
    my_instance.set_log_file_path(log_file_path)
    my_instance.start_logging()
    mock_gdb_controller.write.assert_any_call("-gdb-set logging on")


def test_gdb_log_file_start_log_gdb_new(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-gdb-set logging on"] = "mi_set_log_file_cmd_2.json"
    log_file_path = temp_folder_path+'/my_log_file.txt'
    my_instance = gdb()
    my_instance.set_log_file_path(log_file_path)
    my_instance.start_logging()
    mock_gdb_controller.write.assert_any_call("-gdb-set logging on")


def test_gdb_log_file_start_raise_exception_on_error_rsp(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-gdb-set logging on"] = "mi_set_log_file_cmd_error.json"
    log_file_path = temp_folder_path+'/my_log_file.txt'
    my_instance = gdb()
    my_instance.set_log_file_path(log_file_path)
    with pytest.raises(GdbResponseError, match=r".*Error on start_logging message from gdb*"):
        my_instance.start_logging()


def test_gdb_log_file_start_malformed_msg_raise_exception_and_saves_rsp(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-gdb-set logging on"] = "mi_set_log_file_cmd_malformed.json"
    log_file_path = temp_folder_path+'/my_log_file.txt'
    my_instance = gdb()
    my_instance.set_log_file_path(log_file_path)
    with pytest.raises(GdbResponseError, match=r".*Unexpected GDB response in start_logging.*"):
        my_instance.start_logging()
        assert os.path.isfile(
            temp_folder_path + '/malformed_start_logging.json')


def test_gdb_log_file_stop_log(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    log_file_path = temp_folder_path+'/my_log_file.txt'
    my_instance = gdb()
    my_instance.set_log_file_path(log_file_path)
    my_instance.stop_logging()
    mock_gdb_controller.write.assert_any_call("-gdb-set logging off")


def test_gdb_log_file_stop_raise_exception_on_error_rsp(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-gdb-set logging off"] = "mi_set_log_file_cmd_error.json"
    log_file_path = temp_folder_path+'/my_log_file.txt'
    my_instance = gdb()
    my_instance.set_log_file_path(log_file_path)
    with pytest.raises(GdbResponseError, match=r'.*Error on stop_logging message from gdb.*'):
        my_instance.stop_logging()


def test_gdb_log_file_stop_raise_exception_on_malformed_rsp(mock_gdb_controller, gdb_installed_mock, reset_response_mapping):
    response_mapping["-gdb-set logging off"] = "mi_set_log_file_cmd_malformed.json"
    log_file_path = temp_folder_path+'/my_log_file.txt'
    my_instance = gdb()
    my_instance.set_log_file_path(log_file_path)
    with pytest.raises(GdbResponseError, match=r'.*Unexpected GDB response in stop_logging.*'):
        my_instance.stop_logging()
        assert os.path.isfile(
            temp_folder_path + '/malformed_stop_logging.json')
