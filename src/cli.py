"""
Command line interface for media2vid.
"""
import argparse

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Universal video montage creation script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python media2vid.py                    # Normal operation with colored output
  python media2vid.py --quiet            # Show only warnings and errors
  python media2vid.py --verbose          # Show all debug information
  python media2vid.py --silent           # Minimal output, log to file only
  python media2vid.py --audio-bg-pic bg.png  # Use specific background for all audio files
        """
    )
    
    parser.add_argument(
        '--log-level', 
        choices=['silent', 'quiet', 'normal', 'verbose'],
        default='normal',
        help='Set logging verbosity level (default: normal)'
    )
    
    parser.add_argument(
        '--no-console',
        action='store_true',
        help='Disable console output, log to file only'
    )
    
    parser.add_argument(
        '--no-file',
        action='store_true', 
        help='Disable file logging, console output only'
    )
    
    parser.add_argument(
        '--audio-bg-pic',
        type=str,
        metavar='FILE',
        help='Specify background image for all audio files (overrides automatic search)'
    )
    
    return parser.parse_args()