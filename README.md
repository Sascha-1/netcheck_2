# Netcheck - Network Interface Analysis Tool

Comprehensive network interface analyzer for GNU/Linux systems. Provides detailed information about network configuration, security status, and VPN connectivity.

## Features

- **Interface Classification**: Ethernet, Wireless, VPN, USB Tethering, Bridge, Virtual, Loopback
- **Hardware Identification**: Via PCI/USB vendor/device IDs from sysfs
- **IP Configuration**: IPv4/IPv6 addresses with dual-stack support
- **DNS Analysis**: Configuration and deterministic leak detection
- **External IP Detection**: Public IP, ISP, country via ipinfo.io API
- **VPN Analysis**: Server endpoint detection and underlay interface identification
- **Routing Information**: Gateway and metric information
- **Visual Output**: Color-coded table showing security status
- **Export**: JSON format with metadata and summary

## Key Differentiators

1. **Deterministic Detection**: All values queried from system, never guessed or assumed
2. **DNS Leak Detection**: Configuration-based (not timing-based), recognizes VPN vs ISP vs Public DNS
3. **VPN Underlay Detection**: Identifies which physical interface carries VPN tunnel traffic
4. **ProtonVPN Support**: Detects OpenVPN and WireGuard, shows server endpoints
5. **No Root Required**: All operations use unprivileged APIs

## Requirements

### System Requirements
- **OS**: GNU/Linux with Kernel 6.12+
- **Python**: 3.12 or higher
- **systemd-resolved**: Required for DNS configuration

### System Commands
All of these must be installed:
- `ip` (iproute2)
- `lspci` (pciutils)
- `lsusb` (usbutils)
- `ethtool`
- `resolvectl` (systemd-resolved)
- `ss` (iproute2)

### Installation on Debian/Ubuntu
```bash
sudo apt install iproute2 pciutils usbutils ethtool systemd-resolved
```

## Installation

```bash
# Clone repository
git clone https://github.com/user/netcheck.git
cd netcheck

# Install dependencies
pip install -r requirements.txt

# Install in development mode (optional)
pip install -e .
```

## Usage

### Basic Usage
```bash
# Display table
python netcheck.py

# Verbose output
python netcheck.py -v

# Export to JSON (stdout)
python netcheck.py --export json

# Export to file
python netcheck.py --export json --output report.json

# Log to file
python netcheck.py -v --log-file debug.log
```

### Example Output
```
====================================================================================================================================================================================================
Network Interface Analysis
====================================================================================================================================================================================================
INTERFACE        TYPE        DEVICE                INTERNAL_IPv4    INTERNAL_IPv6              DNS_SERVER            EXTERNAL_IPv4    EXTERNAL_IPv6              ISP              COUNTRY     GATEWAY          METRIC
====================================================================================================================================================================================================
lo               loopback    N/A                   127.0.0.1        ::1                        --                    --               --                         --               --          NONE             NONE
eth0             ethernet    Intel I219-V          192.168.1.100    2001:db8::1                192.168.1.1           203.0.113.45     2001:db8::45               Comcast          US          192.168.1.1      100
tun0             vpn         N/A                   10.8.0.2         N/A                        10.8.0.1              203.0.113.99     N/A                        ProtonVPN        CH          10.8.0.1         50
====================================================================================================================================================================================================

Color Legend:
GREEN  - VPN tunnel (encrypted, DNS OK)
CYAN   - Physical interface carrying VPN
RED    - Direct internet (unencrypted)
YELLOW - DNS leak, public DNS, or warning

DNS Status Meanings:
  OK     - Using VPN DNS (best privacy - VPN provider sees queries)
  PUBLIC - Using public DNS (Cloudflare/Google/Quad9 - not leaking to ISP, but suboptimal)
  LEAK   - Using ISP DNS (security issue - ISP sees all queries, defeats VPN privacy)
  WARN   - Using unknown DNS (investigate further)
  --     - Not applicable (no VPN active or no DNS configured)
```

## Color Coding

The table uses colors to indicate security status:

- **GREEN**: VPN tunnel with proper DNS configuration (encrypted, privacy protected)
- **CYAN**: Physical interface carrying VPN traffic (underlay)
- **RED**: Direct internet connection (unencrypted, no VPN)
- **YELLOW**: DNS leak detected, using public DNS, or configuration warning

## DNS Leak Detection

Netcheck uses **deterministic, configuration-based** DNS leak detection:

1. **Not timing-based**: Unlike other tools, we don't rely on DNS query timing
2. **Configuration analysis**: Compares configured DNS servers against VPN/ISP/Public DNS
3. **Clear status indicators**:
   - `OK`: Using VPN DNS (best privacy)
   - `PUBLIC`: Using Cloudflare/Google/Quad9 (not leaking to ISP, but suboptimal)
   - `LEAK`: Using ISP DNS (critical security issue)
   - `WARN`: Using unknown DNS servers (investigate)
   - `--`: Not applicable (no VPN or no DNS configured)

### Why List Public DNS Providers?

To give users actionable information:
- **ISP DNS**: Your ISP sees all queries → Critical leak
- **Public DNS**: Third-party sees queries, but NOT your ISP → Suboptimal but not leaking
- **VPN DNS**: VPN provider sees queries (trusted) → Ideal

## VPN Detection

Supports ProtonVPN (OpenVPN and WireGuard):

- Detects VPN server endpoints by analyzing active connections
- Identifies physical interface carrying VPN traffic (underlay detection)
- Shows VPN server IP addresses
- Detects common VPN ports: 51820 (WireGuard), 1194/443 (OpenVPN)

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Missing dependencies
- `4`: Invalid arguments

## Design Philosophy

1. **Deterministic Behavior Over Heuristics**: Never guess values, query kernel directly
2. **Explicit Over Implicit**: All configuration visible in config.py
3. **Clear Code Over Clever Code**: Readability prioritized
4. **Type Safety Throughout**: Complete type annotations (mypy --strict)
5. **No Backward Compatibility**: Target modern environments only (Python 3.12+, Kernel 6.12+)

## Development

### Run Tests
```bash
make test
```

### Run Linters
```bash
make lint
```

### Format Code
```bash
make format
```

### Run All Checks
```bash
make check
```

## Security

- **No root required**: All operations use unprivileged APIs
- **No shell=True**: Prevents command injection
- **Input validation**: All inputs validated before use
- **Timeout protection**: 10s timeout on all operations
- **Log sanitization**: Prevents log injection

## License

AGPL v3 - See LICENSE file for details

## Contributing

Contributions welcome! Please ensure:
- Type safety: `mypy --strict` passes
- Code quality: `ruff` and `pylint` pass
- Test coverage: ≥87%
- Follow design philosophy (deterministic, explicit, clear)

## Acknowledgments

Built with a focus on deterministic behavior and user privacy.
