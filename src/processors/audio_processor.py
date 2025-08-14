"""
Audio file processing for media2vid.
"""
from pathlib import Path
from typing import Optional

try:
    from colorama import Fore, Style
except ImportError:
    class Fore:
        RED = YELLOW = ""
    class Style:
        RESET_ALL = ""

def process_audio_file(filename: str, output_path: str, title_screen_path: Optional[Path] = None) -> bool:
    """
    Process audio file by creating video with waveform visualization and text overlay.
    
    Searches for appropriate background image following hierarchy:
    1. Same filename with .png extension (case-insensitive)
    2. audio_background.png 
    3. Title screen image (if provided)
    4. Black background
    
    Args:
        filename: Path to the audio file to process
        output_path: Path where the processed video will be saved  
        title_screen_path: Optional path to title screen for background fallback
        
    Returns:
        True if processing succeeded, False if it failed
        
    Note:
        Output video will have: 1920x1080, 30fps, H.264, yuv420p, AAC audio
        Text overlay shows "Audio only submission" at bottom
    """
    from ..file_utils import find_audio_background
    from ..ffmpeg_utils import get_audio_filter, build_base_ffmpeg_cmd, run_ffmpeg_with_error_handling
    
    try:
        # Find appropriate background image
        background_path, bg_description = find_audio_background(Path(filename).name, title_screen_path)
        
        # Prepare text overlay with proper colon escaping (static text only)
        text_overlay = "Audio only submission"
        text_overlay_escaped = text_overlay.replace(":", "\\\\\\\\:")
        
        # Try background image first if available
        if background_path:
            cmd = [
                'ffmpeg', '-y',
                '-loop', '1', '-i', str(background_path),  # Background image
                '-i', filename,  # Audio file
                '-vf', f'scale=1920:1080,drawtext=fontsize=36:fontcolor=white:x=10:y=h-th-10:text={text_overlay_escaped}',
                '-af', get_audio_filter(),
                '-shortest'  # End when audio ends
            ] + build_base_ffmpeg_cmd(output_path)[2:]  # Skip 'ffmpeg -y' from base
            
            # Try with background image, fall back if it fails
            if run_ffmpeg_with_error_handling(cmd, f"audio file {Path(filename).name} with {bg_description}", output_path, filename, 'AUDIO'):
                return True
            
            # Fallback warning
            print(f"{Fore.YELLOW}  WARNING: Failed to use {bg_description}, falling back to black background{Style.RESET_ALL}")
        
        # Use black background (fallback or no background found)
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi', '-i', 'color=black:size=1920x1080:rate=30',  # Black background
            '-i', filename,  # Audio file
            '-vf', f'drawtext=fontsize=36:fontcolor=white:x=10:y=h-th-10:text={text_overlay_escaped}',
            '-af', get_audio_filter(),
            '-shortest'  # End when audio ends
        ] + build_base_ffmpeg_cmd(output_path)[2:]  # Skip 'ffmpeg -y' from base
        
        return run_ffmpeg_with_error_handling(cmd, f"audio file {Path(filename).name} with black background", output_path, filename, 'AUDIO')
        
    except Exception as e:
        print(f"{Fore.RED}  ✗ FAILED: Unexpected error processing audio file {Path(filename).name}: {e}{Style.RESET_ALL}")
        return False