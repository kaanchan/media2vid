#!/usr/bin/env python3
"""
Universal video montage creation script that automatically processes mixed media files 
into a single concatenated video with standardized formatting.

VERSION: v29b - CODEC NORMALIZATION FIX
CHANGES:
- ADDED: normalize_codec_name() function to handle FFmpeg command vs metadata codec name mismatches
- FIXED: Video and audio codec validation now uses normalized names (libx264->h264, h264_nvenc->h264, etc.)
- IMPROVED: Cache validation more reliable with proper codec name mapping

VERSION: v29 - CACHE SYSTEM AND TIMED CLEANUP
CHANGES:
- ADDED: use_cache flag (defaults True) for intelligent temp file caching
- ADDED: get_cache_info() function to generate parameter signatures for cache validation
- ADDED: is_cached_file_valid() function for cache comparison and modification time checking
- MODIFIED: run_ffmpeg_with_error_handling() now checks cache before processing
- MODIFIED: Main processing loop integrates cache validation to skip regeneration when appropriate
- ADDED: 5-second timed cleanup prompt with default to preserve temp files
- IMPROVED: Cache system compares key FFmpeg parameters and source file modification times
- FIXED: Human-readable JSON cache files with ffprobe validation of actual file properties
- FIXED: Dynamic resolution extraction and float duration parsing
- IMPROVED: Comprehensive validation of resolution, codecs, pixel format, sample rate, and duration

VERSION: v28 - PURE FUNCTION EXTRACTION
CHANGES:
- EXTRACTED: Helper functions for better modularity without changing program flow
- ADDED: extract_person_name() function from inline lambda
- ADDED: generate_output_filename() for timestamp generation
- ADDED: get_media_extensions() for centralized extension management
- ADDED: is_temp_file() for file filtering logic
- ADDED: categorize_media_files() for file categorization
- IMPROVED: Type hints and docstrings for parse_range(), get_stream_info(), print_stream_info()
- FIXED: Added missing FFmpeg execution for intro file processing

VERSION: v27 - DRAWTEXT QUOTE FIX
CHANGES:
- FIXED: Removed double quotes from drawtext filter to prevent literal quote display
- NOTE: filelist.txt already correctly placed in temp_ folder

VERSION: v26 - ENHANCED AUDIO BACKGROUNDS
CHANGES:
- NEW: Enhanced audio background search - same filename.png, audio_background.png, title screen, then black
- FIXED: Proper colon escaping in drawtext filter (double backslash)
- UPDATED: Font size increased to 36pt for better readability
- NEW: Case-insensitive PNG matching for audio backgrounds
- NEW: Fallback cascade with warnings for failed background images

VERSION: v25 - FIXED AUDIO FILTER
CHANGES: 
- Merged complete processing loop from v16 into v23 base
- Preserved improved error handling from v23
- Added colorspace consistency settings from v16
- Restored working INTRO/VIDEO/AUDIO processing logic
- FIXED: Replaced channelmap with aformat for robust mono/stereo handling

VERSION: v24 - WORKING MERGED
CHANGES: 
- Merged complete processing loop from v16 into v23 base
- Preserved improved error handling from v23
- Added colorspace consistency settings from v16
- Restored working INTRO/VIDEO/AUDIO processing logic
- FIXED: Replaced channelmap with aformat for robust mono/stereo handling


DESCRIPTION:
    This Python script performs comprehensive video montage creation with the following features:
    
    FILE DETECTION & SORTING:
    - Auto-detects all video and audio files in the current directory
    - Supports 12 video formats (.mp4, .mov, .avi, .mkv, .wmv, .flv, .webm, .m4v, .3gp, .ts, .mts, .vob)
    - Supports 9 audio formats (.mp3, .m4a, .wav, .flac, .aac, .ogg, .wma, .opus, .mp2)
    - Intelligently excludes temp files, previous merged outputs, and system files
    - Sorts files alphabetically by person name (text after " - " in filename)
    - Processes title screen, then videos, then audio files
    
    TITLE SCREEN SUPPORT:
    - Automatically detects PNG files for use as 3-second intro slides
    - Looks for title.png but failing to find will search for first PNG file
    - Converts PNG to video with silent audio track matching other files
    - Scales and formats intro to match processing standards
    
    VIDEO PROCESSING:
    - Standardizes all content to 1920x1080 @ 30fps with proper aspect ratio preservation
    - Applies letterboxing/pillarboxing as needed to maintain original aspect ratios
    - Crops all content to exactly 15 seconds for consistent segment length
    - Normalizes video to H.264 High profile with yuv420p pixel format
    
    AUDIO PROCESSING:
    - Converts all audio to 48kHz stereo with EBU R128 loudness normalization (-16 LUFS)
    - Handles mono to stereo conversion and multi-channel downmixing
    - Creates waveform visualizations for audio-only files (cyan, no text overlay)
    - Ensures consistent audio bitrate (~128kbps AAC) across all segments
    
    CACHING SYSTEM:
    - Intelligent temp file caching compares FFmpeg parameters and source modification times
    - Skips regeneration when cached files are valid and newer than source
    - Controlled by use_cache flag (defaults to True)
    
    USER INTERACTION:
    - Displays comprehensive file categorization and processing order
    - Shows ignored files with reasons for exclusion
    - Provides 20-second countdown with interactive pause/continue/cancel options
    - Range processing (R) and selective merging (M) options
    - Includes progress tracking for each file processed
    - Timed cleanup prompt (5 seconds) with default to preserve temp files
    
    OUTPUT & CLEANUP:
    - Creates timestamped output files (DirectoryName-MERGED-yyyymmdd_hhmmss.mp4)
    - Uses optimized concatenation with stream copy when possible
    - Offers optional cleanup of temporary files after successful completion
    - Preserves temp files for debugging if processing fails

REQUIREMENTS:
    - FFmpeg must be installed and available in PATH
    - Python 3.6 or later
    - colorama package for colored output (pip install colorama)
    - Sufficient disk space for temporary files (roughly 2x the size of source content)
    
FILENAME CONVENTION:
    - Files should follow "Description - PersonName.extension" format for proper sorting
    - Files without this format will be sorted alphabetically by full filename
    
PROCESSING STANDARDS:
    - All video: 1920x1080, 30fps, H.264 High profile, yuv420p, ~15 seconds
    - All audio: 48kHz stereo, AAC, ~128kbps, EBU R128 normalized to -16 LUFS
    - Intro slides: 3 seconds duration with silent audio track
    
OUTPUT QUALITY:
    - Video: CRF 23 (high quality), medium preset for balanced speed/quality
    - Audio: 128kbps AAC for consistent quality across segments

LINKS:
    FFmpeg documentation: https://ffmpeg.org/documentation.html
    EBU R128 standard: https://en.wikipedia.org/wiki/EBU_R_128
"""

import os
import sys
import re
import subprocess
import threading
import time
import shutil
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Set

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

# =============================================================================
# CONFIGURATION FLAGS
# =============================================================================

# Cache system control - when True, validates existing temp files before regenerating
use_cache = True

# =============================================================================
# HELPER FUNCTIONS - EXTRACTED FOR MODULARITY (v28)
# =============================================================================

def extract_person_name(filename: str) -> str:
    """
    Extract person name from filename for sorting.
    
    Looks for pattern " - PersonName.extension" and extracts the PersonName portion.
    If pattern not found, returns the full filename in lowercase.
    
    Args:
        filename: The filename to extract person name from
        
    Returns:
        The extracted person name in lowercase, or full filename if pattern not found
        
    Examples:
        >>> extract_person_name("Interview - John Doe.mp4")
        'john doe'
        >>> extract_person_name("random_video.mp4")
        'random_video.mp4'
    """
    match = re.search(r' - (.+)\.[^.]+$', filename)
    return match.group(1).lower() if match else filename.lower()

def generate_output_filename() -> str:
    """
    Generate timestamped output filename based on current directory name.
    
    Creates filename in format: DirectoryName-MERGED-YYYYMMDD_HHMMSS.mp4
    Sanitizes directory name to remove invalid filename characters.
    Limits directory name to 35 characters to prevent overly long filenames.
    
    Returns:
        The generated output filename string
        
    Example:
        >>> # If current directory is "My Videos" at 2024-03-15 14:30:45
        >>> generate_output_filename()
        'My Videos-MERGED-20240315_143045.mp4'
    """
    current_dir = Path.cwd().name
    sanitized_dir_name = re.sub(r'[<>:"/\\|?*]', '_', current_dir)
    output_base_name = sanitized_dir_name[:35]  # First 35 characters
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{output_base_name}-MERGED-{timestamp}.mp4"

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

def is_temp_file(file_path: Path) -> bool:
    """
    Check if a file should be excluded from processing.
    
    Excludes:
    - Temporary files (temp_*.mp4)
    - Previous merged outputs (*-MERGED-*.mp4)
    - Hidden files (starting with . or ~)
    - System files (filelist.txt)
    - Script files (.py, .ps1)
    
    Args:
        file_path: Path object to check
        
    Returns:
        True if file should be excluded, False otherwise
    """
    if not file_path.is_file():
        return True
        
    # Check for temp files
    if re.match(r'^temp_\d+\.mp4$', file_path.name):
        return True
        
    # Check for previous merged outputs
    if re.search(r'-MERGED-.*\.mp4$', file_path.name):
        return True
        
    # Check for hidden/system files
    if file_path.name.startswith('.') or file_path.name.startswith('~'):
        return True
        
    # Check for specific files to exclude
    if file_path.name == 'filelist.txt':
        return True
        
    # Check for script files
    if file_path.suffix.lower() in {'.py', '.ps1'}:
        return True
        
    return False

def categorize_media_files(all_files: List[Path]) -> Dict[str, List[str]]:
    """
    Categorize files into video, audio, intro (PNG), and ignored files.
    
    Args:
        all_files: List of Path objects to categorize
        
    Returns:
        Dictionary with keys 'video', 'audio', 'intro', 'ignored' 
        containing lists of filenames (not Path objects)
        
    Note:
        - PNG files are categorized as 'intro' files
        - Files are sorted by person name within video and audio categories
        - Extension matching is case-insensitive
    """
    video_extensions, audio_extensions = get_media_extensions()
    
    video_files = []
    audio_files = []
    intro_files = []
    ignored_files = []
    
    for file_path in all_files:
        extension = file_path.suffix.lower()
        
        if extension == '.png':
            intro_files.append(file_path.name)
        elif extension in video_extensions:
            video_files.append(file_path.name)
        elif extension in audio_extensions:
            audio_files.append(file_path.name)
        else:
            ignored_files.append(file_path.name)
    
    # Sort video and audio files by person name
    video_files.sort(key=extract_person_name)
    audio_files.sort(key=extract_person_name)
    
    return {
        'video': video_files,
        'audio': audio_files,
        'intro': intro_files,
        'ignored': ignored_files
    }

# =============================================================================
# CACHE SYSTEM FUNCTIONS (v29)
# =============================================================================

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
    if not use_cache:
        return
        
    cache_info_file = temp_file_path.with_suffix('.cache')
    try:
        with cache_info_file.open('w') as f:
            json.dump(cache_info, f, indent=2)
    except (OSError, IOError):
        pass  # Cache info saving is not critical

# =============================================================================
# FFMPEG COMMAND BUILDER - CENTRALIZED STANDARDIZATION
# =============================================================================

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
        file_type: Type of file being processed ('INTRO', 'VIDEO', 'AUDIO')
    """
    temp_file_path = Path(output_path)
    
    # Check cache validity first
    if use_cache:
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
        
        # Save cache info for future validation
        if use_cache:
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
        if use_cache:
            cache_info_file = temp_file_path.with_suffix('.cache')
            if cache_info_file.exists():
                cache_info_file.unlink()
            
        return False

def parse_range(range_str: str, max_files: int) -> List[int]:
    """
    Parse range string like '1-5' or '3' into list of indices.
    
    Args:
        range_str: String containing range (e.g., '1-5') or single number
        max_files: Maximum valid file index
        
    Returns:
        List of indices within valid range, or empty list if invalid input
        
    Examples:
        >>> parse_range('1-5', 10)
        [1, 2, 3, 4, 5]
        >>> parse_range('3', 10)
        [3]
        >>> parse_range('', 5)
        [1, 2, 3, 4, 5]
    """
    range_str = range_str.strip()
    
    if not range_str:
        return list(range(1, max_files + 1))
    
    if '-' in range_str:
        parts = range_str.split('-', 1)
        try:
            start = int(parts[0].strip())
            end = int(parts[1].strip())
            
            # Swap if backwards
            if start > end:
                start, end = end, start
                
            # Clamp to valid range
            start = max(1, start)
            end = min(max_files, end)
            
            return list(range(start, end + 1))
        except ValueError:
            print(f"{Fore.RED}Invalid range format. Use format like '1-5' or single number.{Style.RESET_ALL}")
            return []
    else:
        try:
            num = int(range_str)
            num = max(1, min(max_files, num))
            return [num]
        except ValueError:
            print(f"{Fore.RED}Invalid number format.{Style.RESET_ALL}")
            return []

def find_audio_background(filename: str, title_screen_path: Optional[Path] = None) -> Tuple[Optional[Path], str]:
    """
    Find appropriate background image for audio file following the hierarchy:
    1. Same filename with .png extension (case-insensitive)
    2. audio_background.png
    3. Title screen image (if available)
    4. None (will use black background)
    
    Returns: (Path or None, description string)
    """
    # 1. Check for same-name PNG (case-insensitive)
    base_name = Path(filename).stem  # Get filename without extension
    
    # Search for case-insensitive match
    for file in Path('.').iterdir():
        if file.is_file() and file.suffix.lower() == '.png':
            if file.stem.lower() == base_name.lower():
                print(f"{Fore.WHITE}  -> Found matching PNG: {file.name}{Style.RESET_ALL}")
                return (file, f"same-name PNG ({file.name})")
    
    # 2. Check for audio_background.png
    audio_bg_path = Path('audio_background.png')
    if audio_bg_path.exists():
        print(f"{Fore.WHITE}  -> Found audio_background.png{Style.RESET_ALL}")
        return (audio_bg_path, "audio_background.png")
    
    # 3. Use title screen if available
    if title_screen_path and title_screen_path.exists():
        print(f"{Fore.WHITE}  -> Using title screen image: {title_screen_path.name}{Style.RESET_ALL}")
        return (title_screen_path, f"title screen ({title_screen_path.name})")
    
    # 4. No image found - will use black background
    print(f"{Fore.WHITE}  -> No background image found, using black background{Style.RESET_ALL}")
    return (None, "black background")

def get_user_input_with_timeout_cleanup():
    """Handle cleanup prompt with 5-second timeout defaulting to preserve files."""
    print(f"{Fore.YELLOW}Delete temp directory and files? (y/N - defaults to N in 5 seconds): {Style.RESET_ALL}", end="", flush=True)
    
    # Use threading for non-blocking input with timeout
    input_result = [None]
    
    def get_input():
        try:
            input_result[0] = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            input_result[0] = "n"
    
    # Start input thread
    input_thread = threading.Thread(target=get_input, daemon=True)
    input_thread.start()
    
    # Wait up to 5 seconds for input
    start_time = time.time()
    while time.time() - start_time < 5.0:
        if input_result[0] is not None:
            break
        time.sleep(0.1)
    
    # Get result or default to 'n'
    response = input_result[0] if input_result[0] is not None else "n"
    
    if input_result[0] is None:
        print("n (timed out)")
    
    return response in ['y', 'yes']

# =============================================================================
# INITIALIZATION AND OUTPUT FILENAME GENERATION
# =============================================================================

print(f"{Fore.GREEN}=== Starting Video Processing ==={Style.RESET_ALL}")

# Show cache status
if use_cache:
    print(f"{Fore.CYAN}Cache system: ENABLED - will reuse valid temp files{Style.RESET_ALL}")
else:
    print(f"{Fore.YELLOW}Cache system: DISABLED - will regenerate all temp files{Style.RESET_ALL}")

# Generate timestamped output filename to avoid conflicts with previous runs
final_output_file = generate_output_filename()

print(f"{Fore.YELLOW}Output file will be: {final_output_file}{Style.RESET_ALL}")

# =============================================================================
# FILE LISTS - AUTO-DETECTED AND SORTED WITH COMPREHENSIVE FILTERING
# =============================================================================

print(f"{Fore.YELLOW}Auto-detecting and sorting media files...{Style.RESET_ALL}")

# Get all files in current directory, excluding temp files and system files
all_files = []
for file_path in Path('.').iterdir():
    if not is_temp_file(file_path):
        all_files.append(file_path)

# Categorize files
media_files = categorize_media_files(all_files)
video_files = media_files['video']
audio_files = media_files['audio']
intro_files = media_files['intro']
ignored_files = media_files['ignored']

# Cache title screen path for later use in audio processing
title_screen_path = None
if intro_files:
    title_screen_path = Path(intro_files[0])  # Store the first PNG as title screen

# Create processing order list with proper numbering
processing_order = []
current_index = 1

# Add intro files first
if intro_files:
    for intro_file in intro_files[:1]:  # Only use first PNG found
        processing_order.append((current_index, intro_file, 'INTRO'))
        current_index += 1

# Add video files
for video_file in video_files:
    processing_order.append((current_index, video_file, 'VIDEO'))
    current_index += 1

# Add audio files
for audio_file in audio_files:
    processing_order.append((current_index, audio_file, 'AUDIO'))
    current_index += 1

# Display results
print()
print(f"{Fore.GREEN}=== PROCESSING ORDER ==={Style.RESET_ALL}")

if intro_files:
    print(f"{Fore.MAGENTA}TITLE SCREEN FILES ({len(intro_files)} files, using first):{Style.RESET_ALL}")
    for i, (index, filename, file_type) in enumerate([item for item in processing_order if item[2] == 'INTRO']):
        print(f"  {index}. {filename}")
    print()

if video_files:
    print(f"{Fore.CYAN}VIDEO FILES ({len(video_files)} files):{Style.RESET_ALL}")
    for i, (index, filename, file_type) in enumerate([item for item in processing_order if item[2] == 'VIDEO']):
        print(f"  {index}. {filename}")
else:
    print(f"{Fore.YELLOW}VIDEO FILES: None found{Style.RESET_ALL}")

print()

if audio_files:
    print(f"{Fore.MAGENTA}AUDIO FILES ({len(audio_files)} files):{Style.RESET_ALL}")
    for i, (index, filename, file_type) in enumerate([item for item in processing_order if item[2] == 'AUDIO']):
        print(f"  {index}. {filename}")
else:
    print(f"{Fore.YELLOW}AUDIO FILES: None found{Style.RESET_ALL}")

print()

if ignored_files:
    print(f"{Fore.WHITE}IGNORED FILES ({len(ignored_files)} files):{Style.RESET_ALL}")
    for filename in sorted(ignored_files):
        print(f"  {filename} (unknown media format)")
else:
    print(f"{Fore.GREEN}IGNORED FILES: None{Style.RESET_ALL}")

print()

# Validation
total_media_files = len(processing_order)
if total_media_files == 0:
    print(f"{Fore.RED}ERROR: No supported media files found!{Style.RESET_ALL}")
    video_extensions, audio_extensions = get_media_extensions()
    print(f"{Fore.YELLOW}Supported video: {', '.join(sorted(video_extensions))}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Supported audio: {', '.join(sorted(audio_extensions))}{Style.RESET_ALL}")
    sys.exit(1)

# =============================================================================
# USER CONFIRMATION WITH TIMEOUT AND PROPER PAUSE FUNCTIONALITY
# =============================================================================

print(f"{Fore.YELLOW}=== CONFIRMATION ==={Style.RESET_ALL}")
print(f"Ready to process {total_media_files} media files.")
print()
print(f"{Fore.WHITE}Options:{Style.RESET_ALL}")
print(f"{Fore.GREEN}  <Y> or <Enter> - Continue with processing all files{Style.RESET_ALL}")
print(f"{Fore.YELLOW}  <P> - Pause countdown (requires Y/Enter to resume){Style.RESET_ALL}")
print(f"{Fore.CYAN}  <R> - Process specific range of files only{Style.RESET_ALL}")
print(f"{Fore.MAGENTA}  <M> - Merge existing temp files (with optional range){Style.RESET_ALL}")
print(f"{Fore.RED}  <N> - Cancel and exit{Style.RESET_ALL}")
print()

def get_user_input_with_timeout():
    """Handle user input with timeout and pause functionality."""
    timeout_seconds = 20
    paused = False
    start_time = time.time()
    
    # Use threading for non-blocking input
    input_result = [None]
    input_thread = None
    
    def get_input():
        try:
            input_result[0] = input().strip().upper()
        except (EOFError, KeyboardInterrupt):
            input_result[0] = "N"
    
    # Main countdown loop with proper pause handling
    while not paused:
        elapsed = time.time() - start_time
        remaining = max(0, timeout_seconds - int(elapsed))
        
        if remaining == 0:
            break
            
        print(f"\r{Fore.CYAN}Auto-continuing in {remaining} seconds... (Press P to pause, Y/Enter to continue, R for range, M for merge, N to cancel): {Style.RESET_ALL}", 
              end="", flush=True)
        
        # Start input thread if not already running
        if input_thread is None or not input_thread.is_alive():
            input_thread = threading.Thread(target=get_input, daemon=True)
            input_thread.start()
        
        # Check for input
        time.sleep(0.1)
        if input_result[0] is not None:
            response = input_result[0]
            if response in ['Y', '']:
                print(f"\n{Fore.GREEN}Continuing immediately...{Style.RESET_ALL}")
                return 'Y', None
            elif response == 'P':
                paused = True
                print(f"\n{Fore.YELLOW}Countdown PAUSED. Press Y/Enter to continue, R for range, M for merge, or N to cancel.{Style.RESET_ALL}")
                break
            elif response == 'R':
                print(f"\n{Fore.CYAN}Range processing selected.{Style.RESET_ALL}")
                return 'R', None
            elif response == 'M':
                print(f"\n{Fore.MAGENTA}Merge mode selected.{Style.RESET_ALL}")
                return 'M', None
            elif response == 'N':
                print(f"\n{Fore.RED}Cancelled by user.{Style.RESET_ALL}")
                sys.exit(0)
    
    # Handle paused state - wait indefinitely until user input
    while paused:
        print(f"{Fore.YELLOW}PAUSED - Press Y/Enter to continue, R for range, M for merge, or N to cancel: {Style.RESET_ALL}", 
              end="", flush=True)
        
        # Reset input for paused state
        input_result[0] = None
        input_thread = threading.Thread(target=get_input, daemon=True)
        input_thread.start()
        
        # Wait for input
        while input_result[0] is None:
            time.sleep(0.1)
        
        response = input_result[0]
        if response in ['Y', '']:
            print(f"\n{Fore.GREEN}Resuming processing...{Style.RESET_ALL}")
            paused = False
            return 'Y', None
        elif response == 'R':
            print(f"\n{Fore.CYAN}Range processing selected.{Style.RESET_ALL}")
            return 'R', None
        elif response == 'M':
            print(f"\n{Fore.MAGENTA}Merge mode selected.{Style.RESET_ALL}")
            return 'M', None
        elif response == 'N':
            print(f"\n{Fore.RED}Cancelled by user.{Style.RESET_ALL}")
            sys.exit(0)
        else:
            print(f"\n{Fore.RED}Invalid key. Press Y/Enter to continue, R for range, M for merge, or N to cancel.{Style.RESET_ALL}")
    
    # Auto-continue message if countdown completed without pause
    if not paused:
        print(f"\n{Fore.GREEN}Auto-continuing after timeout...{Style.RESET_ALL}")
    
    return 'Y', None

# Run the confirmation
action, _ = get_user_input_with_timeout()

# Handle range processing
selected_indices = None
if action == 'R':
    print(f"{Fore.CYAN}Enter range to process (e.g., '1-5' or '3' or Enter for all): {Style.RESET_ALL}", end="")
    range_input = input().strip()
    selected_indices = parse_range(range_input, total_media_files)
    
    if not selected_indices:
        sys.exit(1)
        
    print(f"{Fore.GREEN}Will process files: {', '.join(map(str, selected_indices))}{Style.RESET_ALL}")
    processing_order = [item for item in processing_order if item[0] in selected_indices]

elif action == 'M':
    print(f"{Fore.MAGENTA}Enter range to merge (e.g., '1-5' or '3' or Enter for all): {Style.RESET_ALL}", end="")
    range_input = input().strip()
    selected_indices = parse_range(range_input, total_media_files)
    
    if not selected_indices:
        sys.exit(1)
    
    print(f"{Fore.GREEN}Will merge files: {', '.join(map(str, selected_indices))}{Style.RESET_ALL}")

print(f"{Fore.GREEN}Starting processing...{Style.RESET_ALL}")

# =============================================================================
# TEMPORARY FILE DIRECTORY SETUP
# =============================================================================

# Create dedicated temp directory for organized file management
temp_dir = Path("temp_")
if temp_dir.exists():
    print(f"{Fore.WHITE}Using existing temp directory: {temp_dir}{Style.RESET_ALL}")
else:
    temp_dir.mkdir()
    print(f"{Fore.WHITE}Created temp directory: {temp_dir}{Style.RESET_ALL}")

# =============================================================================
# HANDLE MERGE MODE
# =============================================================================

if action == 'M':
    # Check which temp files exist and which need to be created
    temp_files = []
    files_to_create = []
    
    # Get the original processing order for all files
    all_processing_order = []
    current_index = 1
    
    if intro_files:
        for intro_file in intro_files[:1]:
            all_processing_order.append((current_index, intro_file, 'INTRO'))
            current_index += 1
    
    for video_file in video_files:
        all_processing_order.append((current_index, video_file, 'VIDEO'))
        current_index += 1
    
    for audio_file in audio_files:
        all_processing_order.append((current_index, audio_file, 'AUDIO'))
        current_index += 1
    
    for index, filename, file_type in all_processing_order:
        if index in selected_indices:
            temp_file_path = temp_dir / f"temp_{index-1}.mp4"
            temp_files.append(str(temp_file_path))
            
            if not temp_file_path.exists():
                files_to_create.append((index, filename, file_type))
    
    if files_to_create:
        print(f"{Fore.YELLOW}Need to create {len(files_to_create)} missing temp files first...{Style.RESET_ALL}")
        processing_order = files_to_create
    else:
        print(f"{Fore.GREEN}All temp files exist, proceeding to merge...{Style.RESET_ALL}")
        processing_order = []  # Skip processing, go straight to merge

# =============================================================================
# MAIN MEDIA PROCESSING LOOP - STANDARDIZATION TO COMMON FORMAT
# =============================================================================

if processing_order:  # Only process if there are files to process
    total_files = len(processing_order)
    print(f"{Fore.YELLOW}Processing {total_files} files...{Style.RESET_ALL}")
    
    # Process each file with format standardization for seamless concatenation
    for i, (index, filename, file_type) in enumerate(processing_order):
        # Use original index for temp file naming
        safe_name = temp_dir / f"temp_{index-1}.mp4"
        
        if file_type == 'INTRO':
            print(f"{Fore.CYAN}[{i + 1}/{total_files}] Processing title screen image: {filename}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}  -> Creating 3-second intro with silent audio track...{Style.RESET_ALL}")
            
            # Convert PNG to 3-second video using the same standardized settings as all other media
            cmd = [
                'ffmpeg', '-y',
                '-loop', '1', '-i', str(filename),  # Loop the image
                '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000',  # Silent audio
                '-vf', get_video_filter(),  # Standard video scaling/padding
                '-shortest'  # End when shortest stream (3 seconds) ends
            ] + build_base_ffmpeg_cmd(safe_name, duration=3)[2:]  # Skip 'ffmpeg -y' from base
            
            # Execute the FFmpeg command for intro processing
            if not run_ffmpeg_with_error_handling(cmd, f"intro file {filename}", str(safe_name), filename, file_type):
                print(f"{Fore.RED}Stopping script - check the error above{Style.RESET_ALL}")
                sys.exit(1)
            
        elif file_type == 'AUDIO':
            print(f"{Fore.CYAN}[{i + 1}/{total_files}] Processing: {filename}{Style.RESET_ALL}")
            
            # Find appropriate background using new search logic
            background_path, bg_description = find_audio_background(filename, title_screen_path)
            
            # Prepare text overlay with proper colon escaping
            text_overlay = f"Audio only submission: {filename}"
            text_overlay_escaped = text_overlay.replace(":", "\\\\:")
            
            if background_path:
                # Try to use the found background image
                cmd = [
                    'ffmpeg', '-y',
                    '-loop', '1', '-i', str(background_path),  # Background image
                    '-i', filename,  # Audio file
                    '-vf', f'scale=1920:1080,drawtext=fontsize=36:fontcolor=white:x=10:y=h-th-10:text={text_overlay_escaped}',
                    '-af', get_audio_filter(),
                    '-shortest'  # End when audio ends
                ] + build_base_ffmpeg_cmd(safe_name)[2:]  # Skip 'ffmpeg -y' from base
                
                # Try the command, fall back if it fails
                if not run_ffmpeg_with_error_handling(cmd, f"audio file {filename} with {bg_description}", str(safe_name), filename, file_type):
                    print(f"{Fore.YELLOW}  WARNING: Failed to use {bg_description}, falling back to black background{Style.RESET_ALL}")
                    
                    # Fallback to black background
                    cmd = [
                        'ffmpeg', '-y',
                        '-f', 'lavfi', '-i', 'color=black:size=1920x1080:rate=30',  # Black background
                        '-i', filename,  # Audio file
                        '-vf', f'drawtext=fontsize=36:fontcolor=white:x=10:y=h-th-10:text={text_overlay_escaped}',
                        '-af', get_audio_filter(),
                        '-shortest'  # End when audio ends
                    ] + build_base_ffmpeg_cmd(safe_name)[2:]  # Skip 'ffmpeg -y' from base
                    
                    if not run_ffmpeg_with_error_handling(cmd, f"audio file {filename} with black background", str(safe_name), filename, file_type):
                        print(f"{Fore.RED}Stopping script - check the error above{Style.RESET_ALL}")
                        sys.exit(1)
                else:
                    # Success with background image, continue to next file
                    continue
            else:
                # No background image found, use black background directly
                cmd = [
                    'ffmpeg', '-y',
                    '-f', 'lavfi', '-i', 'color=black:size=1920x1080:rate=30',  # Black background
                    '-i', filename,  # Audio file
                    '-vf', f'drawtext=fontsize=36:fontcolor=white:x=10:y=h-th-10:text={text_overlay_escaped}',
                    '-af', get_audio_filter(),
                    '-shortest'  # End when audio ends
                ] + build_base_ffmpeg_cmd(safe_name)[2:]  # Skip 'ffmpeg -y' from base
                
                if not run_ffmpeg_with_error_handling(cmd, f"audio file {filename} with black background", str(safe_name), filename, file_type):
                    print(f"{Fore.RED}Stopping script - check the error above{Style.RESET_ALL}")
                    sys.exit(1)
            
        else:  # VIDEO
            print(f"{Fore.CYAN}[{i + 1}/{total_files}] Processing: {filename}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}  -> Processing video file...{Style.RESET_ALL}")
            
            # Apply comprehensive standardization using centralized functions
            cmd = [
                'ffmpeg', '-y', '-i', filename,
                '-vf', get_video_filter(),
                '-af', get_audio_filter()
            ] + build_base_ffmpeg_cmd(safe_name)[2:]  # Skip 'ffmpeg -y' from base
        
            # Process file and exit on failure to prevent corrupted output
            if not run_ffmpeg_with_error_handling(cmd, f"file {filename}", str(safe_name), filename, file_type):
                print(f"{Fore.RED}Stopping script - check the error above{Style.RESET_ALL}")
                sys.exit(1)

# =============================================================================
# FINAL CONCATENATION AND OUTPUT GENERATION
# =============================================================================

print()
print(f"{Fore.GREEN}=== Creating File List ==={Style.RESET_ALL}")

# For merge mode, use the selected indices
if action == 'M':
    # temp_files already built above in merge mode section
    pass
else:
    # Normal mode - build temp_files list from all existing temp files
    temp_files = []
    for index, filename, file_type in processing_order:
        temp_file_path = temp_dir / f"temp_{index-1}.mp4"
        if temp_file_path.exists():
            temp_files.append(str(temp_file_path))

# Generate concatenation input file listing all temp files in order
# Place filelist.txt inside temp directory for better organization
filelist_path = temp_dir / 'filelist.txt'
with filelist_path.open('w', encoding='ascii') as f:
    for temp_file in temp_files:
        # Use relative paths from temp directory
        relative_path = Path(temp_file).name
        f.write(f"file '{relative_path}'\n")

print(f"Created filelist.txt with {len(temp_files)} entries")

print()
print(f"{Fore.GREEN}=== Final Concatenation ==={Style.RESET_ALL}")

# Concatenate all standardized temp files using STREAM COPY (no re-encoding)
# Since all temp files have identical specs, stream copy is safe and much faster
print(f"{Fore.WHITE}  -> Using stream copy for fast concatenation (no re-encoding)...{Style.RESET_ALL}")

cmd = [
    'ffmpeg', '-f', 'concat', '-safe', '0', '-i', str(filelist_path),
    '-c', 'copy',  # Stream copy - no re-encoding needed since all files are standardized
    final_output_file
]

if not run_ffmpeg_with_error_handling(cmd, "final concatenation", final_output_file, str(filelist_path), "CONCAT"):
    print(f"{Fore.RED}Final concatenation failed - falling back to re-encoding...{Style.RESET_ALL}")
    
    # Fallback: Use re-encoding if stream copy fails due to edge cases
    cmd_fallback = [
        'ffmpeg', '-f', 'concat', '-safe', '0', '-i', str(filelist_path),
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
        '-c:a', 'aac', '-b:a', '128k',
        final_output_file
    ]
    
    if not run_ffmpeg_with_error_handling(cmd_fallback, "final concatenation (re-encoding)", final_output_file, str(filelist_path), "CONCAT"):
        print(f"{Fore.RED}Both stream copy and re-encoding failed{Style.RESET_ALL}")
        sys.exit(1)

# =============================================================================
# COMPLETION, CLEANUP, AND USER FEEDBACK
# =============================================================================

# Verify successful output creation and provide cleanup options
if Path(final_output_file).exists():
    print(f"{Fore.GREEN}✓ SUCCESS: Created {final_output_file}{Style.RESET_ALL}")
    
    # Offer optional cleanup with timed prompt
    print()
    should_cleanup = get_user_input_with_timeout_cleanup()
    
    if should_cleanup:
        shutil.rmtree(temp_dir)
        print(f"{Fore.GREEN}Cleanup complete - temp directory and files removed!{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}Temp directory '{temp_dir}' and files preserved.{Style.RESET_ALL}")
else:
    # Preserve temp files for debugging if final output failed
    print(f"{Fore.RED}✗ FAILED: Final video not created{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Temp directory '{temp_dir}' and files preserved for debugging.{Style.RESET_ALL}")

print()
print(f"{Fore.GREEN}=== Process Complete ==={Style.RESET_ALL}")
