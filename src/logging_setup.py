"""
Logging configuration and setup for media2vid.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    print("Warning: colorama not installed. Install with: pip install colorama")
    # Fallback to no colors
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = WHITE = ""
    class Style:
        RESET_ALL = ""

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    COLORS = {
        'DEBUG': Fore.WHITE,
        'INFO': Fore.CYAN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.MAGENTA,
        'SUCCESS': Fore.GREEN,
    }
    
    def format(self, record):
        # Add color to levelname
        if hasattr(record, 'color'):
            color = self.COLORS.get(record.color.upper(), '')
        else:
            color = self.COLORS.get(record.levelname, '')
        
        # Format without color for file output
        if not hasattr(self, 'use_color') or not self.use_color:
            return super().format(record)
        
        # Apply color for console output
        record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)

def setup_logging(verbosity: str = 'normal', console_output: bool = True, file_output: bool = True) -> logging.Logger:
    """
    Configure logging with flexible routing options.
    
    Args:
        verbosity: 'silent', 'quiet', 'normal', 'verbose'
        console_output: Show messages on screen
        file_output: Save messages to log file
        
    Returns:
        Configured logger instance
    """
    from .config import logs_dir
    
    VERBOSITY_LEVELS = {
        'silent': logging.CRITICAL,
        'quiet': logging.WARNING,
        'normal': logging.INFO,
        'verbose': logging.DEBUG
    }
    
    # Create logger
    logger = logging.getLogger('video_processor')
    logger.setLevel(logging.DEBUG)  # Capture everything
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler (with colors)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = ColoredFormatter(
            '%(message)s'  # Simple format for console
        )
        console_formatter.use_color = True
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(VERBOSITY_LEVELS.get(verbosity, logging.INFO))
        logger.addHandler(console_handler)
    
    # File handler (detailed, no colors)
    if file_output and logs_dir.exists():
        log_file = logs_dir / f'video_processor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_formatter = ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_formatter.use_color = False
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)  # Always detailed in files
        logger.addHandler(file_handler)
    
    # Add custom log level for SUCCESS
    logging.addLevelName(25, 'SUCCESS')
    def success(self, message, *args, **kwargs):
        if self.isEnabledFor(25):
            self._log(25, message, args, **kwargs)
    logging.Logger.success = success
    
    return logger