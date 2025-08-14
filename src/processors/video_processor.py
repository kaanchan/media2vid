"""
Video file processing for media2vid.
"""
from pathlib import Path

try:
    from colorama import Fore, Style
except ImportError:
    class Fore:
        RED = ""
    class Style:
        RESET_ALL = ""

def process_video_file(filename: str, output_path: str) -> bool:
    """
    Process video file by applying standardization filters for consistent output.
    
    Applies comprehensive video and audio standardization:
    - Video: 1920x1080, 30fps, aspect ratio preservation, letterbox/pillarbox as needed
    - Audio: 48kHz stereo, EBU R128 loudness normalization (-16 LUFS)
    - Duration: Cropped to 15 seconds maximum
    
    Args:
        filename: Path to the video file to process
        output_path: Path where the processed video will be saved
        
    Returns:
        True if processing succeeded, False if it failed
        
    Note:
        Output video will have: 1920x1080, 30fps, H.264 High profile, yuv420p, AAC audio
    """
    from ..ffmpeg_utils import get_video_filter, get_audio_filter, build_base_ffmpeg_cmd, run_ffmpeg_with_error_handling
    
    try:
        # Apply comprehensive standardization using centralized functions
        cmd = [
            'ffmpeg', '-y', '-i', filename,
            '-vf', get_video_filter(),
            '-af', get_audio_filter()
        ] + build_base_ffmpeg_cmd(output_path)[2:]  # Skip 'ffmpeg -y' from base
        
        return run_ffmpeg_with_error_handling(cmd, f"video file {Path(filename).name}", output_path, filename, 'VIDEO')
        
    except Exception as e:
        print(f"{Fore.RED}  ✗ FAILED: Unexpected error processing video file {Path(filename).name}: {e}{Style.RESET_ALL}")
        return False