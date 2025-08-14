"""
Environment validation for media2vid.
"""
import subprocess
import logging
from pathlib import Path
from .exceptions import EnvironmentError

def validate_environment(logger: logging.Logger) -> bool:
    """
    Validate that the environment is ready for video processing.
    
    Args:
        logger: Logger instance for output
        
    Returns:
        True if environment is valid, False otherwise
        
    Raises:
        EnvironmentError: If critical requirements are missing
    """
    try:
        # Check FFmpeg availability
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            raise EnvironmentError("FFmpeg not found or not working properly")
        
        # Extract FFmpeg version for logging
        version_line = result.stdout.split('\n')[0] if result.stdout else "Unknown version"
        logger.debug(f"FFmpeg available: {version_line}")
        
        # Check ffprobe availability  
        result = subprocess.run(['ffprobe', '-version'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            raise EnvironmentError("ffprobe not found - required for media analysis")
            
        logger.debug("ffprobe available")
        
        # Check write permissions in current directory
        test_file = Path('.video_processor_test')
        try:
            test_file.touch()
            test_file.unlink()
        except OSError as e:
            raise EnvironmentError(f"No write permission in current directory: {e}")
        
        # Check temp directory creation
        temp_dir = Path("temp_")
        if not temp_dir.exists():
            try:
                temp_dir.mkdir()
                logger.debug("Created temp directory")
            except OSError as e:
                raise EnvironmentError(f"Cannot create temp directory: {e}")
        else:
            logger.debug("Temp directory exists")
            
        return True
        
    except subprocess.TimeoutExpired:
        raise EnvironmentError("FFmpeg/ffprobe commands timed out - system may be overloaded")
    except FileNotFoundError:
        raise EnvironmentError("FFmpeg not found in PATH - please install FFmpeg")
    except Exception as e:
        raise EnvironmentError(f"Environment validation failed: {e}")