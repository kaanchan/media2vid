"""
Caching system for media2vid.
"""
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List

try:
    from colorama import Fore, Style
except ImportError:
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = WHITE = ""
    class Style:
        RESET_ALL = ""

def normalize_codec_name(codec_name: str) -> str:
    """
    Normalize codec names for comparison between FFmpeg command and metadata.
    
    Handles common mismatches where command codec names differ from metadata names:
    - libx264 (command) -> h264 (metadata)
    - h264_nvenc (command) -> h264 (metadata)
    - libfdk_aac (command) -> aac (metadata)
    
    Args:
        codec_name: Codec name from command or metadata
        
    Returns:
        Normalized codec name for consistent comparison
    """
    codec_map = {
        # Video codecs
        'libx264': 'h264',
        'h264_nvenc': 'h264', 
        'h264_qsv': 'h264',
        'libx265': 'hevc',
        'hevc_nvenc': 'hevc',
        'hevc_qsv': 'hevc',
        
        # Audio codecs  
        'libfdk_aac': 'aac',
        'aac': 'aac',
        'libmp3lame': 'mp3',
        'mp3': 'mp3',
        'libopus': 'opus',
        'opus': 'opus'
    }
    return codec_map.get(codec_name.lower(), codec_name.lower())

def get_cache_info(cmd: List[str], file_type: str, filename: str) -> Dict:
    """
    Generate cache information from FFmpeg command parameters for validation.
    
    Extracts key parameters that affect output quality and format:
    - Video: codec, resolution, fps, pixel format, CRF/bitrate
    - Audio: codec, sample rate, channels, bitrate  
    - Duration and filters
    
    Args:
        cmd: FFmpeg command list
        file_type: Type of file being processed ('INTRO', 'VIDEO', 'AUDIO')
        filename: Source filename for additional context
        
    Returns:
        Dictionary with command, expected parameters, and metadata
    """
    # Extract key parameters that affect output
    expected_params = {}
    
    # Parse command for key parameters
    i = 0
    while i < len(cmd):
        arg = cmd[i]
        
        # Video parameters
        if arg in ['-c:v', '-vcodec']:
            expected_params['video_codec'] = cmd[i + 1] if i + 1 < len(cmd) else ''
        elif arg == '-crf':
            expected_params['crf'] = cmd[i + 1] if i + 1 < len(cmd) else ''
        elif arg == '-b:v':
            expected_params['video_bitrate'] = cmd[i + 1] if i + 1 < len(cmd) else ''
        elif arg == '-pix_fmt':
            expected_params['pixel_format'] = cmd[i + 1] if i + 1 < len(cmd) else ''
        elif arg == '-profile:v':
            expected_params['video_profile'] = cmd[i + 1] if i + 1 < len(cmd) else ''
        elif arg == '-preset':
            expected_params['preset'] = cmd[i + 1] if i + 1 < len(cmd) else ''
        elif arg == '-vf':
            expected_params['video_filter'] = cmd[i + 1] if i + 1 < len(cmd) else ''
            
        # Audio parameters
        elif arg in ['-c:a', '-acodec']:
            expected_params['audio_codec'] = cmd[i + 1] if i + 1 < len(cmd) else ''
        elif arg == '-ar':
            expected_params['sample_rate'] = cmd[i + 1] if i + 1 < len(cmd) else ''
        elif arg == '-b:a':
            expected_params['audio_bitrate'] = cmd[i + 1] if i + 1 < len(cmd) else ''
        elif arg == '-af':
            expected_params['audio_filter'] = cmd[i + 1] if i + 1 < len(cmd) else ''
            
        # Duration
        elif arg == '-t':
            duration_str = cmd[i + 1] if i + 1 < len(cmd) else '15'
            try:
                command_duration = float(duration_str)
            except ValueError:
                command_duration = 15.0
                
            # Get actual source file duration
            try:
                duration_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', filename]
                result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
                format_info = json.loads(result.stdout)
                source_duration = float(format_info['format']['duration'])
                
                # Use minimum of source duration and command duration (for cropping)
                expected_params['duration'] = min(source_duration, command_duration)
            except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, ValueError):
                # If we can't get source duration, fall back to command duration
                expected_params['duration'] = command_duration
            
        i += 1
    
    # Extract resolution from video filter dynamically
    if 'video_filter' in expected_params:
        filter_str = expected_params['video_filter']
        # Look for scale=WIDTHxHEIGHT pattern
        import re
        scale_match = re.search(r'scale=(\d+):(\d+)', filter_str)
        if scale_match:
            width, height = scale_match.groups()
            expected_params['resolution'] = f"{width}x{height}"
    
    return {
        'command': ' '.join(cmd),
        'expected': expected_params,
        'created': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'source_file': filename,
        'file_type': file_type
    }

def is_cached_file_valid(temp_file_path: Path, source_file_path: str, cache_info: Dict) -> bool:
    """
    Check if cached temp file is valid using ffprobe validation.
    
    Validates:
    - Temp file exists and is not empty
    - Temp file is newer than source file (modification time)
    - ffprobe confirms actual file properties match expected parameters
    
    Args:
        temp_file_path: Path to temp file to validate
        source_file_path: Path to source file
        cache_info: Expected cache information dict
        
    Returns:
        True if cached file is valid and can be reused, False otherwise
    """
    from .config import use_cache
    from .ffmpeg_utils import get_stream_info
    
    if not use_cache:
        return False
        
    # Check if temp file exists and has content
    if not temp_file_path.exists() or temp_file_path.stat().st_size == 0:
        return False
    
    # Check modification times - temp file should be newer than source
    try:
        temp_mtime = temp_file_path.stat().st_mtime
        source_mtime = Path(source_file_path).stat().st_mtime
        
        if temp_mtime <= source_mtime:
            print(f"{Fore.YELLOW}  -> Cache invalid: source file is newer{Style.RESET_ALL}")
            return False
    except (OSError, FileNotFoundError):
        return False
    
    # Check cache info file for parameter matching
    cache_info_file = temp_file_path.with_suffix('.cache')
    if not cache_info_file.exists():
        print(f"{Fore.YELLOW}  -> Cache invalid: no parameter signature found{Style.RESET_ALL}")
        return False
    
    try:
        with cache_info_file.open('r') as f:
            stored_cache_info = json.loads(f.read())
            
        # Compare expected parameters
        stored_expected = stored_cache_info.get('expected', {})
        current_expected = cache_info.get('expected', {})
        
        # Check key parameters match
        key_params_to_check = ['video_codec', 'audio_codec', 'resolution', 'duration', 'pixel_format', 'sample_rate']
        for param in key_params_to_check:
            if stored_expected.get(param) != current_expected.get(param):
                print(f"{Fore.YELLOW}  -> Cache invalid: {param} parameter changed{Style.RESET_ALL}")
                return False
        
        # Use ffprobe to validate actual file properties
        actual_info = get_stream_info(str(temp_file_path))
        
        # Validate video properties if expected
        if 'resolution' in current_expected:
            expected_res = current_expected['resolution']
            if actual_info['video']:
                actual_res = actual_info['video']['resolution']
                if actual_res != expected_res:
                    print(f"{Fore.YELLOW}  -> Cache invalid: resolution mismatch (expected {expected_res}, got {actual_res}){Style.RESET_ALL}")
                    return False
            else:
                print(f"{Fore.YELLOW}  -> Cache invalid: expected video stream not found{Style.RESET_ALL}")
                return False
        
        # Validate video codec if expected
        if 'video_codec' in current_expected and actual_info['video']:
            expected_codec = current_expected['video_codec']
            actual_codec = actual_info['video']['codec']
            # Normalize both codec names for comparison
            expected_codec_norm = normalize_codec_name(expected_codec)
            actual_codec_norm = normalize_codec_name(actual_codec)
            if expected_codec_norm != actual_codec_norm:
                print(f"{Fore.YELLOW}  -> Cache invalid: video codec mismatch (expected {expected_codec}->{expected_codec_norm}, got {actual_codec}->{actual_codec_norm}){Style.RESET_ALL}")
                return False
        
        # Validate pixel format if expected
        if 'pixel_format' in current_expected and actual_info['video']:
            expected_pix_fmt = current_expected['pixel_format']
            actual_pix_fmt = actual_info['video']['pix_fmt']
            if expected_pix_fmt != actual_pix_fmt:
                print(f"{Fore.YELLOW}  -> Cache invalid: pixel format mismatch (expected {expected_pix_fmt}, got {actual_pix_fmt}){Style.RESET_ALL}")
                return False
        
        # Validate audio codec if expected
        if 'audio_codec' in current_expected and actual_info['audio']:
            expected_codec = current_expected['audio_codec']
            actual_codec = actual_info['audio']['codec']
            # Normalize both codec names for comparison
            expected_codec_norm = normalize_codec_name(expected_codec)
            actual_codec_norm = normalize_codec_name(actual_codec)
            if expected_codec_norm != actual_codec_norm:
                print(f"{Fore.YELLOW}  -> Cache invalid: audio codec mismatch (expected {expected_codec}->{expected_codec_norm}, got {actual_codec}->{actual_codec_norm}){Style.RESET_ALL}")
                return False
        
        # Validate sample rate if expected
        if 'sample_rate' in current_expected and actual_info['audio']:
            expected_sr = str(current_expected['sample_rate'])
            actual_sr = str(actual_info['audio']['sample_rate'])
            if expected_sr != actual_sr:
                print(f"{Fore.YELLOW}  -> Cache invalid: sample rate mismatch (expected {expected_sr}Hz, got {actual_sr}Hz){Style.RESET_ALL}")
                return False
        
        # Validate duration if expected (with tolerance for encoding variations)
        if 'duration' in current_expected:
            expected_duration = float(current_expected['duration'])
            # Get actual duration using ffprobe
            try:
                duration_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', str(temp_file_path)]
                result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
                format_info = json.loads(result.stdout)
                actual_duration = float(format_info['format']['duration'])
                
                # Allow 0.5 second tolerance for encoding variations
                duration_diff = abs(actual_duration - expected_duration)
                if duration_diff > 0.5:
                    print(f"{Fore.YELLOW}  -> Cache invalid: duration mismatch (expected {expected_duration}s, got {actual_duration}s){Style.RESET_ALL}")
                    return False
            except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, ValueError):
                # If we can't get duration, don't fail validation
                pass
        
        print(f"{Fore.GREEN}  -> Using cached file: {temp_file_path.name} (validated with ffprobe){Style.RESET_ALL}")
        return True
        
    except (OSError, IOError, json.JSONDecodeError, KeyError):
        print(f"{Fore.YELLOW}  -> Cache invalid: could not read or parse cache file{Style.RESET_ALL}")
        return False

def save_cache_info(temp_file_path: Path, cache_info: Dict) -> None:
    """
    Save cache information to JSON file for future validation.
    
    Args:
        temp_file_path: Path to temp file 
        cache_info: Cache information dict to save
    """
    from .config import use_cache
    
    if not use_cache:
        return
        
    cache_info_file = temp_file_path.with_suffix('.cache')
    try:
        with cache_info_file.open('w') as f:
            json.dump(cache_info, f, indent=2)
    except (OSError, IOError):
        pass  # Cache info saving is not critical