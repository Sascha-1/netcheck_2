"""Tests for netcheck.py.

Tests CLI argument parsing, main workflow, and exit code handling.
"""

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from config import ExitCode
from models import InterfaceInfo
from enums import InterfaceType
from netcheck import parse_arguments, main


class TestParseArguments:
    """Tests for parse_arguments function."""

    def test_no_arguments(self, monkeypatch) -> None:
        """Test default behavior with no arguments."""
        monkeypatch.setattr(sys, "argv", ["netcheck"])

        args = parse_arguments()

        assert args.verbose is False
        assert args.log_file is None
        assert args.export is None
        assert args.output is None

    def test_verbose_flag(self, monkeypatch) -> None:
        """Test --verbose flag."""
        monkeypatch.setattr(sys, "argv", ["netcheck", "--verbose"])

        args = parse_arguments()

        assert args.verbose is True

    def test_verbose_short_flag(self, monkeypatch) -> None:
        """Test -v flag."""
        monkeypatch.setattr(sys, "argv", ["netcheck", "-v"])

        args = parse_arguments()

        assert args.verbose is True

    def test_log_file(self, monkeypatch) -> None:
        """Test --log-file argument."""
        monkeypatch.setattr(sys, "argv", ["netcheck", "--log-file", "debug.log"])

        args = parse_arguments()

        assert args.log_file == Path("debug.log")

    def test_export_json(self, monkeypatch) -> None:
        """Test --export json."""
        monkeypatch.setattr(sys, "argv", ["netcheck", "--export", "json"])

        args = parse_arguments()

        assert args.export == "json"

    def test_output_file(self, monkeypatch) -> None:
        """Test --output argument."""
        monkeypatch.setattr(sys, "argv", ["netcheck", "--export", "json", "--output", "report.json"])

        args = parse_arguments()

        assert args.export == "json"
        assert args.output == Path("report.json")

    def test_output_without_export_exits(self, monkeypatch) -> None:
        """Test --output without --export exits with code 4."""
        monkeypatch.setattr(sys, "argv", ["netcheck", "--output", "report.json"])

        with pytest.raises(SystemExit) as exc_info:
            parse_arguments()

        assert exc_info.value.code == ExitCode.INVALID_ARGUMENTS

    def test_combined_flags(self, monkeypatch) -> None:
        """Test combining multiple flags."""
        monkeypatch.setattr(
            sys,
            "argv",
            ["netcheck", "-v", "--log-file", "debug.log", "--export", "json", "--output", "out.json"]
        )

        args = parse_arguments()

        assert args.verbose is True
        assert args.log_file == Path("debug.log")
        assert args.export == "json"
        assert args.output == Path("out.json")

    def test_help_flag_exits(self, monkeypatch) -> None:
        """Test --help flag exits (argparse behavior)."""
        monkeypatch.setattr(sys, "argv", ["netcheck", "--help"])

        with pytest.raises(SystemExit) as exc_info:
            parse_arguments()

        assert exc_info.value.code == 0


class TestMain:
    """Tests for main function."""

    @patch("netcheck.format_output")
    @patch("netcheck.collect_network_data")
    @patch("netcheck.check_dependencies")
    @patch("netcheck.setup_logging")
    @patch("netcheck.parse_arguments")
    def test_main_basic_success(
        self,
        mock_parse,
        mock_setup_logging,
        mock_check_deps,
        mock_collect,
        mock_format,
    ):
        """Test basic successful execution."""
        # Setup mocks
        mock_args = Mock()
        mock_args.verbose = False
        mock_args.log_file = None
        mock_args.export = None
        mock_args.output = None
        mock_parse.return_value = mock_args

        mock_check_deps.return_value = True

        test_interface = InterfaceInfo.create_empty("eth0")
        test_interface.interface_type = InterfaceType.ETHERNET
        mock_collect.return_value = [test_interface]

        # Run main
        with pytest.raises(SystemExit) as exc_info:
            main()

        # Verify exit code
        assert exc_info.value.code == ExitCode.SUCCESS

        # Verify calls
        mock_setup_logging.assert_called_once_with(
            verbose=False,
            log_file=None,
            use_colors=True,
        )
        mock_check_deps.assert_called_once()
        mock_collect.assert_called_once()
        mock_format.assert_called_once_with([test_interface])

    @patch("netcheck.check_dependencies")
    @patch("netcheck.setup_logging")
    @patch("netcheck.parse_arguments")
    def test_main_missing_dependencies(
        self,
        mock_parse,
        mock_setup_logging,
        mock_check_deps,
    ):
        """Test exit when dependencies missing."""
        mock_args = Mock()
        mock_args.verbose = False
        mock_args.log_file = None
        mock_parse.return_value = mock_args

        mock_check_deps.return_value = False  # Dependencies missing

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == ExitCode.MISSING_DEPENDENCIES

    @patch("netcheck.collect_network_data")
    @patch("netcheck.check_dependencies")
    @patch("netcheck.setup_logging")
    @patch("netcheck.parse_arguments")
    def test_main_no_interfaces_found(
        self,
        mock_parse,
        mock_setup_logging,
        mock_check_deps,
        mock_collect,
    ):
        """Test exit when no interfaces found."""
        mock_args = Mock()
        mock_args.verbose = False
        mock_args.log_file = None
        mock_parse.return_value = mock_args

        mock_check_deps.return_value = True
        mock_collect.return_value = []  # No interfaces

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == ExitCode.GENERAL_ERROR

    @patch("netcheck.export_to_json")
    @patch("netcheck.collect_network_data")
    @patch("netcheck.check_dependencies")
    @patch("netcheck.setup_logging")
    @patch("netcheck.parse_arguments")
    def test_main_export_json_stdout(
        self,
        mock_parse,
        mock_setup_logging,
        mock_check_deps,
        mock_collect,
        mock_export,
        capsys,
    ):
        """Test JSON export to stdout."""
        mock_args = Mock()
        mock_args.verbose = False
        mock_args.log_file = None
        mock_args.export = "json"
        mock_args.output = None
        mock_parse.return_value = mock_args

        mock_check_deps.return_value = True
        test_interface = InterfaceInfo.create_empty("eth0")
        mock_collect.return_value = [test_interface]
        mock_export.return_value = '{"interfaces": []}'

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == ExitCode.SUCCESS
        mock_export.assert_called_once_with([test_interface])

        # Verify JSON was printed to stdout
        captured = capsys.readouterr()
        assert '{"interfaces": []}' in captured.out

    @patch("netcheck.export_to_json")
    @patch("netcheck.collect_network_data")
    @patch("netcheck.check_dependencies")
    @patch("netcheck.setup_logging")
    @patch("netcheck.parse_arguments")
    def test_main_export_json_file(
        self,
        mock_parse,
        mock_setup_logging,
        mock_check_deps,
        mock_collect,
        mock_export,
        tmp_path,
    ):
        """Test JSON export to file."""
        output_file = tmp_path / "report.json"

        mock_args = Mock()
        mock_args.verbose = False
        mock_args.log_file = None
        mock_args.export = "json"
        mock_args.output = output_file
        mock_parse.return_value = mock_args

        mock_check_deps.return_value = True
        test_interface = InterfaceInfo.create_empty("eth0")
        mock_collect.return_value = [test_interface]
        mock_export.return_value = '{"test": "data"}'

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == ExitCode.SUCCESS

        # Verify file was written
        assert output_file.exists()
        assert output_file.read_text() == '{"test": "data"}'

    @patch("netcheck.format_output")
    @patch("netcheck.collect_network_data")
    @patch("netcheck.check_dependencies")
    @patch("netcheck.setup_logging")
    @patch("netcheck.parse_arguments")
    def test_main_verbose_with_log_file(
        self,
        mock_parse,
        mock_setup_logging,
        mock_check_deps,
        mock_collect,
        mock_format,
        tmp_path,
    ):
        """Test verbose mode with log file includes table in log."""
        log_file = tmp_path / "debug.log"

        mock_args = Mock()
        mock_args.verbose = True
        mock_args.log_file = log_file
        mock_args.export = None
        mock_args.output = None
        mock_parse.return_value = mock_args

        mock_check_deps.return_value = True
        test_interface = InterfaceInfo.create_empty("eth0")
        mock_collect.return_value = [test_interface]

        # Create the log file
        log_file.touch()

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == ExitCode.SUCCESS

        # format_output should be called twice:
        # 1. For stdout
        # 2. For log file (because verbose + log_file)
        assert mock_format.call_count == 2

    @patch("netcheck.collect_network_data")
    @patch("netcheck.check_dependencies")
    @patch("netcheck.setup_logging")
    @patch("netcheck.parse_arguments")
    def test_main_keyboard_interrupt(
        self,
        mock_parse,
        mock_setup_logging,
        mock_check_deps,
        mock_collect,
    ):
        """Test KeyboardInterrupt handling."""
        mock_args = Mock()
        mock_args.verbose = False
        mock_args.log_file = None
        mock_parse.return_value = mock_args

        mock_check_deps.return_value = True
        mock_collect.side_effect = KeyboardInterrupt()

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == ExitCode.GENERAL_ERROR

    @patch("netcheck.collect_network_data")
    @patch("netcheck.check_dependencies")
    @patch("netcheck.setup_logging")
    @patch("netcheck.parse_arguments")
    @pytest.mark.parametrize("exception_type", [
        OSError,
        IOError,
        ValueError,
        RuntimeError,
    ])
    def test_main_exception_handling(
        self,
        mock_parse,
        mock_setup_logging,
        mock_check_deps,
        mock_collect,
        exception_type,
    ):
        """Test exception handling for various error types."""
        mock_args = Mock()
        mock_args.verbose = False
        mock_args.log_file = None
        mock_parse.return_value = mock_args

        mock_check_deps.return_value = True
        mock_collect.side_effect = exception_type("Test error")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == ExitCode.GENERAL_ERROR

    @patch("netcheck.traceback")
    @patch("netcheck.collect_network_data")
    @patch("netcheck.check_dependencies")
    @patch("netcheck.setup_logging")
    @patch("netcheck.parse_arguments")
    def test_main_verbose_exception_prints_traceback(
        self,
        mock_parse,
        mock_setup_logging,
        mock_check_deps,
        mock_collect,
        mock_traceback,
    ):
        """Test verbose mode prints traceback on exception."""
        mock_args = Mock()
        mock_args.verbose = True
        mock_args.log_file = None
        mock_parse.return_value = mock_args

        mock_check_deps.return_value = True
        mock_collect.side_effect = RuntimeError("Test error")

        with pytest.raises(SystemExit):
            main()

        # Verify traceback was printed
        mock_traceback.print_exc.assert_called_once()

    @patch("netcheck.format_output")
    @patch("netcheck.collect_network_data")
    @patch("netcheck.check_dependencies")
    @patch("netcheck.setup_logging")
    @patch("netcheck.parse_arguments")
    def test_main_multiple_interfaces(
        self,
        mock_parse,
        mock_setup_logging,
        mock_check_deps,
        mock_collect,
        mock_format,
    ):
        """Test with multiple interfaces."""
        mock_args = Mock()
        mock_args.verbose = False
        mock_args.log_file = None
        mock_args.export = None
        mock_parse.return_value = mock_args

        mock_check_deps.return_value = True

        # Create multiple interfaces
        interfaces = [
            InterfaceInfo.create_empty("lo"),
            InterfaceInfo.create_empty("eth0"),
            InterfaceInfo.create_empty("wlan0"),
        ]
        interfaces[0].interface_type = InterfaceType.LOOPBACK
        interfaces[1].interface_type = InterfaceType.ETHERNET
        interfaces[2].interface_type = InterfaceType.WIRELESS

        mock_collect.return_value = interfaces

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == ExitCode.SUCCESS
        mock_format.assert_called_once_with(interfaces)


class TestMainIntegration:
    """Integration tests for main function (marked for optional execution)."""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not Path("/sys/class/net/lo").exists(),
        reason="Requires real Linux system"
    )
    def test_main_real_system(self, monkeypatch, capsys) -> None:
        """Test main on real system (integration test).

        This test runs the actual netcheck tool on real hardware.
        Mark with @pytest.mark.integration to skip in CI.
        """
        # Set up minimal arguments
        monkeypatch.setattr(sys, "argv", ["netcheck"])

        with pytest.raises(SystemExit) as exc_info:
            main()

        # Should succeed on any Linux system (at least has loopback)
        assert exc_info.value.code == ExitCode.SUCCESS

        # Should have printed table
        captured = capsys.readouterr()
        assert "INTERFACE" in captured.out
        assert "lo" in captured.out  # Loopback always present

    @pytest.mark.integration
    def test_main_json_export_real(self, monkeypatch, tmp_path, capsys) -> None:
        """Test JSON export on real system (integration test)."""
        output_file = tmp_path / "test_report.json"

        monkeypatch.setattr(
            sys,
            "argv",
            ["netcheck", "--export", "json", "--output", str(output_file)]
        )

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == ExitCode.SUCCESS
        assert output_file.exists()

        # Verify JSON is valid
        import json
        data = json.loads(output_file.read_text())
        assert "metadata" in data
        assert "interfaces" in data
