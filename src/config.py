"""
Configuration and constants for media2vid.
"""
from pathlib import Path
from typing import Set, Tuple

# =============================================================================
# CONFIGURATION FLAGS
# =============================================================================

# Cache system control - when True, validates existing temp files before regenerating
use_cache = True

# =============================================================================
# DIRECTORY STRUCTURE DETECTION
# =============================================================================

# Check for existing INPUT/OUTPUT/LOGS directories and set path variables
input_dir = Path("INPUT") if Path("INPUT").exists() else Path(".")
output_dir = Path("OUTPUT") if Path("OUTPUT").exists() else Path(".")
logs_dir = Path("LOGS") if Path("LOGS").exists() else Path(".")

# =============================================================================
# MEDIA FILE EXTENSIONS
# =============================================================================

def get_media_extensions() -> Tuple[Set[str], Set[str]]:
    """
    Get the sets of supported video and audio file extensions.
    
    Returns:
        A tuple containing:
        - Set of video extensions (12 formats)
        - Set of audio extensions (9 formats)
        
    Note:
        Extensions are returned in lowercase for case-insensitive matching.
    """
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', 
                       '.webm', '.m4v', '.3gp', '.ts', '.mts', '.vob'}
    audio_extensions = {'.mp3', '.m4a', '.wav', '.flac', '.aac', '.ogg', 
                       '.wma', '.opus', '.mp2'}
    return video_extensions, audio_extensions

# =============================================================================
# PROCESSING STANDARDS
# =============================================================================

# Standard video parameters
STANDARD_RESOLUTION = "1920x1080"
STANDARD_FPS = 30
STANDARD_DURATION = 15  # seconds
INTRO_DURATION = 3  # seconds for PNG files

# Standard audio parameters
STANDARD_SAMPLE_RATE = 48000
STANDARD_AUDIO_BITRATE = "128k"
STANDARD_AUDIO_CHANNELS = "stereo"

# Video encoding parameters
DEFAULT_CRF = 23
DEFAULT_PRESET = "medium"
DEFAULT_PIXEL_FORMAT = "yuv420p"
DEFAULT_PROFILE = "high"

# Audio processing parameters
TARGET_LOUDNESS = -16  # LUFS for EBU R128
TARGET_TRUE_PEAK = -1.5
TARGET_LRA = 11

def setup_global_config():
    """
    Setup global configuration based on current directory structure.
    This function should be called at startup to initialize paths.
    """
    global input_dir, output_dir, logs_dir
    
    # Re-check directory structure at runtime
    input_dir = Path("INPUT") if Path("INPUT").exists() else Path(".")
    output_dir = Path("OUTPUT") if Path("OUTPUT").exists() else Path(".")
    logs_dir = Path("LOGS") if Path("LOGS").exists() else Path(".")