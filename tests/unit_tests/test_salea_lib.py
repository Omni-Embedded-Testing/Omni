import unittest
import pytest
from Omni.robotlibraries.SaleaLogicAnalyzer import (LogicAnalyzer,
                                                    SaleaConfigurationError,
                                                    SaleaConnectionTimeout,
                                                    config_spi_channels,
                                                    config_spi_protocol,
                                                    config_i2c_channels,
                                                    config_uart_channel
                                                    )

from unittest.mock import patch, Mock, MagicMock, ANY
from saleae.automation import *


class TestSalea(unittest.TestCase):

    @patch('saleae.automation.Manager.connect', side_effect=Exception())
    def test_connect_raises_exception_if_connection_timeout(self, mock_mgr_connect):
        my_logic = LogicAnalyzer()
        with pytest.raises(SaleaConnectionTimeout, match=".*Unable to connect to Salea application. Verify connection on.*"):
            my_logic.connect_to_backend(timeout_seconds=0.1)

    @patch('saleae.automation.Manager.connect')
    def test_connect(self, mock_mgr_connect):
        my_logic = LogicAnalyzer()
        my_logic.connect_to_backend(timeout_seconds=1)
        mock_mgr_connect.assert_called_once_with(
            port=10430,
            address='127.0.0.1',
            connect_timeout_seconds=1
        )

    @patch('saleae.automation.LogicDeviceConfiguration')
    def test_set_device_configuration_configures_digital_channels_str(self, mock_device_cfg):
        my_logic = LogicAnalyzer()
        my_logic.set_device_configuration(
            digital_sample_rate="50000", enabled_digital_chanels=["1", "2"])
        mock_device_cfg.assert_called_once_with(
            enabled_digital_channels=[1, 2],
            digital_sample_rate=50000,
            enabled_analog_channels=None,
            analog_sample_rate=None,
            digital_threshold_volts=None,
            glitch_filters=[]
        )

    @patch('saleae.automation.LogicDeviceConfiguration')
    def test_set_device_configuration_configures_digital_channels_int(self, mock_device_cfg):
        my_logic = LogicAnalyzer()
        my_logic.set_device_configuration(
            digital_sample_rate=20000, enabled_digital_chanels=[1, 2], digital_threshold_volts=1.2)
        mock_device_cfg.assert_called_once_with(
            enabled_digital_channels=[1, 2],
            digital_sample_rate=20000,
            enabled_analog_channels=None,
            analog_sample_rate=None,
            digital_threshold_volts=1.2,
            glitch_filters=[]
        )

    @patch('saleae.automation.LogicDeviceConfiguration')
    def test_set_device_configuration_configures_analog_channels_str(self, mock_device_cfg):
        my_logic = LogicAnalyzer()
        my_logic.set_device_configuration(
            analog_sample_rate="30000", enabled_analog_channels=["1", "2"])
        mock_device_cfg.assert_called_once_with(
            enabled_digital_channels=None,
            digital_sample_rate=None,
            enabled_analog_channels=[1, 2],
            analog_sample_rate=30000,
            digital_threshold_volts=None,
            glitch_filters=[]
        )

    @patch('saleae.automation.LogicDeviceConfiguration')
    def test_set_device_configuration_configures_analog_channels_int(self, mock_device_cfg):
        my_logic = LogicAnalyzer()
        my_logic.set_device_configuration(
            analog_sample_rate=30000, enabled_analog_channels=[1, 2])
        mock_device_cfg.assert_called_once_with(
            enabled_analog_channels=[1, 2],
            analog_sample_rate=30000,
            enabled_digital_channels=None,
            digital_sample_rate=None,
            digital_threshold_volts=None,
            glitch_filters=[]
        )

    @patch('saleae.automation.CaptureConfiguration')
    def test_set_capture_mode_to_manual(self, mock_capture_cfg):
        my_logic = LogicAnalyzer()
        my_logic.set_manual_capture()
        mock_capture_cfg.assert_called_once_with(
            capture_mode=saleae.automation.ManualCaptureMode()
        )

    @patch('saleae.automation.CaptureConfiguration')
    def test_set_capture_mode_to_timmed(self, mock_capture_cfg):
        my_logic = LogicAnalyzer()
        my_logic.set_timed_capture(3)
        mock_capture_cfg.assert_called_once_with(
            capture_mode=saleae.automation.TimedCaptureMode(3)
        )

    @patch('saleae.automation.Manager.start_capture')
    @patch('saleae.automation.CaptureConfiguration', return_value=["mocked_capture"])
    def test_set_start_capture_raise_exp_if_device_not_configured(self, mock_start_capture, mock_capture):
        my_logic = LogicAnalyzer()
        my_logic.set_timed_capture(3)
        with pytest.raises(SaleaConfigurationError, match=r".*Device Configuration Error.*"):
            my_logic.start_capture()

    @patch('saleae.automation.Manager.start_capture')
    @patch('saleae.automation.LogicDeviceConfiguration', return_value=["mocked_configuration"])
    def test_set_start_capture_raise_exp_if_capture_not_configured(self, mock_dev_cfg, mock_cfg):
        my_logic = LogicAnalyzer()
        my_logic.set_device_configuration(
            analog_sample_rate=30000, enabled_analog_channels=[1, 2])
        with pytest.raises(SaleaConfigurationError, match=r".*Capture Configuration Error.*"):
            my_logic.start_capture()

    @patch("Omni.robotlibraries.SaleaLogicAnalyzer.SaleaLogicAnalyzer.automation.Manager")
    def test_set_start_capture(self, mock_connect):
        my_logic = LogicAnalyzer()
        mock_manager_instance = mock_connect.connect.return_value
        mock_start_capture = MagicMock()
        mock_manager_instance.start_capture = mock_start_capture
        my_logic.connect_to_backend(timeout_seconds=1)
        my_logic.set_device_configuration(
            analog_sample_rate=30000, enabled_analog_channels=[1, 2])
        my_logic.set_timed_capture(3)
        my_logic.start_capture()
        print(dir(my_logic))
        mock_manager_instance.start_capture.assert_called_once_with(
            device_id=None,
            device_configuration=my_logic._LogicAnalyzer__device_configuration,
            capture_configuration=my_logic._LogicAnalyzer__capture_configuration
        )

    def test_wait_capture_end_calls_api(self):
        my_logic = LogicAnalyzer()
        mock_wait = Mock()
        my_logic.capture = mock_wait
        my_logic.wait_capture_end()
        mock_wait.wait.assert_called_once()

    def test_disconnect_from_backend_calls_close(self):
        my_logic = LogicAnalyzer()
        mock_disconnect = Mock()
        my_logic.manager = mock_disconnect
        my_logic.disconnect_from_backend()
        mock_disconnect.close.assert_called_once()

    def test_add_spi_analyser_adds_analyser_with_protocol_and_cfg(self):
        expected_dict = {'MISO': 1,
                         'MOSI': 2,
                         'Enable': 3,
                         'Clock': 4,
                         'Bits per Transfer': '8 Bits per Transfer (Standard)',
                         'Significant Bit': 'Most Significant Bit First (Standard)',
                         'Clock State': 'Clock is Low when inactive (CPOL = 0)',
                         'Clock Phase': 'Data is Valid on Clock Leading Edge (CPHA = 0)',
                         'Enable Line': 'Enable line is Active Low (Standard)'}
        my_logic = LogicAnalyzer()
        mock_spi_analyzer = Mock()
        my_logic.capture = mock_spi_analyzer
        spi_channels_cfg = config_spi_channels(
            MISO=1, MOSI=2, Enable=3, Clock=4)
        spi_protocol_cfg = config_spi_protocol(
            DATA_FRAME_SIZE=8, FIRST_BIT='MSB', CPHA=0, CPOL=0, EnableLineActiveOn=0)
        my_logic.add_spi_analyser(
            spi_channels_cfg, spi_protocol_cfg, "TEST_SPI")
        mock_spi_analyzer.add_analyzer.assert_called_with(
            'SPI', label='TEST_SPI', settings=expected_dict)

    def test_add_spi_analyser_does_not_add_two_analysers_with_same_label(self):
        my_logic = LogicAnalyzer()
        mock_spi_analyzer = Mock()
        my_logic.capture = mock_spi_analyzer
        spi_channels_cfg = config_spi_channels(
            MISO=1, MOSI=2, Enable=3, Clock=4)
        spi_protocol_cfg = config_spi_protocol(
            DATA_FRAME_SIZE=8, FIRST_BIT='MSB', CPHA=0, CPOL=0, EnableLineActiveOn=0)
        my_logic.add_spi_analyser(
            spi_channels_cfg, spi_protocol_cfg, "TEST_SPI")
        with pytest.raises(ValueError, match=r".*Analysers must have unique labels.*"):
            my_logic.add_spi_analyser(
                spi_channels_cfg, spi_protocol_cfg, "TEST_SPI")

    def test_invalid_EnableLineActive_raises_exception(self):
        my_logic = LogicAnalyzer()
        mock_spi_analyzer = Mock()
        my_logic.capture = mock_spi_analyzer
        spi_channels_cfg = config_spi_channels(
            MISO=1, MOSI=2, Enable=3, Clock=4)
        with pytest.raises(SaleaConfigurationError, match=r"Invalid value for 'EnableLineActive'. Provided value: '2'. Valid values are: 0, 1."):
            spi_protocol_cfg = config_spi_protocol(
                DATA_FRAME_SIZE=8, FIRST_BIT='MSB', CPHA=0, CPOL=0, EnableLineActiveOn=2)

    def test_invalid_DATA_FRAME_SIZE_raises_exception(self):
        my_logic = LogicAnalyzer()
        mock_spi_analyzer = Mock()
        my_logic.capture = mock_spi_analyzer
        spi_channels_cfg = config_spi_channels(
            MISO=1, MOSI=2, Enable=3, Clock=4)
        with pytest.raises(SaleaConfigurationError, match=r"Invalid value for 'DATA_FRAME_SIZE'. Provided value: '55'. Valid values are: 8, 16."):
            spi_protocol_cfg = config_spi_protocol(
                DATA_FRAME_SIZE=55, FIRST_BIT='MSB', CPHA=0, CPOL=0, EnableLineActiveOn=0)

    def test_invalid_FIRST_BIT_raises_exception(self):
        my_logic = LogicAnalyzer()
        mock_spi_analyzer = Mock()
        my_logic.capture = mock_spi_analyzer
        spi_channels_cfg = config_spi_channels(
            MISO=1, MOSI=2, Enable=3, Clock=4)
        with pytest.raises(SaleaConfigurationError, match=r"Invalid value for 'FIRST_BIT'. Provided value: 'ABC'. Valid values are: MSB, LSB."):
            spi_protocol_cfg = config_spi_protocol(
                DATA_FRAME_SIZE=8, FIRST_BIT='ABC', CPHA=0, CPOL=0, EnableLineActiveOn=0)

    def test_invalid_CPHA_raises_exception(self):
        my_logic = LogicAnalyzer()
        mock_spi_analyzer = Mock()
        my_logic.capture = mock_spi_analyzer
        spi_channels_cfg = config_spi_channels(
            MISO=1, MOSI=2, Enable=3, Clock=4)
        with pytest.raises(SaleaConfigurationError, match=r"Invalid value for 'CPHA'. Provided value: '22'. Valid values are: 0, 1."):
            spi_protocol_cfg = config_spi_protocol(
                DATA_FRAME_SIZE=8, FIRST_BIT='LSB', CPHA=22, CPOL=0, EnableLineActiveOn=0)

    def test_invalid_CPOL_raises_exception(self):
        my_logic = LogicAnalyzer()
        mock_spi_analyzer = Mock()
        my_logic.capture = mock_spi_analyzer
        spi_channels_cfg = config_spi_channels(
            MISO=1, MOSI=2, Enable=3, Clock=4)
        with pytest.raises(SaleaConfigurationError, match=r"Invalid value for 'CPOL'. Provided value: '33'. Valid values are: 0, 1."):
            spi_protocol_cfg = config_spi_protocol(
                DATA_FRAME_SIZE=8, FIRST_BIT='LSB', CPHA=0, CPOL=33, EnableLineActiveOn=0)

    @patch("Omni.robotlibraries.SaleaLogicAnalyzer.SaleaLogicAnalyzer.automation.capture.DataTableExportConfiguration",
           return_value="mocked_ExportConfiguration")
    def test_export_to_csv_calls_api_with_spi_analyser(self, mock_export_cfg):
        my_logic = LogicAnalyzer()
        mock_spi_analyzer = Mock()
        my_logic.capture = mock_spi_analyzer
        spi_channels_cfg = config_spi_channels(
            MISO=1, MOSI=2, Enable=3, Clock=4)
        spi_protocol_cfg = config_spi_protocol(
            DATA_FRAME_SIZE=8, FIRST_BIT='MSB', CPHA=0, CPOL=0, EnableLineActiveOn=0)
        my_logic.add_spi_analyser(
            spi_channels_cfg, spi_protocol_cfg, "TEST_SPI")
        my_logic.export_to_csv("/folder/to/csv/capture",
                               "capture_name.txt", "TEST_SPI", radix="HEXADECIMAL")
        mock_export_cfg.assert_called_with(
            mock_spi_analyzer.add_analyzer(), ANY)

    def test_add_i2c_analyser_adds_analyser_with_protocol_and_cfg(self):
        expected_dict = {'SDA': 1,
                         'SCL': 0,
                         }
        my_logic = LogicAnalyzer()
        mock_i2c_analyzer = Mock()
        my_logic.capture = mock_i2c_analyzer
        i2c_channels_cfg = config_i2c_channels(
            SDA=1, SCL=0)
        my_logic.add_i2c_analyser(
            i2c_channels_cfg, label="TEST_I2C")
        mock_i2c_analyzer.add_analyzer.assert_called_with(
            'I2C', label='TEST_I2C', settings=expected_dict)

    @patch("Omni.robotlibraries.SaleaLogicAnalyzer.SaleaLogicAnalyzer.automation.capture.DataTableExportConfiguration",
           return_value="mocked_ExportConfiguration")
    def test_export_to_csv_calls_api_with_spi_analyser(self, mock_export_cfg):
        my_logic = LogicAnalyzer()
        mock_i2c_analyzer = Mock()
        my_logic.capture = mock_i2c_analyzer
        i2c_channels_cfg = config_i2c_channels(
            SDA=1, SCL=0)
        my_logic.add_i2c_analyser(
            i2c_channels_cfg, label="TEST_I2C")
        my_logic.export_to_csv("/folder/to/csv/capture",
                               "capture_name.txt", "TEST_I2C", radix="HEXADECIMAL")
        mock_export_cfg.assert_called_with(
            mock_i2c_analyzer.add_analyzer(), ANY)

    def test_add_analyser_raises_exception_if_analyser_does_not_exists(self):
        my_logic = LogicAnalyzer()
        with pytest.raises(ValueError, match=r".*Analyser NON_EXISTENT_ANALYSER not added.*"):
            my_logic.export_to_csv("/folder/to/csv/capture",
                                   "capture_name.txt", "NON_EXISTENT_ANALYSER")

    def test_add_i2c_analyser_does_not_add_two_analysers_with_same_label(self):
        my_logic = LogicAnalyzer()
        mock_i2c_analyzer = Mock()
        my_logic.capture = mock_i2c_analyzer
        i2c_channels_cfg = config_i2c_channels(
            SDA=1, SCL=0)
        my_logic.add_i2c_analyser(
            i2c_channels_cfg, label="TEST_I2C")
        with pytest.raises(ValueError, match=r".*Analysers must have unique labels.*"):
            my_logic.add_i2c_analyser(
                i2c_channels_cfg, label="TEST_I2C")

    @patch("Omni.robotlibraries.SaleaLogicAnalyzer.SaleaLogicAnalyzer.automation.capture.DataTableExportConfiguration",
           return_value="mocked_ExportConfiguration")
    def test_export_to_csv_calls_api_hex(self, mock_export_cfg):
        my_logic = LogicAnalyzer()
        mock_spi_analyzer = Mock()
        my_logic.capture = mock_spi_analyzer
        spi_channels_cfg = config_spi_channels(
            MISO=1, MOSI=2, Enable=3, Clock=4)
        spi_protocol_cfg = config_spi_protocol(
            DATA_FRAME_SIZE=8, FIRST_BIT='MSB', CPHA=0, CPOL=0, EnableLineActiveOn=0)
        my_logic.add_spi_analyser(
            spi_channels_cfg, spi_protocol_cfg, "TEST_SPI")
        my_logic.export_to_csv("/folder/to/csv/capture",
                               "capture_name.txt", "TEST_SPI", radix="HEXADECIMAL")
        mock_export_cfg.assert_called_with(
            ANY, saleae.automation.capture.RadixType.HEXADECIMAL)
        mock_spi_analyzer.export_data_table.assert_called_with(
            filepath='/folder/to/csv/capture/capture_name.txt', analyzers=ANY)

    @patch("Omni.robotlibraries.SaleaLogicAnalyzer.SaleaLogicAnalyzer.automation.capture.DataTableExportConfiguration",
           return_value="mocked_ExportConfiguration")
    def test_export_to_csv_calls_api_bin(self, mock_export_cfg):
        my_logic = LogicAnalyzer()
        mock_spi_analyzer = Mock()
        my_logic.capture = mock_spi_analyzer
        spi_channels_cfg = config_spi_channels(
            MISO=1, MOSI=2, Enable=3, Clock=4)
        spi_protocol_cfg = config_spi_protocol(
            DATA_FRAME_SIZE=8, FIRST_BIT='MSB', CPHA=0, CPOL=0, EnableLineActiveOn=0)
        my_logic.add_spi_analyser(
            spi_channels_cfg, spi_protocol_cfg, "TEST_SPI")
        my_logic.export_to_csv("/folder/to/csv/capture",
                               "capture_name.txt", "TEST_SPI", radix="BINARY")
        mock_export_cfg.assert_called_with(
            ANY, saleae.automation.capture.RadixType.BINARY)
        mock_spi_analyzer.export_data_table.assert_called_with(
            filepath='/folder/to/csv/capture/capture_name.txt', analyzers=ANY)

    @patch("Omni.robotlibraries.SaleaLogicAnalyzer.SaleaLogicAnalyzer.automation.capture.DataTableExportConfiguration",
           return_value="mocked_ExportConfiguration")
    def test_export_to_csv_calls_api_dec(self, mock_export_cfg):
        my_logic = LogicAnalyzer()
        mock_spi_analyzer = Mock()
        my_logic.capture = mock_spi_analyzer
        spi_channels_cfg = config_spi_channels(
            MISO=1, MOSI=2, Enable=3, Clock=4)
        spi_protocol_cfg = config_spi_protocol(
            DATA_FRAME_SIZE=8, FIRST_BIT='MSB', CPHA=0, CPOL=0, EnableLineActiveOn=0)
        my_logic.add_spi_analyser(
            spi_channels_cfg, spi_protocol_cfg, "TEST_SPI")
        my_logic.export_to_csv("/folder/to/csv/capture",
                               "capture_name.txt", "TEST_SPI", radix="DECIMAL")
        mock_export_cfg.assert_called_with(
            ANY, saleae.automation.capture.RadixType.DECIMAL)
        mock_spi_analyzer.export_data_table.assert_called_with(
            filepath='/folder/to/csv/capture/capture_name.txt', analyzers=ANY)

    base_uart_dict = {"Input Channel": 2,
                      "Bit Rate (Bits/s)": 115200,
                      "Bits per Frame": "8 Bits per Transfer (Standard)",
                      "Stop Bits": "1 Stop Bit (Standard)",
                      "Parity Bit": "No Parity Bit (Standard)",
                      "Significant Bit": "Least Significant Bit Sent First (Standard)",
                      "Signal inversion": "Non Inverted (Standard)",
                      "Mode": "Normal"}

    def test_config_uart_builds_base_uart_dict(self):
        uart_channel_cfg = config_uart_channel(
            Channel=2, BitRate=115200, BitsPerFrame=8, StopBits=1, Parity="None",
            Indianess="LSB", Inversion=False, AddressMode="Normal")
        assert self.base_uart_dict == uart_channel_cfg

    def test_config_uart_builds_uart_cfg_dict_alternate_values(self):
        expected_dict = {"Input Channel": 3,
                         "Bit Rate (Bits/s)": 9600,
                         "Bits per Frame": "9 Bits per Transfer",
                         "Stop Bits": "1.5 Stop Bits",
                         "Parity Bit": "Even Parity Bit",
                         "Significant Bit": "Most Significant Bit Sent First",
                         "Signal inversion": "Inverted",
                         "Mode": "MP - Address indicated by MSB=0"}
        uart_channel_cfg = config_uart_channel(
            Channel=3, BitRate=9600, BitsPerFrame=9, StopBits=1.5, Parity="Even",
            Indianess="MSB", Inversion=True, AddressMode="MP")
        assert expected_dict == uart_channel_cfg

    def test_config_uart_builds_uart_cfg_dict_alternate_parity(self):
        expected_dict = self.base_uart_dict.copy()
        expected_dict["Parity Bit"] = "Odd Parity Bit"
        uart_channel_cfg = config_uart_channel(
            Channel=2, BitRate=115200, BitsPerFrame=8, StopBits=1, Parity="Odd",
            Indianess="LSB", Inversion=False, AddressMode="Normal")
        assert expected_dict == uart_channel_cfg

    def test_config_uart_builds_uart_cfg_dict_alternate_mode(self):
        expected_dict = self.base_uart_dict.copy()
        expected_dict["Mode"] = "MDB - Address indicated by MSB=1 (TX only)"
        uart_channel_cfg = config_uart_channel(
            Channel=2, BitRate=115200, BitsPerFrame=8, StopBits=1, Parity="None",
            Indianess="LSB", Inversion=False, AddressMode="MDB")
        assert expected_dict == uart_channel_cfg

    def test_config_uart_builds_uart_cfg_dict_invalid_bitrate_raises_exception(self):
        with pytest.raises(ValueError, match=r"Invalid value for BitRate. Value must be positive."):
            config_uart_channel(
                Channel=2, BitRate=0, BitsPerFrame=8, StopBits=1, Parity="Chocolate",
                Indianess="MSB", Inversion=False, AddressMode="Normal")

    def test_config_uart_builds_uart_cfg_dict_invalid_bits_per_fame_zero_raises_exception(self):
        with pytest.raises(ValueError, match=r"Invalid value for Bits Per Frame. Value must be positive and less than 65."):
            config_uart_channel(
                Channel=2, BitRate=9600, BitsPerFrame=0, StopBits=1, Parity="Even",
                Indianess="MSB", Inversion=False, AddressMode="Normal")

    def test_config_uart_builds_uart_cfg_dict_invalid_bits_per_fame_zero_raises_exception(self):
        with pytest.raises(ValueError, match=r"Invalid value for Bits Per Frame. Value must be positive and less than 65."):
            config_uart_channel(
                Channel=2, BitRate=9600, BitsPerFrame=65, StopBits=1, Parity="Even",
                Indianess="MSB", Inversion=False, AddressMode="Normal")

    def test_config_uart_builds_uart_cfg_dict_invalid_parity_raises_exception(self):
        with pytest.raises(ValueError, match=r"Invalid value for Parity. Valied values are: None,Odd and Even."):
            config_uart_channel(
                Channel=2, BitRate=115200, BitsPerFrame=8, StopBits=1, Parity="Chocolate",
                Indianess="MSB", Inversion=False, AddressMode="Normal")

    def test_config_uart_builds_uart_cfg_dict_invalid_indianess_raises_exception(self):
        with pytest.raises(ValueError, match=r"Invalid value for Indianess. Valied values are: MSB or LSB."):
            config_uart_channel(
                Channel=2, BitRate=115200, BitsPerFrame=8, StopBits=1, Parity="Odd",
                Indianess="Cupcake", Inversion=False, AddressMode="Normal")

    def test_config_uart_builds_uart_cfg_dict_invalid_address_mode_raises_exception(self):
        with pytest.raises(ValueError, match=r"Invalid value for AddressMode. Valied values are: Normal or MP or MDB."):
            config_uart_channel(
                Channel=2, BitRate=115200, BitsPerFrame=8, StopBits=1, Parity="Odd",
                Indianess="MSB", Inversion=False, AddressMode="Potato")

    def test_add_uart_analyser_adds_analyser(self):
        uart_channel_cfg = config_uart_channel(
            Channel=2, BitRate=115200, BitsPerFrame=8, StopBits=1, Parity="None",
            Indianess="LSB", Inversion=False, AddressMode="Normal")
        my_logic = LogicAnalyzer()
        mock_uart_analyzer = Mock()
        my_logic.capture = mock_uart_analyzer
        my_logic.add_uart_analyser(
            uart_channel_cfg, "TEST_UART")
        mock_uart_analyzer.add_analyzer.assert_called_with(
            'Async Serial', label='TEST_UART', settings=self.base_uart_dict)
        return

    def test_add_uart_analyser_adds_analyser2(self):
        expected_dict = {"Input Channel": 3,
                         "Bit Rate (Bits/s)": 9600,
                         "Bits per Frame": "9 Bits per Transfer",
                         "Stop Bits": "1.5 Stop Bits",
                         "Parity Bit": "Even Parity Bit",
                         "Significant Bit": "Most Significant Bit Sent First",
                         "Signal inversion": "Inverted",
                         "Mode": "MP - Address indicated by MSB=0"}
        uart_channel_cfg = config_uart_channel(
            Channel=3, BitRate=9600, BitsPerFrame=9, StopBits=1.5, Parity="Even",
            Indianess="MSB", Inversion=True, AddressMode="MP")
        my_logic = LogicAnalyzer()
        mock_uart_analyzer = Mock()
        my_logic.capture = mock_uart_analyzer
        my_logic.add_uart_analyser(
            uart_channel_cfg, "TEST_UART")
        mock_uart_analyzer.add_analyzer.assert_called_with(
            'Async Serial', label='TEST_UART', settings=expected_dict)

    def test_add_uart_analyser_doesnt_add_same_label_twice(self):
        uart_channel_cfg = config_uart_channel(
            Channel=3, BitRate=9600, BitsPerFrame=9, StopBits=1.5, Parity="Even",
            Indianess="MSB", Inversion=True, AddressMode="MP")
        my_logic = LogicAnalyzer()
        mock_uart_analyzer = Mock()
        my_logic.capture = mock_uart_analyzer
        my_logic.add_uart_analyser(
            uart_channel_cfg, "TEST_UART")
        with pytest.raises(ValueError, match=r".*Analysers must have unique labels.*"):
            my_logic.add_uart_analyser(
                uart_channel_cfg, "TEST_UART")

    @patch("Omni.robotlibraries.SaleaLogicAnalyzer.SaleaLogicAnalyzer.automation.capture.DataTableExportConfiguration",
           return_value="mocked_ExportConfiguration")
    def test_export_to_csv_calls_api_ascii(self, mock_export_cfg):
        my_logic = LogicAnalyzer()
        mock_spi_analyzer = Mock()
        my_logic.capture = mock_spi_analyzer
        spi_channels_cfg = config_spi_channels(
            MISO=1, MOSI=2, Enable=3, Clock=4)
        spi_protocol_cfg = config_spi_protocol(
            DATA_FRAME_SIZE=8, FIRST_BIT='MSB', CPHA=0, CPOL=0, EnableLineActiveOn=0)
        my_logic.add_spi_analyser(
            spi_channels_cfg, spi_protocol_cfg, "TEST_SPI")
        my_logic.export_to_csv("/folder/to/csv/capture",
                               "capture_name.txt", "TEST_SPI", radix="ASCII")
        mock_export_cfg.assert_called_with(
            ANY, saleae.automation.capture.RadixType.ASCII)
        mock_spi_analyzer.export_data_table.assert_called_with(
            filepath='/folder/to/csv/capture/capture_name.txt', analyzers=ANY)

    @patch("Omni.robotlibraries.SaleaLogicAnalyzer.SaleaLogicAnalyzer.automation.capture.DataTableExportConfiguration",
           return_value="mocked_ExportConfiguration")
    def test_export_to_csv_calls_api_invalid(self, mock_export_cfg):
        my_logic = LogicAnalyzer()
        mock_spi_analyzer = Mock()
        my_logic.capture = mock_spi_analyzer
        spi_channels_cfg = config_spi_channels(
            MISO=1, MOSI=2, Enable=3, Clock=4)
        spi_protocol_cfg = config_spi_protocol(
            DATA_FRAME_SIZE=8, FIRST_BIT='MSB', CPHA=0, CPOL=0, EnableLineActiveOn=0)
        my_logic.add_spi_analyser(
            spi_channels_cfg, spi_protocol_cfg, label="TEST_SPI")
        with pytest.raises(ValueError, match=r".*Invalid value for radix.*"):
            my_logic.export_to_csv("/folder/to/csv/capture",
                                   "capture_name.txt", "TEST_SPI", "INVALID")

    def test_save_raw(self):
        my_logic = LogicAnalyzer()
        mock_capture = Mock()
        my_logic.capture = mock_capture
        my_logic.save_raw("/path/to/folder", "filename")
        mock_capture.save_capture.assert_called_once_with(
            filepath='/path/to/folder/filename')

    @patch('saleae.automation.LogicDeviceConfiguration')
    def test_set_device_configuration_configures_glitch_filters(self, mock_device_cfg):
        my_logic = LogicAnalyzer()
        my_logic.add_glitch_filter(1, 1e-05)
        my_logic.set_device_configuration(
            digital_sample_rate=20000, enabled_digital_chanels=[1, 2], digital_threshold_volts=1.2)
        mock_device_cfg.assert_called_once_with(
            enabled_digital_channels=[1, 2],
            digital_sample_rate=20000,
            enabled_analog_channels=None,
            analog_sample_rate=None,
            digital_threshold_volts=1.2,
            glitch_filters=[GlitchFilterEntry(
                channel_index=1, pulse_width_seconds=1e-05)]
        )

    @patch('saleae.automation.LogicDeviceConfiguration')
    def test_set_device_configuration_configures_glitch_filters_with_str(self, mock_device_cfg):
        my_logic = LogicAnalyzer()
        my_logic.add_glitch_filter("1", "1e-05")
        my_logic.set_device_configuration(
            digital_sample_rate=20000, enabled_digital_chanels=[1, 2], digital_threshold_volts=1.2)
        mock_device_cfg.assert_called_once_with(
            enabled_digital_channels=[1, 2],
            digital_sample_rate=20000,
            enabled_analog_channels=None,
            analog_sample_rate=None,
            digital_threshold_volts=1.2,
            glitch_filters=[GlitchFilterEntry(
                channel_index=1, pulse_width_seconds=1e-05)]
        )
