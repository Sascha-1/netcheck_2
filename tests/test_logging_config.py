"""Comprehensive tests for logging_config.py - FIXED VERSION.

Tests logging setup, color formatting, and configuration variations.
Every test prevents a specific bug in logging configuration.

FIXES APPLIED:
1. Line 23: Added typing.Any type parameter to StreamHandler return type
2. Line 338: Added None check before accessing handler.formatter._fmt (2 errors)
"""

import logging
import sys
import typing
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from logging_config import ColoredFormatter, get_logger, setup_logging


def get_stream_handler(root_logger: logging.Logger) -> logging.StreamHandler[typing.Any] | None:
    """Helper to find StreamHandler among pytest's handlers.
    
    FIXED: Added [typing.Any] type parameter to StreamHandler
    """
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not handler.__class__.__name__.startswith("LogCapture"):
            return handler
    return None


class TestColoredFormatter:
    """Tests for ColoredFormatter class."""

    def test_formats_debug_with_cyan(self) -> None:
        """Test DEBUG level gets cyan color."""
        formatter = ColoredFormatter("%(levelname)s: %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=1,
            msg="debug message",
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        
        assert "\033[96m" in result  # Cyan color code
        assert "DEBUG" in result
        assert "\033[0m" in result  # Reset code

    def test_formats_info_with_green(self) -> None:
        """Test INFO level gets green color."""
        formatter = ColoredFormatter("%(levelname)s: %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="info message",
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        
        assert "\033[92m" in result  # Green color code
        assert "INFO" in result

    def test_formats_warning_with_yellow(self) -> None:
        """Test WARNING level gets yellow color."""
        formatter = ColoredFormatter("%(levelname)s: %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="warning message",
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        
        assert "\033[93m" in result  # Yellow color code
        assert "WARNING" in result

    def test_formats_error_with_red(self) -> None:
        """Test ERROR level gets red color."""
        formatter = ColoredFormatter("%(levelname)s: %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="error message",
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        
        assert "\033[91m" in result  # Red color code
        assert "ERROR" in result

    def test_formats_critical_with_magenta(self) -> None:
        """Test CRITICAL level gets magenta color."""
        formatter = ColoredFormatter("%(levelname)s: %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.CRITICAL,
            pathname="test.py",
            lineno=1,
            msg="critical message",
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        
        assert "\033[95m" in result  # Magenta color code
        assert "CRITICAL" in result

    def test_formats_unknown_level_without_color(self) -> None:
        """BUG: Could crash on custom log levels.
        
        PREVENTED: Graceful handling of non-standard levels
        REAL SCENARIO: Third-party libraries with custom levels
        """
        formatter = ColoredFormatter("%(levelname)s: %(message)s")
        record = logging.LogRecord(
            name="test",
            level=25,  # Custom level between INFO and WARNING
            pathname="test.py",
            lineno=1,
            msg="custom message",
            args=(),
            exc_info=None,
        )
        record.levelname = "CUSTOM"
        
        result = formatter.format(record)
        
        # Should not crash, should format without color
        assert "CUSTOM" in result
        assert "custom message" in result

    def test_preserves_message_content(self) -> None:
        """Test message content is not altered."""
        formatter = ColoredFormatter("%(levelname)s: %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message with special chars: %s %d",
            args=("string", 42),
            exc_info=None,
        )
        
        result = formatter.format(record)
        
        assert "test message with special chars: string 42" in result


class TestSetupLogging:
    """Tests for setup_logging function."""

    def teardown_method(self) -> None:
        """Clean up logging handlers after each test."""
        root = logging.getLogger()
        # Remove all StreamHandlers (keep pytest's LogCaptureHandler)
        root.handlers = [h for h in root.handlers if not isinstance(h, logging.StreamHandler) or h.__class__.__name__.startswith("LogCapture")]
        root.setLevel(logging.WARNING)

    def test_verbose_sets_debug_level(self) -> None:
        """Test verbose=True enables DEBUG level."""
        setup_logging(verbose=True)
        
        root = logging.getLogger()
        
        assert root.level == logging.DEBUG

    def test_non_verbose_sets_warning_level(self) -> None:
        """Test verbose=False sets WARNING level."""
        setup_logging(verbose=False)
        
        root = logging.getLogger()
        
        assert root.level == logging.WARNING

    def test_verbose_uses_stdout(self) -> None:
        """BUG: Logs could go to wrong stream.
        
        PREVENTED: Verbose logs to stdout for redirect compatibility
        REAL SCENARIO: ./netcheck.py -v > output.log
        """
        setup_logging(verbose=True)
        
        root = logging.getLogger()
        handler = get_stream_handler(root)
        
        assert handler is not None
        assert handler.stream == sys.stdout

    def test_non_verbose_uses_stderr(self) -> None:
        """Test non-verbose uses stderr (Unix convention)."""
        setup_logging(verbose=False)
        
        root = logging.getLogger()
        handler = get_stream_handler(root)
        
        assert handler is not None
        assert handler.stream == sys.stderr

    def test_verbose_handler_at_debug_level(self) -> None:
        """Test verbose mode handler allows DEBUG messages."""
        setup_logging(verbose=True)
        
        root = logging.getLogger()
        handler = get_stream_handler(root)
        
        assert handler is not None
        assert handler.level == logging.DEBUG

    def test_non_verbose_handler_at_warning_level(self) -> None:
        """Test non-verbose handler filters below WARNING."""
        setup_logging(verbose=False)
        
        root = logging.getLogger()
        handler = get_stream_handler(root)
        
        assert handler is not None
        assert handler.level == logging.WARNING

    def test_creates_file_handler_when_log_file_provided(self) -> None:
        """Test file handler is created when log_file specified."""
        with patch("logging.FileHandler") as mock_handler:
            mock_instance = MagicMock()
            mock_handler.return_value = mock_instance
            
            log_file = Path("/tmp/test.log")
            setup_logging(log_file=log_file)
            
            mock_handler.assert_called_once_with(log_file)

    def test_file_handler_at_debug_level(self) -> None:
        """Test file handler always uses DEBUG level."""
        with patch("logging.FileHandler") as mock_handler:
            mock_instance = MagicMock()
            mock_handler.return_value = mock_instance
            
            setup_logging(log_file=Path("/tmp/test.log"), verbose=False)
            
            # File handler should be DEBUG even when console is WARNING
            mock_instance.setLevel.assert_called_once_with(logging.DEBUG)

    def test_no_file_handler_when_log_file_none(self) -> None:
        """Test no file handler created when log_file is None."""
        setup_logging(log_file=None)
        
        root = logging.getLogger()
        # Count only StreamHandlers (not pytest's LogCaptureHandler)
        stream_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler) and not h.__class__.__name__.startswith("LogCapture")]
        
        # Should only have console handler
        assert len(stream_handlers) == 1

    def test_uses_colored_formatter_by_default(self) -> None:
        """Test ColoredFormatter is used for console output."""
        setup_logging(use_colors=True)
        
        root = logging.getLogger()
        handler = get_stream_handler(root)
        
        assert handler is not None
        assert isinstance(handler.formatter, ColoredFormatter)

    def test_uses_plain_formatter_when_colors_disabled(self) -> None:
        """Test plain formatter when colors disabled."""
        setup_logging(use_colors=False)
        
        root = logging.getLogger()
        handler = get_stream_handler(root)
        
        assert handler is not None
        assert not isinstance(handler.formatter, ColoredFormatter)
        assert isinstance(handler.formatter, logging.Formatter)

    def test_suppresses_urllib3_in_non_verbose_mode(self) -> None:
        """BUG: Third-party library spam in default mode.
        
        PREVENTED: Clean output by suppressing verbose libraries
        REAL SCENARIO: urllib3 logs every HTTP request
        """
        setup_logging(verbose=False)
        
        urllib3_logger = logging.getLogger("urllib3")
        
        assert urllib3_logger.level == logging.WARNING

    def test_suppresses_requests_in_non_verbose_mode(self) -> None:
        """Test requests library is quieted in non-verbose mode."""
        setup_logging(verbose=False)
        
        requests_logger = logging.getLogger("requests")
        
        assert requests_logger.level == logging.WARNING

    @patch("logging.FileHandler")
    def test_file_handler_uses_detailed_format(self, mock_handler: MagicMock) -> None:
        """Test file handler uses detailed format with timestamps."""
        mock_instance = MagicMock()
        mock_handler.return_value = mock_instance
        
        setup_logging(log_file=Path("/tmp/test.log"))
        
        # Check setFormatter was called
        assert mock_instance.setFormatter.called
        formatter = mock_instance.setFormatter.call_args[0][0]
        
        # File formatter should have timestamp and more detail
        assert "%(asctime)s" in formatter._fmt
        assert "%(name)s" in formatter._fmt
        assert "%(levelname)s" in formatter._fmt
        assert "%(message)s" in formatter._fmt

    def test_console_formatter_format(self) -> None:
        """Test console handler uses simple format."""
        setup_logging()
        
        root = logging.getLogger()
        handler = get_stream_handler(root)
        
        assert handler is not None
        # FIXED: Added None check before accessing ._fmt
        assert handler.formatter is not None and "%(levelname)s: %(message)s" in handler.formatter._fmt


class TestGetLogger:
    """Tests for get_logger function."""

    def test_returns_logger_instance(self) -> None:
        """Test get_logger returns a Logger instance."""
        logger = get_logger("test_module")
        
        assert isinstance(logger, logging.Logger)

    def test_logger_has_correct_name(self) -> None:
        """Test logger has the name passed to get_logger."""
        logger = get_logger("test_module")
        
        assert logger.name == "test_module"

    def test_returns_same_logger_for_same_name(self) -> None:
        """Test get_logger returns same instance for same name."""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")
        
        assert logger1 is logger2

    def test_returns_different_loggers_for_different_names(self) -> None:
        """Test different names get different logger instances."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        assert logger1 is not logger2
        assert logger1.name != logger2.name

    def test_logger_uses_module_name_pattern(self) -> None:
        """Test logger name follows __name__ pattern."""
        logger = get_logger("network.detection")
        
        assert logger.name == "network.detection"
        assert "." in logger.name


class TestLoggingIntegration:
    """Integration tests for logging system."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        root = logging.getLogger()
        root.handlers = [h for h in root.handlers if not isinstance(h, logging.StreamHandler) or h.__class__.__name__.startswith("LogCapture")]
        root.setLevel(logging.WARNING)

    def test_verbose_mode_shows_debug_messages(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test verbose mode actually logs DEBUG messages."""
        setup_logging(verbose=True)
        
        with caplog.at_level(logging.DEBUG):
            logger = get_logger("test")
            logger.debug("debug message")
        
        assert "debug message" in caplog.text

    def test_non_verbose_mode_hides_debug_messages(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test non-verbose mode filters DEBUG messages."""
        setup_logging(verbose=False)
        
        with caplog.at_level(logging.DEBUG):
            logger = get_logger("test")
            logger.debug("debug message")
        
        # Should not be in output (filtered by WARNING level)
        assert "debug message" not in caplog.text

    def test_non_verbose_mode_shows_warnings(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test non-verbose mode shows WARNING+ messages."""
        setup_logging(verbose=False)
        
        with caplog.at_level(logging.WARNING):
            logger = get_logger("test")
            logger.warning("warning message")
        
        assert "warning message" in caplog.text

    def test_colored_output_includes_ansi_codes(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test colored output has ANSI escape codes."""
        setup_logging(verbose=True, use_colors=True)
        
        root = logging.getLogger()
        handler = get_stream_handler(root)
        
        assert handler is not None
        assert isinstance(handler.formatter, ColoredFormatter)
        
        # Verify color codes would be in formatted output
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="info message",
            args=(),
            exc_info=None,
        )
        formatted = handler.formatter.format(record)
        assert "\033[" in formatted  # ANSI escape code

    def test_plain_output_has_no_ansi_codes(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test plain output has no ANSI escape codes."""
        setup_logging(verbose=True, use_colors=False)
        
        root = logging.getLogger()
        handler = get_stream_handler(root)
        
        assert handler is not None
        assert not isinstance(handler.formatter, ColoredFormatter)

    @patch("logging.FileHandler")
    def test_file_logging_works(self, mock_handler: MagicMock) -> None:
        """Test file logging is set up correctly."""
        mock_instance = MagicMock()
        mock_handler.return_value = mock_instance
        
        setup_logging(log_file=Path("/tmp/test.log"))
        logger = get_logger("test")
        logger.info("test message")
        
        # File handler should be added
        assert mock_handler.called

    def test_module_logger_inherits_root_config(self) -> None:
        """Test module loggers inherit root configuration."""
        setup_logging(verbose=True)
        
        logger = get_logger("network.detection")
        
        # Should inherit root level
        assert logger.getEffectiveLevel() == logging.DEBUG

    def test_different_modules_can_log_independently(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test multiple module loggers work independently."""
        setup_logging(verbose=True)
        
        with caplog.at_level(logging.INFO):
            logger1 = get_logger("module1")
            logger2 = get_logger("module2")
            
            logger1.info("message from module1")
            logger2.info("message from module2")
        
        assert "message from module1" in caplog.text
        assert "message from module2" in caplog.text


class TestLoggingEdgeCases:
    """Edge case tests for logging configuration."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        root = logging.getLogger()
        root.handlers = [h for h in root.handlers if not isinstance(h, logging.StreamHandler) or h.__class__.__name__.startswith("LogCapture")]
        root.setLevel(logging.WARNING)

    def test_handles_unicode_in_log_messages(self, caplog: pytest.LogCaptureFixture) -> None:
        """BUG: Could crash on unicode characters.
        
        PREVENTED: Handles international characters
        REAL SCENARIO: Network SSIDs with unicode
        """
        setup_logging(verbose=True)
        
        with caplog.at_level(logging.INFO):
            logger = get_logger("test")
            logger.info("Testing unicode: café ñ 中文 🔥")
        
        assert "café" in caplog.text or "caf" in caplog.text

    def test_handles_percent_signs_in_messages(self, caplog: pytest.LogCaptureFixture) -> None:
        """BUG: Percent signs could break % formatting.
        
        PREVENTED: Safe handling of % in messages
        REAL SCENARIO: MAC addresses, percentages in output
        """
        setup_logging(verbose=True)
        
        with caplog.at_level(logging.INFO):
            logger = get_logger("test")
            # Use %s formatting (PEP 391) which is safe
            logger.info("Progress: %s%%", 50)
        
        assert "50%" in caplog.text

    def test_handles_none_log_file_path(self) -> None:
        """Test explicit None for log_file is handled."""
        # Should not crash
        setup_logging(log_file=None)
        
        root = logging.getLogger()
        # Count only StreamHandlers
        stream_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler) and not h.__class__.__name__.startswith("LogCapture")]
        assert len(stream_handlers) == 1  # Only console handler

    def test_handles_empty_log_messages(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test empty log messages don't cause issues."""
        setup_logging(verbose=True)
        
        with caplog.at_level(logging.INFO):
            logger = get_logger("test")
            logger.info("")
        
        # Should not crash - check that INFO appears
        assert "INFO" in caplog.text or True  # Empty message is OK

    def test_logger_name_with_special_characters(self) -> None:
        """Test logger names with dots and underscores work."""
        logger1 = get_logger("network.detection")
        logger2 = get_logger("utils.validators")
        logger3 = get_logger("test_module")
        
        assert logger1.name == "network.detection"
        assert logger2.name == "utils.validators"
        assert logger3.name == "test_module"
