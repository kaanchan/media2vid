"""
PNG intro file processing for media2vid.
"""
from pathlib import Path
from typing import Optional

try:
    from colorama import Fore, Style
except ImportError:
    class Fore:
        RED = ""
    class Style:
        RESET_ALL = ""

def process_intro_file(filename: str, output_path: str, title_screen_path: Optional[Path] = None, duration: int = 3) -> bool:
    """
    Process PNG intro file by converting to video with silent audio track.
    
    Creates a standardized video from PNG image with specified duration,
    using the same output format as all other processed files for seamless concatenation.
    
    Args:
        filename: Path to the PNG file to process
        output_path: Path where the processed video will be saved
        title_screen_path: Optional title screen path (unused for intro processing)
        duration: Duration in seconds for the intro video (default: 3)
        
    Returns:
        True if processing succeeded, False if it failed
        
    Note:
        Output video will have: 1920x1080, 30fps, H.264, yuv420p, AAC audio
    """
    from ..ffmpeg_utils import get_video_filter, build_base_ffmpeg_cmd, run_ffmpeg_with_error_handling
    
    try:
        # Convert PNG to video using standardized settings
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-i', filename,  # Loop the image
            '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000',  # Silent audio
            '-vf', get_video_filter(),  # Standard video scaling/padding
            '-shortest'  # End when shortest stream (duration) ends
        ] + build_base_ffmpeg_cmd(output_path, duration=duration)[2:]  # Skip 'ffmpeg -y' from base
        
        # Execute FFmpeg command
        return run_ffmpeg_with_error_handling(cmd, f"intro file {Path(filename).name}", output_path, filename, 'INTRO')
        
    except Exception as e:
        print(f"{Fore.RED}  ✗ FAILED: Unexpected error processing intro file {Path(filename).name}: {e}{Style.RESET_ALL}")
        return False