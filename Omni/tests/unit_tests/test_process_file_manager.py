import os
import unittest
from unittest.mock import patch, MagicMock, call, ANY
from pathlib import Path
import pytest
import json
import shutil
import psutil
from os.path import isfile

from ...process_manager.process_manager import ProcessManager
from ...process_manager.process_manager import PortClosedError

current_file_path = os.path.dirname(os.path.abspath(__file__))
test_data_dir_path = Path(current_file_path) / "process_manager_test_data"
temp_dir_path = test_data_dir_path / "Temp"


def load_processes_from_data_file(data_file):
    with open(data_file, "r") as file:
            json_data = json.load(file)
    return json_data

def del_temp():
    if os.path.exists(temp_dir_path):
        shutil.rmtree(temp_dir_path)


class TestProcessManager(unittest.TestCase):

    @classmethod
    def setup_class(cls):
        if not os.path.exists(temp_dir_path):
            os.makedirs(temp_dir_path)
        else:
            shutil.rmtree(temp_dir_path)
            os.makedirs(temp_dir_path)

    def test_process_manager_raises_if_config_file_doesnt_exists(self):
            """
            User tries to create a ProcessManager object with a non-existing configuration file.
            Raises:
                FileNotFoundError: If the configuration file does not exist.
            """
            with pytest.raises(FileNotFoundError):
                malformed_process_cfg_file = test_data_dir_path / "does_not_exists.json"
                ProcessManager(malformed_process_cfg_file)


    def test_process_config_file_is_malfomed_no_backend_processes_data_file(self):
        """
        User tries to create a ProcessManager object with a malformed 
        configuration file. The field 'backend_processes_data_file' is missing.
        Raises:
        KeyError: If the configuration file does not exist.
        """
        with pytest.raises(KeyError):
            malformed_process_cfg_file = test_data_dir_path / "backend_processes_malformed1.json"
            ProcessManager(malformed_process_cfg_file)


    def test_create_backend_processes_data_file_raise_if_file_exists(self):
        """
        User tries to create a backend_processes_data_file but the file already 
        exists.
        Raises:
        RuntimeError: If the file already exists.
        """
        existing_file = test_data_dir_path / "my_existing_file.json"
        assert isfile(existing_file)
        with pytest.raises(RuntimeError,match="File '.*' already exists!"):
            malformed_process_cfg_file = test_data_dir_path / "backend_processes_malformed2.json"
            manager=ProcessManager(malformed_process_cfg_file)
            manager.create_backend_processes_data_file()
    
    def test_create_backend_processes_create_data_file_overwrite_active(self):
        """
        User tries to create a backend_processes_data_file, the file already 
        exists and overwrite is active.
        """
        malformed_process_cfg_file = test_data_dir_path / "backend_processes_malformed4.json"
        existing_file = test_data_dir_path / "dummy.json"
        manager=ProcessManager(malformed_process_cfg_file)
        assert isfile(existing_file)
        manager.create_backend_processes_data_file(overwrite_data_file=True)

    def test_launch_processes_with_bad_process_config(self):
        """
        User tries to launch a process but one of the processes configuraitons from backend_processes_config.json
        is missing the entry port.
        """
        process_manager = ProcessManager(test_data_dir_path / "backend_processes_malformed3.json")
        with pytest.raises(ValueError, match=r"Entry '.*' is mandatory\.\s*\n.*"):
            process_manager.launch_processes()
    
    @patch('Omni.process_manager.process_manager.subprocess.Popen')
    def test_launch_processes_fail_process(self, mock_popen):
        """
        User tries to launches the processes and a process fails to launch.
        """
        del_temp()
        mock_popen_instance = MagicMock()
        mock_popen.return_value = mock_popen_instance
        mock_popen_instance.pid = 1234
        # The return code is 0, which means the process was terminated successfully
        mock_popen_instance.poll.return_value = 0
        process_manager = ProcessManager(test_data_dir_path / "backend_processes_config.json")
        process_manager.create_backend_processes_data_file(temp_dir_path)
        with pytest.raises(RuntimeError, match="Process '.*' has stopped with return code .*"):
            process_manager.launch_processes()

    @patch('Omni.process_manager.process_manager.psutil.net_connections')
    @patch('Omni.process_manager.process_manager.subprocess.Popen')
    def test_launch_processes(self, mock_popen,mock_net_connections):
        """
        Verifies that when the user initiates the launch of backend processes, the expected system calls are made 
        to start each process, the relevant process data is saved accurately to the data file and the ports are verified 
        if open.
        """
        del_temp()
        mock_popen_instance = MagicMock()
        mock_popen.return_value = mock_popen_instance
        mock_popen_instance.pid = 1234
        mock_popen_instance.poll.return_value = None
        mock_conn1 = MagicMock()
        mock_conn1.laddr = MagicMock(port=7777)
        mock_conn2 = MagicMock()
        mock_conn2.laddr = MagicMock(port=44444)
        mock_net_connections.return_value = [mock_conn1, mock_conn2]

        process_manager = ProcessManager(test_data_dir_path / "backend_processes_config.json")
        process_manager.create_backend_processes_data_file(temp_dir_path)
        process_manager.launch_processes()
        process_manager.verify_open_ports()
        expected_calls = [
                    call(['/path/to/MyApplication', '-a', 'arg1', '-b', 'arg2'], stdout=ANY, stderr=ANY),
                    call(['/path/to/AnotherApp', '-c', 'argXXX', '-d', 'argZZZZ'], stdout=ANY, stderr=ANY)
                ]
        mock_popen.assert_has_calls(expected_calls, any_order=True)
        saved_processes=load_processes_from_data_file(temp_dir_path / "my_backend_processes_status.json")
        assert len(saved_processes) == 2
        self.assertEqual(saved_processes[0]["name"], "MyApplication")
        self.assertEqual(saved_processes[0]["pid"], "1234")
        self.assertEqual(saved_processes[0]["log_file"], "LOG.txt")
        self.assertEqual(saved_processes[0]["port"], "7777")
        self.assertEqual(saved_processes[1]["name"], "AnotherApp")
        self.assertEqual(saved_processes[1]["pid"], "1234")
        self.assertEqual(saved_processes[1]["log_file"], "another_app.log")
        self.assertEqual(saved_processes[1]["port"], "44444")
        self.assertEqual(saved_processes[1]["status"], "running")


    @patch('Omni.process_manager.process_manager.psutil.net_connections')
    @patch('Omni.process_manager.process_manager.subprocess.Popen')
    def test_raises_on_closed_port(self, mock_popen, mock_net_connections):
        """
        User initiates the launch of backend processes, during the ports 
        verification one of the ports is closed hence an exception is raised.
        """

        del_temp()
        mock_popen_instance = MagicMock()
        mock_popen.return_value = mock_popen_instance
        mock_popen_instance.pid = 1234
        mock_popen_instance.poll.return_value = None
        mock_conn1 = MagicMock()
        mock_conn1.laddr = MagicMock(port=7777)
        mock_net_connections.return_value = [mock_conn1]

        process_manager = ProcessManager(test_data_dir_path / "backend_processes_config.json")
        process_manager.create_backend_processes_data_file(temp_dir_path)
        process_manager.launch_processes()
        with pytest.raises(PortClosedError, match="Port .* is not open."):
            process_manager.verify_open_ports()

    @patch('Omni.process_manager.process_manager.sleep', return_value=None)
    @patch('Omni.process_manager.process_manager.subprocess.Popen')
    @patch('Omni.process_manager.process_manager.psutil.Process')
    def test_terminate_processes(self, mock_process_class, mock_popen, mock_sleep):
        """
        User requests the processes to terminate. Each of the processes from data file receive a SIGTERM request 
        and close correctly.
        """
        del_temp()
        mock_popen_instance = MagicMock()
        mock_popen.return_value = mock_popen_instance
        mock_popen_instance.pid = 1234
        mock_popen_instance.poll.return_value = None

        mock_process_instance = MagicMock()
        mock_process_class.side_effect = [mock_process_instance, 
                                          mock_process_instance, 
                                          psutil.NoSuchProcess(mock_popen_instance.pid),
                                          psutil.NoSuchProcess(mock_popen_instance.pid)]

        process_starter = ProcessManager(test_data_dir_path / "backend_processes_config.json")
        process_starter.create_backend_processes_data_file(temp_dir_path)
        process_starter.launch_processes()
        del process_starter
        process_stoper = ProcessManager(test_data_dir_path / "backend_processes_config.json")
        process_stoper.load_backend_processes_data_file(temp_dir_path)
        process_stoper.close_applications()
        expected_calls = [call(1234), call(1234)]
        mock_process_class.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(mock_process_instance.terminate.call_count, 2)
        saved_processes=load_processes_from_data_file(temp_dir_path / "my_backend_processes_status.json")
        self.assertEqual(saved_processes[0]["status"], "terminate requested")
        self.assertEqual(saved_processes[1]["status"], "terminate requested")
        process_stoper.verify_application_termination()
        saved_processes=load_processes_from_data_file(temp_dir_path / "my_backend_processes_status.json")
        self.assertEqual(saved_processes[0]["status"], "terminated")
        self.assertEqual(saved_processes[1]["status"], "terminated")

    @patch('Omni.cli.console_animations.time.sleep', return_value=None)
    @patch('Omni.process_manager.process_manager.subprocess.Popen')
    @patch('Omni.process_manager.process_manager.psutil.Process')
    def test_terminate_processes_not_terminated(self, mock_process_class, mock_popen, mock_sleep):
        """
        User requests the processes to terminate. Each of the processes from the data file receives a SIGTERM request.
        The first process terminates correctly, but the second process does not terminate properly, so a SIGKILL signal is sent.
        """
        del_temp()
        mock_popen_instance = MagicMock()
        mock_popen.return_value = mock_popen_instance
        mock_popen_instance.pid = 1234
        mock_popen_instance.poll.return_value = None

        mock_process_instance = MagicMock()
        mock_process_class.return_value = mock_process_instance
        process_terminate_call = mock_process_instance
        process_one_not_running = psutil.NoSuchProcess(mock_popen_instance.pid)
        process_two_running_first_call = mock_process_instance
        process_two_not_running_second_call = psutil.NoSuchProcess(mock_popen_instance.pid)
        mock_process_class.side_effect = [process_terminate_call, #executed in close_applications when the 1st process is terminated
                                          process_terminate_call, #executed in close_applications when the 2nd process is terminated
                                          process_one_not_running,#executed in verify_application_termination when the 1st process is fetched
                                          process_two_running_first_call,#executed in verify_application_termination when the 2st process is fetched
                                          process_two_not_running_second_call#executed in verify_application_termination when the 2st process is fetched for the second time
                                          ]

        process_starter = ProcessManager(test_data_dir_path / "backend_processes_config.json")
        process_starter.create_backend_processes_data_file(temp_dir_path)
        process_starter.launch_processes()
        del process_starter
        process_stoper = ProcessManager(test_data_dir_path / "backend_processes_config.json")
        process_stoper.load_backend_processes_data_file(temp_dir_path)
        process_stoper.close_applications()
        expected_calls = [call(1234), call(1234)]
        mock_process_class.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(mock_process_instance.terminate.call_count, 2)
        saved_processes=load_processes_from_data_file(temp_dir_path / "my_backend_processes_status.json")
        self.assertEqual(saved_processes[0]["status"], "terminate requested")
        self.assertEqual(saved_processes[1]["status"], "terminate requested")
        process_stoper.verify_application_termination()
        mock_process_instance.kill.assert_called_once()
        saved_processes=load_processes_from_data_file(temp_dir_path / "my_backend_processes_status.json")
        self.assertEqual(saved_processes[0]["status"], "terminated")
        self.assertEqual(saved_processes[1]["status"], "killed")

    @classmethod
    def teardown_class(cls):
        if os.path.exists(temp_dir_path):
            shutil.rmtree(temp_dir_path)
