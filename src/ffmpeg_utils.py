"""
FFmpeg command building and execution utilities for media2vid.
"""
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

try:
    from colorama import Fore, Style
except ImportError:
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = WHITE = ""
    class Style:
        RESET_ALL = ""

def build_base_ffmpeg_cmd(output_path: str, duration: int = 15, use_gpu: bool = False) -> List[str]:
    """
    Build the base FFmpeg command with standardized output settings.
    All processed files will have identical specs for seamless concatenation.
    GPU encoding via h264_nvenc is used if use_gpu is True; otherwise, CPU (libx264).
    """
    if use_gpu:
        #video_codec = ['-c:v', 'h264_nvenc', '-preset', 'fast', '-b:v', '4M'] # Always 4Mbps, file may be big
        video_codec = ['-c:v', 'h264_nvenc', '-preset', 'fast', '-rc:v', 'vbr', '-cq:v', '23', '-b:v', '0'] # CQ (constant quality, VBR)

    else:
        video_codec = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '23']

    return [
        'ffmpeg', '-y',
        # VIDEO CODEC AND SPECS
        *video_codec,
        '-pix_fmt', 'yuv420p', '-profile:v', 'high',
        '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
        # AUDIO SPECS
        '-c:a', 'aac', '-ar', '48000', '-b:a', '128k',
        # DURATION
        '-t', str(duration),
        str(output_path)
    ]

def get_video_filter() -> str:
    """Standard video filter for consistent 1920x1080 output with aspect ratio preservation."""
    return 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30'

def get_audio_filter() -> str:
    """
    Standard audio filter with robust channel handling and EBU R128 normalization.
    Handles mono, stereo, and multi-channel inputs gracefully.
    """
    return 'aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.5:LRA=11'

def get_stream_info(file_path: str) -> Dict[str, Optional[Dict[str, str]]]:
    """
    Get basic stream information from a media file.
    
    Args:
        file_path: Path to the media file to analyze
        
    Returns:
        Dictionary with 'video' and 'audio' keys, each containing stream info
        or None if that stream type is not present
        
    Example:
        >>> info = get_stream_info("video.mp4")
        >>> info['video']['resolution']
        '1920x1080'
    """
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', file_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        info = {'video': None, 'audio': None}
        
        for stream in data.get('streams', []):
            if stream['codec_type'] == 'video' and info['video'] is None:
                fps = 'unknown'
                if 'r_frame_rate' in stream and '/' in str(stream['r_frame_rate']):
                    try:
                        num, den = map(int, stream['r_frame_rate'].split('/'))
                        if den != 0:
                            fps = f"{num/den:.1f}"
                    except:
                        pass
                        
                info['video'] = {
                    'codec': stream.get('codec_name', 'unknown'),
                    'resolution': f"{stream.get('width', '?')}x{stream.get('height', '?')}",
                    'fps': fps,
                    'pix_fmt': stream.get('pix_fmt', 'unknown')
                }
            elif stream['codec_type'] == 'audio' and info['audio'] is None:
                info['audio'] = {
                    'codec': stream.get('codec_name', 'unknown'),
                    'sample_rate': stream.get('sample_rate', 'unknown'),
                    'channels': stream.get('channels', 'unknown'),
                    'channel_layout': stream.get('channel_layout', 'unknown')
                }
        
        return info
    except:
        return {'video': None, 'audio': None}

def print_stream_info(file_path: str, prefix: str = "  ") -> None:
    """
    Print formatted stream information for a media file.
    
    Args:
        file_path: Path to the media file
        prefix: String to prefix each output line with (for indentation)
    """
    info = get_stream_info(file_path)
    
    if info['video']:
        v = info['video']
        fps_str = f"{v['fps']}fps" if v['fps'] != 'unknown' else 'unknown fps'
        print(f"{prefix}📹 Video: {v['codec']} {v['resolution']} {fps_str} {v['pix_fmt']}")
    
    if info['audio']:
        a = info['audio']
        channels = f"{a['channels']}ch" if a['channels'] != 'unknown' else 'unknown'
        layout = f"({a['channel_layout']})" if a['channel_layout'] not in ['unknown', 'stereo', '2'] else ''
        print(f"{prefix}🔊 Audio: {a['codec']} {a['sample_rate']}Hz {channels} {layout}")

def run_ffmpeg_with_error_handling(cmd: List[str], description: str, output_path: str, source_file: str, file_type: str) -> bool:
    """
    Execute FFmpeg command with comprehensive error handling, cleanup, and cache validation.
    Returns True on success, False on failure.
    
    Args:
        cmd: FFmpeg command list
        description: Description for logging
        output_path: Path where output will be created
        source_file: Source file path for cache validation
        file_type: Type of file being processed ('INTRO', 'VIDEO', 'AUDIO', 'CONCAT')
    """
    from .config import use_cache
    from .cache_system import get_cache_info, is_cached_file_valid, save_cache_info
    
    temp_file_path = Path(output_path)
    
    # Skip cache for final output files (CONCAT type)
    if use_cache and file_type != 'CONCAT':
        cache_info = get_cache_info(cmd, file_type, source_file)
        
        if is_cached_file_valid(temp_file_path, source_file, cache_info):
            # Show stream info for the cached file
            print_stream_info(output_path)
            return True
        
        # If we reach here, cache is invalid or doesn't exist, so we'll process
        # Clean up any existing cache files
        cache_info_file = temp_file_path.with_suffix('.cache')
        if cache_info_file.exists():
            cache_info_file.unlink()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"{Fore.GREEN}  ✓ Created: {output_path}{Style.RESET_ALL}")
        
        # Save cache info for future validation (skip for final outputs)
        if use_cache and file_type != 'CONCAT':
            save_cache_info(temp_file_path, cache_info)
        
        # Show stream info for the created file
        print_stream_info(output_path)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}  ✗ FAILED: {description}{Style.RESET_ALL}")
        print(f"{Fore.RED}Exit code: {e.returncode}{Style.RESET_ALL}")
        print()
        
        # Show full command for debugging
        print(f"{Fore.YELLOW}Command that failed:{Style.RESET_ALL}")
        print(f"  {' '.join(cmd)}")
        print()
        
        # Show full stderr output - this contains the real error info
        if e.stderr:
            print(f"{Fore.RED}Full error output:{Style.RESET_ALL}")
            # Split into lines and show relevant error lines
            stderr_lines = e.stderr.strip().split('\n')
            
            # Skip the copyright/configuration lines and show the actual errors
            relevant_lines = []
            skip_config = True
            
            for line in stderr_lines:
                # Skip configuration and build info
                if 'configuration:' in line:
                    skip_config = True
                    continue
                elif skip_config and (line.strip() == '' or 'libavutil' in line or 'libavcodec' in line or 'libavformat' in line):
                    skip_config = False
                    continue
                elif not skip_config:
                    relevant_lines.append(line)
            
            # If we found relevant error lines, show them; otherwise show last 10 lines
            if relevant_lines:
                for line in relevant_lines[-15:]:  # Show last 15 relevant lines
                    print(f"  {line}")
            else:
                print(f"  Last 10 lines of error output:")
                for line in stderr_lines[-10:]:
                    print(f"  {line}")
        
        # Show stdout if available (sometimes contains useful info)
        if e.stdout:
            print(f"{Fore.YELLOW}Output:{Style.RESET_ALL}")
            for line in e.stdout.strip().split('\n')[-5:]:  # Last 5 lines
                if line.strip():
                    print(f"  {line}")
        
        print()
        
        # Clean up failed output file and cache
        if Path(output_path).exists():
            Path(output_path).unlink()
        if use_cache and file_type != 'CONCAT':
            cache_info_file = temp_file_path.with_suffix('.cache')
            if cache_info_file.exists():
                cache_info_file.unlink()
            
        return False