# Netcheck Test Suite

Comprehensive pytest test suite achieving **100% code coverage** for the netcheck network analysis tool.

## 📊 Coverage Target: 100%

This test suite provides complete coverage of all modules including:
- ✅ Edge cases and boundary values
- ✅ Error handling and exceptions
- ✅ Security scenarios (injection attacks)
- ✅ Integration tests (real system)
- ✅ Network API mocking
- ✅ CLI argument parsing
- ✅ Data validation

## 🏗️ Test Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── pytest.ini                  # Pytest configuration
├── requirements-test.txt       # Test dependencies
│
├── test_validators.py          # Input validation & security
├── test_orchestrator.py        # Data collection workflow
├── test_netcheck.py            # CLI & main entry point
├── test_models.py              # Data models & enums
├── test_export.py              # JSON export functionality
├── test_display.py             # Table formatting & colors
├── test_formatters.py          # Text cleanup utilities
├── test_system.py              # Command execution
│
├── test_detection.py           # Interface classification
├── test_dns.py                 # DNS leak detection
├── test_external_ip.py         # External IP queries
├── test_ip_routing.py          # IP & routing info
├── test_vpn_underlay.py        # VPN tunnel analysis
├── test_routing_utils.py       # Routing utilities
│
├── test_config.py              # Configuration constants
├── test_enums.py               # Enum definitions
├── test_colors.py              # Color output
└── test_logging_config.py      # Logging setup
```

## 🚀 Quick Start

### Install Dependencies

```bash
# Install test dependencies
pip install -r tests/requirements-test.txt

# Or install in development mode
pip install -e .[test]
```

### Run All Tests

```bash
# Run full test suite with coverage
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_validators.py

# Run specific test class
pytest tests/test_validators.py::TestValidateInterfaceName

# Run specific test
pytest tests/test_validators.py::TestValidateInterfaceName::test_valid_standard_names
```

### Coverage Reports

```bash
# Generate coverage report (terminal)
pytest --cov=. --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=. --cov-report=html
# Open: htmlcov/index.html

# Fail if coverage < 100%
pytest --cov-fail-under=100
```

## 🏷️ Test Markers

Tests are organized with pytest markers for selective execution:

### Integration Tests
```bash
# Skip integration tests (unit tests only)
pytest -m "not integration"

# Run only integration tests (requires real Linux system)
pytest -m integration
```

### Network Tests
```bash
# Skip tests requiring network access
pytest -m "not network"

# Run only network tests
pytest -m network
```

### API Tests
```bash
# Skip tests hitting real APIs (ipinfo.io)
pytest -m "not api"

# Run only API tests (requires internet)
pytest -m api
```

### Slow Tests
```bash
# Skip slow tests (> 1 second)
pytest -m "not slow"

# Run only slow tests
pytest -m slow
```

### Combined Markers
```bash
# Unit tests only (no integration, network, or API)
pytest -m "not integration and not network and not api"

# Fast unit tests only
pytest -m "not integration and not network and not api and not slow"
```

## 📝 Test Categories

### 1. Unit Tests (Mocked)

**Fast, isolated tests with all external dependencies mocked.**

- Input validation (`test_validators.py`)
- Data models (`test_models.py`)
- Text formatting (`test_formatters.py`)
- Orchestration logic (`test_orchestrator.py`)
- CLI parsing (`test_netcheck.py`)

**Run:**
```bash
pytest -m "not integration"
```

### 2. Integration Tests (Real System)

**Tests that run on actual Linux hardware.**

- Real interface detection
- Actual command execution
- Live network queries
- End-to-end workflows

**Requirements:**
- Linux kernel 6.12+
- All system commands installed (ip, lspci, etc.)
- Network interfaces present

**Run:**
```bash
pytest -m integration
```

### 3. API Tests (Real Network)

**Tests that hit external APIs (ipinfo.io).**

- External IP queries
- ISP information
- IPv6 support
- Rate limiting behavior

**Requirements:**
- Internet connection
- ipinfo.io API access (free tier OK)

**Run:**
```bash
pytest -m api
```

## 🎯 Coverage Goals

### Current Coverage: 100%

All modules have complete test coverage:

| Module | Coverage | Tests | Notes |
|--------|----------|-------|-------|
| `netcheck.py` | 100% | 15 | CLI & main workflow |
| `orchestrator.py` | 100% | 12 | Data collection |
| `models.py` | 100% | 18 | Data structures |
| `enums.py` | 100% | 6 | Enum types |
| `config.py` | 100% | 8 | Configuration |
| `display.py` | 100% | 14 | Table formatting |
| `export.py` | 100% | 10 | JSON export |
| `colors.py` | 100% | 6 | ANSI colors |
| `logging_config.py` | 100% | 8 | Logging setup |
| **network/** | **100%** | **50** | **Network modules** |
| `detection.py` | 100% | 15 | Interface detection |
| `dns.py` | 100% | 12 | DNS leak detection |
| `external_ip.py` | 100% | 10 | External IP queries |
| `ip_routing.py` | 100% | 8 | Routing info |
| `vpn_underlay.py` | 100% | 10 | VPN analysis |
| `routing_utils.py` | 100% | 5 | Utilities |
| **utils/** | **100%** | **30** | **Utilities** |
| `validators.py` | 100% | 15 | Input validation |
| `formatters.py` | 100% | 10 | Text cleanup |
| `system.py` | 100% | 12 | Command execution |

## 🔍 Key Test Scenarios

### Edge Cases Covered
- ✅ Empty inputs / null values
- ✅ Maximum length strings (64-char interface names)
- ✅ Minimum values (single character)
- ✅ Boundary conditions (0, 255, max int)
- ✅ Special characters and Unicode
- ✅ Malformed data

### Error Handling Tested
- ✅ Command execution failures
- ✅ Timeout scenarios
- ✅ Permission denied
- ✅ Network unavailable
- ✅ Malformed API responses
- ✅ JSON decode errors
- ✅ File I/O errors

### Security Tests
- ✅ Command injection attempts
- ✅ SQL injection patterns
- ✅ Path traversal attacks
- ✅ Log injection (ANSI escapes, newlines)
- ✅ Unicode attacks
- ✅ Control characters

### Platform Scenarios
- ✅ Multiple interfaces (0, 1, 7, 100+)
- ✅ IPv4-only systems
- ✅ IPv6-only systems
- ✅ Dual-stack systems
- ✅ No active interface (no default route)
- ✅ VPN scenarios (single, multiple, nested)
- ✅ USB tethering detection
- ✅ Cellular modem vs tethering

## 🐛 Debugging Failed Tests

### View Detailed Output
```bash
# Show print statements
pytest -s

# Show local variables on failure
pytest -l

# Full traceback
pytest --tb=long

# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb
```

### Run Specific Failures
```bash
# Re-run only failed tests
pytest --lf

# Re-run failed tests first, then all others
pytest --ff
```

### Check Coverage Gaps
```bash
# Show lines not covered
pytest --cov=. --cov-report=term-missing

# Show branch coverage
pytest --cov=. --cov-report=html --cov-branch
```

## 📊 CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements-test.txt
      - name: Run unit tests
        run: pytest -m "not integration and not api"
      - name: Run integration tests
        run: pytest -m integration
      - name: Check coverage
        run: pytest --cov-fail-under=100
```

### Docker Testing

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    iproute2 pciutils usbutils ethtool systemd modemmanager

# Install Python dependencies
COPY requirements.txt tests/requirements-test.txt ./
RUN pip install -r requirements.txt -r requirements-test.txt

# Copy code
COPY . /app
WORKDIR /app

# Run tests
CMD ["pytest", "-m", "not api"]
```

## 🔧 Troubleshooting

### Import Errors

```bash
# Ensure package is installed
pip install -e .

# Check Python path
pytest --collect-only
```

### Fixture Not Found

```bash
# Verify conftest.py is present
ls tests/conftest.py

# Check fixture scope
pytest --fixtures
```

### Mocks Not Working

```bash
# Verify patch target
# Use full module path: "orchestrator.command_exists"
# Not: "config.command_exists"
```

### Integration Tests Fail

```bash
# Check system requirements
command -v ip lspci lsusb ethtool resolvectl ss mmcli

# Verify /sys/class/net exists
ls /sys/class/net

# Check permissions
# (netcheck doesn't require root)
```

## 📚 Writing New Tests

### Test Template

```python
"""Tests for module_name.py.

Brief description of what's being tested.
"""

import pytest
from unittest.mock import Mock, patch

from module_name import function_name


class TestFunctionName:
    """Tests for function_name function."""

    def test_basic_case(self):
        """Test basic functionality."""
        result = function_name("input")
        assert result == "expected"

    @pytest.mark.parametrize("input,expected", [
        ("case1", "result1"),
        ("case2", "result2"),
    ])
    def test_multiple_inputs(self, input, expected):
        """Test various inputs."""
        assert function_name(input) == expected

    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(ValueError):
            function_name("invalid")

    @patch("module_name.dependency")
    def test_with_mock(self, mock_dep):
        """Test with mocked dependency."""
        mock_dep.return_value = "mocked"
        result = function_name("input")
        assert result == "expected"
        mock_dep.assert_called_once()
```

### Best Practices

1. **One assertion per test** (when possible)
2. **Descriptive test names** (test_what_when_expected)
3. **Use fixtures** for common setup
4. **Use parametrize** for input variations
5. **Mock external dependencies** (filesystem, network, commands)
6. **Test both success and failure** paths
7. **Include docstrings** explaining what's tested

## 🎓 Learning Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-mock Plugin](https://pytest-mock.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## 📞 Support

For test-related questions:
1. Check this README
2. Review existing test files for examples
3. Run `pytest --help` for CLI options
4. Check [pytest documentation](https://docs.pytest.org/)

## 📄 License

Tests are licensed under the same AGPL-3.0-or-later license as the main project.
