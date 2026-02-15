"""Tests for utils/system.py.

Tests system command execution and sanitization utilities.
"""

import subprocess
from unittest.mock import Mock, patch

import pytest

from utils.system import command_exists, run_command, sanitize_for_log


class TestRunCommand:
    """Tests for run_command function."""

    @patch("subprocess.run")
    def test_successful_command(self, mock_run):
        """Test successful command execution."""
        mock_run.return_value = Mock(returncode=0, stdout="output\n")
        result = run_command(["echo", "test"])
        assert result == "output"
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert args[0] == ["echo", "test"]
        assert kwargs["shell"] is False

    @patch("subprocess.run")
    def test_command_failure(self, mock_run):
        """Test failed command returns None."""
        mock_run.return_value = Mock(returncode=1, stdout="")
        result = run_command(["false"])
        assert result is None

    @patch("subprocess.run")
    def test_command_timeout(self, mock_run):
        """Test command timeout returns None."""
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 10)
        result = run_command(["sleep", "100"])
        assert result is None

    @patch("subprocess.run")
    def test_command_not_found(self, mock_run):
        """Test command not found returns None."""
        mock_run.side_effect = FileNotFoundError()
        result = run_command(["nonexistent"])
        assert result is None

    @patch("subprocess.run")
    def test_os_error(self, mock_run):
        """Test OSError returns None."""
        mock_run.side_effect = OSError("error")
        result = run_command(["test"])
        assert result is None

    @patch("subprocess.run")
    def test_value_error(self, mock_run):
        """Test ValueError returns None."""
        mock_run.side_effect = ValueError("error")
        result = run_command(["test"])
        assert result is None

    @patch("subprocess.run")
    def test_runtime_error(self, mock_run):
        """Test RuntimeError returns None."""
        mock_run.side_effect = RuntimeError("error")
        result = run_command(["test"])
        assert result is None

    @patch("subprocess.run")
    def test_shell_false_always(self, mock_run):
        """Test shell=False is always used (security)."""
        mock_run.return_value = Mock(returncode=0, stdout="test")
        run_command(["test"])
        args, kwargs = mock_run.call_args
        assert kwargs["shell"] is False

    @patch("subprocess.run")
    def test_output_stripped(self, mock_run):
        """Test output is stripped of whitespace."""
        mock_run.return_value = Mock(returncode=0, stdout="  output  \n")
        result = run_command(["test"])
        assert result == "output"


class TestCommandExists:
    """Tests for command_exists function."""

    @patch("shutil.which")
    def test_command_exists_true(self, mock_which):
        """Test existing command returns True."""
        mock_which.return_value = "/usr/bin/test"
        assert command_exists("test") is True

    @patch("shutil.which")
    def test_command_exists_false(self, mock_which):
        """Test non-existing command returns False."""
        mock_which.return_value = None
        assert command_exists("nonexistent") is False

    @patch("shutil.which")
    def test_multiple_calls(self, mock_which):
        """Test multiple calls work correctly."""
        mock_which.side_effect = ["/usr/bin/ls", None, "/bin/cat"]
        assert command_exists("ls") is True
        assert command_exists("notfound") is False
        assert command_exists("cat") is True


class TestSanitizeForLog:
    """Tests for sanitize_for_log function."""

    def test_normal_string(self):
        """Test normal string is unchanged."""
        assert sanitize_for_log("normal text") == "normal text"
        assert sanitize_for_log("test123") == "test123"

    def test_remove_newlines(self):
        """Test newlines are replaced with spaces."""
        assert sanitize_for_log("line1\nline2") == "line1 line2"
        assert sanitize_for_log("line1\r\nline2") == "line1  line2"

    def test_remove_ansi_escapes(self):
        """Test ANSI escape codes are removed."""
        assert sanitize_for_log("\x1b[91mred\x1b[0m") == "red"
        assert sanitize_for_log("\x1b[1mbold\x1b[0m") == "bold"

    def test_remove_control_characters(self):
        """Test control characters are removed."""
        assert sanitize_for_log("test\x00null") == "testnull"
        assert sanitize_for_log("test\x01control") == "testcontrol"

    def test_truncate_long_strings(self):
        """Test strings over 200 chars are truncated."""
        long_string = "a" * 250
        result = sanitize_for_log(long_string)
        assert len(result) == 200
        assert result.endswith("...")

    def test_preserve_spaces(self):
        """Test spaces are preserved."""
        assert sanitize_for_log("hello world") == "hello world"

    def test_non_string_input(self):
        """Test non-string input is converted to string."""
        assert sanitize_for_log(123) == "123"
        assert sanitize_for_log(None) == "None"
        assert sanitize_for_log([1, 2, 3]) == "[1, 2, 3]"

    def test_security_log_injection(self):
        """Test log injection attempts are sanitized."""
        malicious = "User: admin\nPASSWORD: secret"
        result = sanitize_for_log(malicious)
        assert "\n" not in result
        assert result == "User: admin PASSWORD: secret"
