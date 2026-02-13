#!/usr/bin/env python3
"""Netcheck - Network Interface Analysis Tool.

Main entry point for the netcheck command-line tool.
"""

import argparse
import sys
import traceback
from pathlib import Path

from config import ExitCode
from display import format_output
from export import export_to_json
from logging_config import get_logger, setup_logging
from orchestrator import check_dependencies, collect_network_data
from utils import sanitize_for_log


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.

    Exits:
        Code 4 if invalid argument combinations.
    """
    parser = argparse.ArgumentParser(
        description="Network interface analysis tool for GNU/Linux",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  netcheck                    # Display table
  netcheck -v                 # Verbose output
  netcheck --export json      # Export to JSON (stdout)
  netcheck --export json --output report.json  # Export to file
  netcheck -v --log-file debug.log  # Log to file

Exit codes:
  0 - Success
  1 - General error
  2 - Missing dependencies
  4 - Invalid arguments
        """,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    parser.add_argument(
        "--log-file",
        type=Path,
        metavar="PATH",
        help="Write logs to file",
    )

    parser.add_argument(
        "--export",
        choices=["json"],
        metavar="FORMAT",
        help="Export format (json only in v1.0)",
    )

    parser.add_argument(
        "--output",
        type=Path,
        metavar="PATH",
        help="Export destination file (requires --export)",
    )

    args = parser.parse_args()

    # Validation: --output requires --export
    if args.output and not args.export:
        print("Error: --output requires --export", file=sys.stderr)
        sys.exit(ExitCode.INVALID_ARGUMENTS)

    return args


def main() -> None:
    """Main execution flow.

    Exit codes:
        0: Success
        1: General error
        2: Missing dependencies
        4: Invalid arguments
    """
    args = parse_arguments()

    # Setup logging (must be called before any logger usage)
    setup_logging(
        verbose=args.verbose,
        log_file=args.log_file,
        use_colors=True,  # Always enabled
    )

    logger = get_logger(__name__)

    # Check dependencies
    if not check_dependencies():
        logger.error("Missing required dependencies - cannot continue")
        sys.exit(ExitCode.MISSING_DEPENDENCIES)

    try:
        # Collect data
        logger.info("Starting network data collection...")
        interfaces = collect_network_data()

        if not interfaces:
            logger.error("No network interfaces found")
            sys.exit(ExitCode.GENERAL_ERROR)

        logger.info("Successfully collected data for %d interfaces", len(interfaces))

        # Output
        if args.export:
            json_data = export_to_json(interfaces)
            if args.output:
                args.output.write_text(json_data)
                logger.info("Exported to %s", sanitize_for_log(str(args.output)))
            else:
                print(json_data)
        else:
            # Display table to stdout
            format_output(interfaces)

            # If log file and verbose, also write table to log file
            if args.log_file and args.verbose:
                with args.log_file.open('a') as f:
                    f.write("\n")  # Separator between logs and table
                    format_output(interfaces, file=f)

        sys.exit(ExitCode.SUCCESS)

    except KeyboardInterrupt:
        logger.error("Interrupted by user")
        sys.exit(ExitCode.GENERAL_ERROR)
    except (OSError, IOError, ValueError, RuntimeError) as e:
        logger.error("Error during execution: %s", sanitize_for_log(str(e)))
        if args.verbose:
            traceback.print_exc()
        sys.exit(ExitCode.GENERAL_ERROR)


if __name__ == "__main__":
    main()
