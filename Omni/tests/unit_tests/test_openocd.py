import os
import unittest
from unittest.mock import patch, ANY, MagicMock
import shutil
from pathlib import Path
from ...applications.Openocd import *
from ...process_manager.process_manager import *

folder_path = "./TempOCD"
DummyProcess_file = "./TempOCD/DummyProcess.json"

openocd_path = "/path/to/openocd"
board_cfg_file_path = "/board/board.cfg"
interface_cfg_file_path = "/interface/interface.cfg"
open_ocd_log_path = folder_path+"/Openlog.txt"
arguments =  ["-f", "DummyArg1.cfg", "-f", "DummyArg2.cfg"]

class TestOpenocd(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        else:
            shutil.rmtree(folder_path)
            os.makedirs(folder_path)

    def test_launch_openocd_raises_exception_if_process_file_dont_exist(self):
        with self.assertRaises(FileNotFoundError):
            launch_openocd(os.path.abspath(DummyProcess_file), openocd_path, arguments, open_ocd_log_path)


    @patch('subprocess.Popen', side_effect=None)
    def test_launch_openocd_dont_raise_exception_if_process_file_exist(self, mock_subprocess):
        create_config_file(DummyProcess_file)
        launch_openocd(os.path.abspath(DummyProcess_file), openocd_path, arguments, open_ocd_log_path)
        os.remove(DummyProcess_file)

    def test_launch_openocd_raises_exception_if_file_has_bad_format(self):
        file_path = "TempOCD/my_bad_format_file.json"
        with open(file_path, 'w') as f:
            f.write('This is a dummy file.')
        with self.assertRaises(ValueError):
            launch_openocd(os.path.abspath(file_path), openocd_path, arguments, open_ocd_log_path)
        os.remove(file_path)

    @patch('subprocess.Popen', side_effect=None)
    def test_launches_openocd_application_correct_call(self, mock_subprocess):
        create_config_file(DummyProcess_file)
        cmd_call = [openocd_path]+ arguments
        launch_openocd(os.path.abspath(DummyProcess_file), openocd_path, arguments, open_ocd_log_path)
        mock_subprocess.assert_called_with(
            cmd_call, stdout=ANY, stderr=ANY)
        os.remove(DummyProcess_file)

    @patch('subprocess.Popen', side_effect=None)
    def test_launches_openocd_application_correct_log(self, mock_subprocess):
        create_config_file(DummyProcess_file)
        launch_openocd(os.path.abspath(DummyProcess_file), openocd_path, arguments, open_ocd_log_path)
        cmd_call = [openocd_path]+ arguments
        mock_subprocess.assert_called_with(
            cmd_call, stdout=ANY, stderr=ANY)
        call_args = mock_subprocess.call_args
        stdout_value = call_args[1]['stdout']
        stderr_value = call_args[1]['stderr']
        assert (stdout_value.name == open_ocd_log_path)
        assert (stderr_value.name == open_ocd_log_path)
        os.remove(DummyProcess_file)

    @patch('subprocess.Popen', side_effect=None)
    @patch('Omni.process_manager.process_manager.append_process_data_to_file', side_effect=None)
    def test_launches_openocd_creates_correct_process_entry(self, mock_append_process_data, mock_subprocess):
        mock_popen_instance = MagicMock()
        mock_popen_instance.pid = 12345
        mock_subprocess.return_value = mock_popen_instance
        create_config_file(DummyProcess_file)
        launch_openocd(os.path.abspath(DummyProcess_file), openocd_path, arguments, open_ocd_log_path)
        call_args = mock_append_process_data.call_args
        open_ocd_process_entry = call_args[0][0]
        assert (open_ocd_process_entry["application"] == "Open OCD")
        assert (open_ocd_process_entry["pid"] == "12345")
        assert (open_ocd_process_entry["log_file"] == open_ocd_log_path)
        assert (open_ocd_process_entry["process_call"] ==
                "/path/to/openocd -f DummyArg1.cfg -f DummyArg2.cfg")
        assert (open_ocd_process_entry["port"] == 3333)
        assert (open_ocd_process_entry["pgrep_string"] == "openocd")
        assert (open_ocd_process_entry["status"] == "started")
        os.remove(DummyProcess_file)

    # def test_verify_openocdLaunched_no_exception_if_openocd_started(self):
    #     open_ocd_log_path = "./Omni/tests/unit_tests/openocd_test_data/OpenOCD_LOG_started.txt"
    #     absolute_path = Path(open_ocd_log_path).resolve()
    #     verify_openocd(absolute_path)

    # def test_verify_openocdLaunched_raise_exception_if_openocd_not_started(self):
    #     open_ocd_log_path = "./Omni/tests/unit_tests/openocd_test_data/OpenOCD_LOG_not_started.txt"
    #     absolute_path = Path(open_ocd_log_path).resolve()
    #     with self.assertRaises(ProcessStartupError):
    #         verify_openocd(absolute_path)

    @classmethod
    def teardown_class(cls):
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
