#!/usr/bin/env python3
"""
Universal video montage creation script that automatically processes mixed media files 
into a single concatenated video with standardized formatting.

VERSION: v30b - MAIN FLOW RESTRUCTURING
CHANGES:
- EXTRACTED: discover_media_files() function for file discovery and categorization
- EXTRACTED: create_processing_order() function for numbered processing sequence creation
- EXTRACTED: display_processing_order() function for formatted file list display
- EXTRACTED: get_user_action() function for user interaction with timeout and pause handling
- EXTRACTED: handle_special_operations() function for C and O operations
- EXTRACTED: determine_files_to_process() function for processing list management
- EXTRACTED: create_final_output() function for concatenation and output generation
- ADDED: main() orchestration function with clear program stages
- RESTRUCTURED: Main flow into logical stages for better maintainability and testability
- FIXED: Audio text overlay now shows static "Audio only submission" without filename

VERSION: v30a - CORE PROCESSING FUNCTION EXTRACTION
CHANGES:
- EXTRACTED: process_intro_file() function for PNG to video conversion with silent audio
- EXTRACTED: process_audio_file() function for audio processing with background search and text overlay
- EXTRACTED: process_video_file() function for video standardization with filters
- SIMPLIFIED: Main processing loop now calls extracted functions for better modularity
- IMPROVED: Enhanced error handling and type hints for processing functions
- MAINTAINED: All existing functionality and behavior preserved

VERSION: v29B - OPERATION BEHAVIOR AND ORGANIZATION
CHANGES:
- ADDED: C operation to clear cache (delete temp_ directory and all .cache files)
- ADDED: O operation to organize directory into INPUT/OUTPUT/LOGS folders with overwrite prompts
- ADDED: Directory path detection at startup - checks for existing INPUT/OUTPUT/LOGS directories
- MODIFIED: R and M operations preserve temp directory instead of clearing it
- ADDED: Range indicators in output filenames (Ma_b, Ra_b, M3, R5 for range operations)
- IMPROVED: File detection searches INPUT directory if it exists, with empty directory warning
- ADDED: Overwrite prompts with 3-second timeout defaulting to "No Overwrite"

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
    - Cache clearing (C) and directory organization (O) operations
    - Includes progress tracking for each file processed
    - Timed cleanup prompt (5 seconds) with default to preserve temp files
    
    OUTPUT & CLEANUP:
    - Creates timestamped output files (DirectoryName-MERGED-yyyymmdd_hhmmss.mp4)
    - Range operations append indicators (Ma_b, Ra_b, M3, R5) to filenames
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
# DIRECTORY STRUCTURE DETECTION (v29B)
# =============================================================================

# Check for existing INPUT/OUTPUT/LOGS directories and set path variables
input_dir = Path("INPUT") if Path("INPUT").exists() else Path(".")
output_dir = Path("OUTPUT") if Path("OUTPUT").exists() else Path(".")
logs_dir = Path("LOGS") if Path("LOGS").exists() else Path(".")

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

def generate_output_filename(range_info: Optional[str] = None) -> str:
    """
    Generate timestamped output filename based on current directory name.
    
    Creates filename in format: DirectoryName-MERGED-yyyymmdd_hhmmss.mp4
    Or with range indicators: DirectoryName-Ma_b-yyyymmdd_hhmmss.mp4
    
    Args:
        range_info: Optional range indicator (e.g., 'M1_5', 'R3_7', 'M3', 'R5')
        
    Returns:
        The generated output filename string
        
    Example:
        >>> generate_output_filename('M1_5')
        'My Videos-M1_5-20240315_143045.mp4'
    """
    current_dir = Path.cwd().name
    sanitized_dir_name = re.sub(r'[<>:"/\\|?*]', '_', current_dir)
    output_base_name = sanitized_dir_name[:35]  # First 35 characters
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if range_info:
        return f"{output_base_name}-{range_info}-{timestamp}.mp4"
    else:
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
        
    # Check for range merged outputs
    if re.search(r'-(M|R)\d+(_\d+)?-.*\.mp4$', file_path.name):
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
# NEW OPERATIONS (v29B)
# =============================================================================

def get_overwrite_confirmation(filename: str) -> bool:
    """
    Get overwrite confirmation with 3-second timeout defaulting to No.
    
    Args:
        filename: Name of file that would be overwritten
        
    Returns:
        True if user wants to overwrite, False otherwise
    """
    print(f"{Fore.YELLOW}File exists: {filename} - Overwrite? (y/N - defaults to N in 3 seconds): {Style.RESET_ALL}", 
          end="", flush=True)
    
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
    
    # Wait up to 3 seconds for input
    start_time = time.time()
    while time.time() - start_time < 3.0:
        if input_result[0] is not None:
            break
        time.sleep(0.1)
    
    # Get result or default to 'n'
    response = input_result[0] if input_result[0] is not None else "n"
    
    if input_result[0] is None:
        print("n (timed out)")
    
    return response in ['y', 'yes']

def organize_directory() -> None:
    """
    Organize directory into INPUT/OUTPUT/LOGS folders with overwrite prompts.
    
    Creates directories if they don't exist and moves files:
    - Media files → INPUT/
    - -MERGED-.mp4 files → OUTPUT/
    - *.log files → LOGS/
    """
    print(f"{Fore.CYAN}=== Organizing Directory ==={Style.RESET_ALL}")
    
    current_dir = Path('.')
    video_extensions, audio_extensions = get_media_extensions()
    all_extensions = video_extensions | audio_extensions | {'.png'}
    
    # Create directories if they don't exist
    input_path = Path("INPUT")
    output_path = Path("OUTPUT") 
    logs_path = Path("LOGS")
    
    input_path.mkdir(exist_ok=True)
    output_path.mkdir(exist_ok=True)
    logs_path.mkdir(exist_ok=True)
    
    moved_count = 0
    skipped_count = 0
    
    # First pass: Handle -MERGED- files specifically (bypass is_temp_file check)
    for file_path in current_dir.iterdir():
        if not file_path.is_file():
            continue
            
        # Skip files already in target directories
        if file_path.parent.name in ['INPUT', 'OUTPUT', 'LOGS']:
            continue
            
        # Handle -MERGED- files specifically (including range indicators like -M1_2- and -M3-)
        # Only consider video files to prevent false positives
        if (file_path.suffix.lower() in video_extensions and 
            re.search(r'-(merged|M\d+(_\d+)?)-', file_path.name, re.IGNORECASE)):
            destination = output_path / file_path.name
            
            # Check if destination exists
            if destination.exists():
                if get_overwrite_confirmation(str(destination)):
                    file_path.rename(destination)
                    print(f"{Fore.GREEN}  ✓ Moved: {file_path.name} → {destination.parent.name}/{Style.RESET_ALL}")
                    moved_count += 1
                else:
                    print(f"{Fore.YELLOW}  ⊘ Skipped: {file_path.name} (already exists){Style.RESET_ALL}")
                    skipped_count += 1
            else:
                file_path.rename(destination)
                print(f"{Fore.GREEN}  ✓ Moved: {file_path.name} → {destination.parent.name}/{Style.RESET_ALL}")
                moved_count += 1
    
    # Second pass: Handle other files with normal filtering
    for file_path in current_dir.iterdir():
        if not file_path.is_file():
            continue
            
        # Skip files already in target directories
        if file_path.parent.name in ['INPUT', 'OUTPUT', 'LOGS']:
            continue
            
        # Skip script files and temp files (this excludes -MERGED- files, but we handled them above)
        if is_temp_file(file_path):
            continue
            
        # Skip -MERGED- files (including range indicators) since we handled them in first pass
        if (file_path.suffix.lower() in video_extensions and 
            re.search(r'-(merged|M\d+(_\d+)?)-', file_path.name, re.IGNORECASE)):
            continue
            
        destination = None
        
        # Determine destination for remaining files
        if file_path.suffix.lower() == '.log':
            destination = logs_path / file_path.name
        elif file_path.suffix.lower() in all_extensions:
            destination = input_path / file_path.name
        
        if destination:
            # Check if destination exists
            if destination.exists():
                if get_overwrite_confirmation(str(destination)):
                    file_path.rename(destination)
                    print(f"{Fore.GREEN}  ✓ Moved: {file_path.name} → {destination.parent.name}/{Style.RESET_ALL}")
                    moved_count += 1
                else:
                    print(f"{Fore.YELLOW}  ⊘ Skipped: {file_path.name} (already exists){Style.RESET_ALL}")
                    skipped_count += 1
            else:
                file_path.rename(destination)
                print(f"{Fore.GREEN}  ✓ Moved: {file_path.name} → {destination.parent.name}/{Style.RESET_ALL}")
                moved_count += 1
    
    print(f"{Fore.GREEN}Organization complete: {moved_count} files moved, {skipped_count} skipped{Style.RESET_ALL}")

def clear_cache() -> None:
    """
    Clear cache by deleting temp_ directory and all .cache files.
    """
    print(f"{Fore.CYAN}=== Clearing Cache ==={Style.RESET_ALL}")
    
    removed_count = 0
    
    # Remove temp_ directory
    temp_dir = Path("temp_")
    if temp_dir.exists():
        try:
            shutil.rmtree(temp_dir)
            print(f"{Fore.GREEN}  ✓ Removed temp_ directory{Style.RESET_ALL}")
            removed_count += 1
        except Exception as e:
            print(f"{Fore.RED}  ✗ Failed to remove temp_ directory: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}  ⊘ temp_ directory not found{Style.RESET_ALL}")
    
    # Remove .cache files
    current_dir = Path('.')
    cache_files_removed = 0
    
    for cache_file in current_dir.glob("*.cache"):
        try:
            cache_file.unlink()
            cache_files_removed += 1
        except Exception as e:
            print(f"{Fore.RED}  ✗ Failed to remove {cache_file.name}: {e}{Style.RESET_ALL}")
    
    if cache_files_removed > 0:
        print(f"{Fore.GREEN}  ✓ Removed {cache_files_removed} .cache files{Style.RESET_ALL}")
        removed_count += cache_files_removed
    else:
        print(f"{Fore.YELLOW}  ⊘ No .cache files found{Style.RESET_ALL}")
    
    if removed_count > 0:
        print(f"{Fore.GREEN}Cache cleared: {removed_count} items removed{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}Cache was already clean{Style.RESET_ALL}")

def format_range_indicator(indices: List[int], operation: str) -> str:
    """
    Format range indicator for filename (Ma_b, Ra_b, M3, R5).
    
    Args:
        indices: List of selected indices
        operation: 'M' for merge or 'R' for range
        
    Returns:
        Formatted range indicator string
    """
    if not indices:
        return f"{operation}0"
    elif len(indices) == 1:
        return f"{operation}{indices[0]}"
    else:
        return f"{operation}{min(indices)}_{max(indices)}"

# =============================================================================
# MAIN FLOW FUNCTIONS (v30b)
# =============================================================================

def discover_media_files(search_dir: Path) -> Dict[str, List[str]]:
    """
    Discover and categorize all media files in specified directory.
    
    Searches the directory for supported media files, excludes temp files and system files,
    and categorizes them into video, audio, intro (PNG), and ignored files.
    
    Args:
        search_dir: Directory to search for media files
        
    Returns:
        Dictionary with keys 'video', 'audio', 'intro', 'ignored' containing
        lists of filenames sorted appropriately
        
    Note:
        Video and audio files are sorted by person name (text after " - ").
        Intro files are PNG images used for title screens.
    """
    # Get all files in search directory, excluding temp files and system files
    all_files = []
    for file_path in search_dir.iterdir():
        if not is_temp_file(file_path):
            all_files.append(file_path)
    
    # Categorize files using existing function
    return categorize_media_files(all_files)

def create_processing_order(intro_files: List[str], video_files: List[str], audio_files: List[str]) -> List[Tuple[int, str, str]]:
    """
    Create numbered processing order from categorized media files.
    
    Assigns sequential numbers to files in processing order:
    1. Intro files (PNG) - first intro only
    2. Video files - in sorted order
    3. Audio files - in sorted order
    
    Args:
        intro_files: List of PNG filenames
        video_files: List of video filenames (pre-sorted)
        audio_files: List of audio filenames (pre-sorted)
        
    Returns:
        List of tuples: (index, filename, file_type)
        Example: [(1, 'title.png', 'INTRO'), (2, 'video.mp4', 'VIDEO'), ...]
    """
    processing_order = []
    current_index = 1
    
    # Add intro files first (only use first PNG found)
    if intro_files:
        for intro_file in intro_files[:1]:
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
    
    return processing_order

def display_processing_order(processing_order: List[Tuple[int, str, str]], ignored_files: List[str]) -> None:
    """
    Display the processing order with formatted output and color coding.
    
    Shows categorized file lists with proper formatting:
    - Title screen files (magenta)
    - Video files (cyan) 
    - Audio files (magenta)
    - Ignored files (white)
    
    Args:
        processing_order: List of (index, filename, file_type) tuples
        ignored_files: List of ignored filenames
    """
    print()
    print(f"{Fore.GREEN}=== PROCESSING ORDER ==={Style.RESET_ALL}")
    
    # Extract files by type from processing order
    intro_items = [item for item in processing_order if item[2] == 'INTRO']
    video_items = [item for item in processing_order if item[2] == 'VIDEO']
    audio_items = [item for item in processing_order if item[2] == 'AUDIO']
    
    if intro_items:
        print(f"{Fore.MAGENTA}TITLE SCREEN FILES ({len(intro_items)} files, using first):{Style.RESET_ALL}")
        for index, filename, file_type in intro_items:
            print(f"  {index}. {filename}")
        print()
    
    if video_items:
        print(f"{Fore.CYAN}VIDEO FILES ({len(video_items)} files):{Style.RESET_ALL}")
        for index, filename, file_type in video_items:
            print(f"  {index}. {filename}")
    else:
        print(f"{Fore.YELLOW}VIDEO FILES: None found{Style.RESET_ALL}")
    
    print()
    
    if audio_items:
        print(f"{Fore.MAGENTA}AUDIO FILES ({len(audio_items)} files):{Style.RESET_ALL}")
        for index, filename, file_type in audio_items:
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

def get_user_action() -> Tuple[str, Optional[List[int]]]:
    """
    Handle user confirmation with timeout, pause functionality, and range selection.
    
    Presents options menu and handles user input with 20-second timeout:
    - Y/Enter: Continue with all files
    - P: Pause countdown  
    - R: Re-render specific range
    - M: Merge specific range
    - C: Clear cache
    - O: Organize directory
    - N: Cancel and exit
    
    Returns:
        Tuple of (action, selected_indices)
        - action: 'Y', 'R', 'M', 'C', 'O'
        - selected_indices: None for Y/C/O, List[int] for R/M
        
    Note:
        C and O operations are handled immediately and exit the program.
    """
    print(f"{Fore.YELLOW}=== CONFIRMATION ==={Style.RESET_ALL}")
    print(f"Ready to process media files.")
    print()
    print(f"{Fore.WHITE}Options:{Style.RESET_ALL}")
    print(f"{Fore.GREEN}  <Y> or <Enter> - Continue with processing all files{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}  <P> - Pause countdown (requires Y/Enter to resume){Style.RESET_ALL}")
    print(f"{Fore.CYAN}  <R> - Re-render specific range of files (force recreate temp files){Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}  <M> - Merge existing temp files (with optional range){Style.RESET_ALL}")
    print(f"{Fore.WHITE}  <C> - Clear cache (delete temp_ directory and .cache files){Style.RESET_ALL}")
    print(f"{Fore.WHITE}  <O> - Organize directory (move files to INPUT/OUTPUT/LOGS){Style.RESET_ALL}")
    print(f"{Fore.RED}  <N> - Cancel and exit{Style.RESET_ALL}")
    print()
    
    # Timeout functionality with pause support
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
            
        print(f"\r{Fore.CYAN}Auto-continuing in {remaining} seconds... (Y/Enter/P/R=re-render/M=merge/C/O/N): {Style.RESET_ALL}", 
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
                action = 'Y'
                break
            elif response == 'P':
                paused = True
                print(f"\n{Fore.YELLOW}Countdown PAUSED. Press Y/Enter to continue, R for range, M for merge, C to clear cache, O to organize, or N to cancel.{Style.RESET_ALL}")
                break
            elif response == 'R':
                print(f"\n{Fore.CYAN}Re-render mode selected.{Style.RESET_ALL}")
                action = 'R'
                break
            elif response == 'M':
                print(f"\n{Fore.MAGENTA}Merge mode selected.{Style.RESET_ALL}")
                action = 'M'
                break
            elif response == 'C':
                print(f"\n{Fore.WHITE}Clear cache selected.{Style.RESET_ALL}")
                action = 'C'
                break
            elif response == 'O':
                print(f"\n{Fore.WHITE}Organize directory selected.{Style.RESET_ALL}")
                action = 'O'
                break
            elif response == 'N':
                print(f"\n{Fore.RED}Cancelled by user.{Style.RESET_ALL}")
                sys.exit(0)
    
    # Handle paused state - wait indefinitely until user input
    while paused:
        print(f"{Fore.YELLOW}PAUSED - Options: Y/Enter/R/M/C/O/N: {Style.RESET_ALL}", 
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
            action = 'Y'
            break
        elif response == 'R':
            print(f"\n{Fore.CYAN}Re-render mode selected.{Style.RESET_ALL}")
            action = 'R'
            break
        elif response == 'M':
            print(f"\n{Fore.MAGENTA}Merge mode selected.{Style.RESET_ALL}")
            action = 'M'
            break
        elif response == 'C':
            print(f"\n{Fore.WHITE}Clear cache selected.{Style.RESET_ALL}")
            action = 'C'
            break
        elif response == 'O':
            print(f"\n{Fore.WHITE}Organize directory selected.{Style.RESET_ALL}")
            action = 'O'
            break
        elif response == 'N':
            print(f"\n{Fore.RED}Cancelled by user.{Style.RESET_ALL}")
            sys.exit(0)
        else:
            print(f"\n{Fore.RED}Invalid key. Press Y/Enter to continue, R for range, M for merge, C to clear cache, O to organize, or N to cancel.{Style.RESET_ALL}")
    
    # Auto-continue message if countdown completed without pause
    if not paused and 'action' not in locals():
        print(f"\n{Fore.GREEN}Auto-continuing after timeout...{Style.RESET_ALL}")
        action = 'Y'
    
    # Handle range input for R and M operations
    selected_indices = None
    if action == 'R':
        total_files = 18  # We know this from the display
        print(f"{Fore.CYAN}Enter range to re-render (e.g., '1-5' or '3' or Enter for all): {Style.RESET_ALL}", end="")
        range_input = input().strip()
        selected_indices = parse_range(range_input, total_files)
        
        if not selected_indices:
            print(f"{Fore.RED}Invalid range. Exiting.{Style.RESET_ALL}")
            sys.exit(1)
            
        print(f"{Fore.GREEN}Will re-render file IDs: {', '.join(map(str, selected_indices))}{Style.RESET_ALL}")
    
    elif action == 'M':
        total_files = 18  # We know this from the display
        print(f"{Fore.MAGENTA}Enter range to merge (e.g., '1-5' or '3' or Enter for all): {Style.RESET_ALL}", end="")
        range_input = input().strip()
        selected_indices = parse_range(range_input, total_files)
        
        if not selected_indices:
            print(f"{Fore.RED}Invalid range. Exiting.{Style.RESET_ALL}")
            sys.exit(1)
        
        print(f"{Fore.GREEN}Will merge file IDs: {', '.join(map(str, selected_indices))}{Style.RESET_ALL}")
    
    return action, selected_indices

def handle_special_operations(action: str) -> None:
    """
    Handle special operations (C and O) that don't require media processing.
    
    Args:
        action: 'C' for clear cache, 'O' for organize directory
        
    Note:
        These operations exit the program after completion.
    """
    if action == 'C':
        clear_cache()
    elif action == 'O':
        organize_directory()
    
    sys.exit(0)

def determine_files_to_process(action: str, selected_indices: Optional[List[int]], processing_order: List[Tuple[int, str, str]]) -> Tuple[List[Tuple[int, str, str]], List[str]]:
    """
    Determine which files need processing based on user action.
    
    Args:
        action: User action ('Y', 'R', 'M')
        selected_indices: Selected file indices for R/M operations
        processing_order: Complete processing order list
        
    Returns:
        Tuple of (files_to_process, temp_files_for_merge)
        - files_to_process: List of files that need processing
        - temp_files_for_merge: List of temp file paths for merge operations
    """
    temp_files_for_merge = []
    
    if action == 'M':
        # Handle merge mode - check which temp files exist
        files_to_create = []
        temp_dir = Path("temp_")
        
        for index, filename, file_type in processing_order:
            if index in selected_indices:
                temp_file_path = temp_dir / f"temp_{index-1}.mp4"
                temp_files_for_merge.append(str(temp_file_path))
                
                if not temp_file_path.exists():
                    files_to_create.append((index, filename, file_type))
        
        if files_to_create:
            print(f"{Fore.YELLOW}Need to create {len(files_to_create)} missing temp files first...{Style.RESET_ALL}")
            return files_to_create, temp_files_for_merge
        else:
            print(f"{Fore.GREEN}All temp files exist, proceeding to merge...{Style.RESET_ALL}")
            return [], temp_files_for_merge
    
    elif action == 'R':
        # Handle re-render mode - filter by selected indices
        return [item for item in processing_order if item[0] in selected_indices], temp_files_for_merge
    
    else:
        # Normal processing - all files
        return processing_order, temp_files_for_merge

def create_final_output(files_processed: List[Tuple[int, str, str]], action: str, selected_indices: Optional[List[int]], temp_files_for_merge: List[str] = None) -> bool:
    """
    Create final concatenated output file.
    
    Args:
        files_processed: List of processed files
        action: User action ('Y', 'M')
        selected_indices: Selected indices for range operations
        temp_files_for_merge: Pre-built list of temp files for merge operations
        
    Returns:
        True if output creation succeeded, False otherwise
    """
    print()
    print(f"{Fore.GREEN}=== Creating File List ==={Style.RESET_ALL}")
    
    # Generate range indicator for filename if applicable (M operation only)
    range_indicator = None
    if selected_indices and action == 'M':
        range_indicator = format_range_indicator(selected_indices, action)
    
    # Generate final output filename with range indicator
    final_output_filename = generate_output_filename(range_indicator)
    final_output_path = output_dir / final_output_filename
    
    print(f"{Fore.YELLOW}Final output: {final_output_path}{Style.RESET_ALL}")
    
    # Build temp files list
    temp_dir = Path("temp_")
    if temp_files_for_merge:
        # Use pre-built list from merge operation
        temp_files = temp_files_for_merge
    else:
        # Build from processed files
        temp_files = []
        for index, filename, file_type in files_processed:
            temp_file_path = temp_dir / f"temp_{index-1}.mp4"
            if temp_file_path.exists():
                temp_files.append(str(temp_file_path))
    
    # Generate concatenation input file
    filelist_path = temp_dir / 'filelist.txt'
    with filelist_path.open('w', encoding='ascii') as f:
        for temp_file in temp_files:
            relative_path = Path(temp_file).name
            f.write(f"file '{relative_path}'\n")
    
    print(f"Created filelist.txt with {len(temp_files)} entries")
    
    print()
    print(f"{Fore.GREEN}=== Final Concatenation ==={Style.RESET_ALL}")
    print(f"{Fore.WHITE}  -> Using stream copy for fast concatenation (no re-encoding)...{Style.RESET_ALL}")
    
    # Concatenate using stream copy
    cmd = [
        'ffmpeg', '-f', 'concat', '-safe', '0', '-i', str(filelist_path),
        '-c', 'copy',
        str(final_output_path)
    ]
    
    if not run_ffmpeg_with_error_handling(cmd, "final concatenation", str(final_output_path), str(filelist_path), "CONCAT"):
        print(f"{Fore.RED}Final concatenation failed - falling back to re-encoding...{Style.RESET_ALL}")
        
        # Fallback to re-encoding
        cmd_fallback = [
            'ffmpeg', '-f', 'concat', '-safe', '0', '-i', str(filelist_path),
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            str(final_output_path)
        ]
        
        if not run_ffmpeg_with_error_handling(cmd_fallback, "final concatenation (re-encoding)", str(final_output_path), str(filelist_path), "CONCAT"):
            print(f"{Fore.RED}Both stream copy and re-encoding failed{Style.RESET_ALL}")
            return False
    
    return final_output_path.exists()

def main() -> None:
    """
    Main orchestration function for video processing workflow.
    
    Coordinates the entire video processing pipeline through clear stages:
    1. Setup and initialization
    2. File discovery and categorization  
    3. User interaction and action selection
    4. Media file processing
    5. Final output generation and cleanup
    
    Exits with status code 0 on success, 1 on failure.
    """
    try:
        # =============================================================================
        # STAGE 1: SETUP AND INITIALIZATION
        # =============================================================================
        
        print(f"{Fore.GREEN}=== Starting Video Processing ==={Style.RESET_ALL}")
        
        # Show directory structure status
        print(f"{Fore.CYAN}Directory structure:{Style.RESET_ALL}")
        print(f"  INPUT: {input_dir}")
        print(f"  OUTPUT: {output_dir}") 
        print(f"  LOGS: {logs_dir}")
        
        # Check for empty INPUT directory warning
        if input_dir.name == "INPUT" and input_dir.exists():
            input_files = [f for f in input_dir.iterdir() if not is_temp_file(f)]
            if not input_files:
                print(f"{Fore.YELLOW}WARNING: INPUT directory exists but is empty!{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Use O operation to organize files into INPUT directory.{Style.RESET_ALL}")
        
        # Show cache status
        if use_cache:
            print(f"{Fore.CYAN}Cache system: ENABLED - will reuse valid temp files{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}Cache system: DISABLED - will regenerate all temp files{Style.RESET_ALL}")
        
        # =============================================================================
        # STAGE 2: FILE DISCOVERY AND CATEGORIZATION
        # =============================================================================
        
        print(f"{Fore.YELLOW}Auto-detecting and sorting media files...{Style.RESET_ALL}")
        
        # Discover and categorize media files
        media_files = discover_media_files(input_dir)
        processing_order = create_processing_order(
            media_files['intro'],
            media_files['video'], 
            media_files['audio']
        )
        
        # Display processing order
        display_processing_order(processing_order, media_files['ignored'])
        
        # Validation
        total_media_files = len(processing_order)
        if total_media_files == 0:
            print(f"{Fore.RED}ERROR: No supported media files found!{Style.RESET_ALL}")
            video_extensions, audio_extensions = get_media_extensions()
            print(f"{Fore.YELLOW}Supported video: {', '.join(sorted(video_extensions))}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Supported audio: {', '.join(sorted(audio_extensions))}{Style.RESET_ALL}")
            sys.exit(1)
        
        # Cache title screen path for audio processing
        title_screen_path = None
        if media_files['intro']:
            title_screen_path = input_dir / media_files['intro'][0]
        
        # =============================================================================
        # STAGE 3: USER INTERACTION AND ACTION SELECTION
        # =============================================================================
        
        print(f"Ready to process {total_media_files} media files.")
        action, selected_indices = get_user_action()
        
        # Handle special operations (C and O exit immediately)
        if action in ['C', 'O']:
            handle_special_operations(action)
            return  # Never reached due to sys.exit(0) in handle_special_operations
        
        print(f"{Fore.GREEN}Starting processing...{Style.RESET_ALL}")
        
        # =============================================================================
        # STAGE 4: TEMP DIRECTORY SETUP AND FILE PROCESSING  
        # =============================================================================
        
        # Setup temp directory based on operation type
        temp_dir = Path("temp_")
        
        if action == 'R':
            # R operation: Re-render selected files, forcing cache invalidation
            if temp_dir.exists():
                print(f"{Fore.WHITE}Using existing temp directory for re-rendering: {temp_dir}{Style.RESET_ALL}")
                # Remove cache files for selected indices to force re-rendering
                for index, _, _ in processing_order:
                    if selected_indices and index in selected_indices:
                        temp_file_path = temp_dir / f"temp_{index-1}.mp4"
                        cache_file_path = temp_file_path.with_suffix('.cache')
                        if cache_file_path.exists():
                            cache_file_path.unlink()
                            print(f"{Fore.YELLOW}  -> Removed cache for temp_{index-1}.mp4 (forcing re-render){Style.RESET_ALL}")
            else:
                temp_dir.mkdir()
                print(f"{Fore.WHITE}Created temp directory: {temp_dir}{Style.RESET_ALL}")
        elif action == 'M':
            # M operation: Merge existing temp files, preserve temp directory
            if temp_dir.exists():
                print(f"{Fore.WHITE}Preserving existing temp directory for merge operation: {temp_dir}{Style.RESET_ALL}")
            else:
                temp_dir.mkdir()
                print(f"{Fore.WHITE}Created temp directory: {temp_dir}{Style.RESET_ALL}")
        else:
            # Normal processing
            if temp_dir.exists():
                print(f"{Fore.WHITE}Using existing temp directory: {temp_dir}{Style.RESET_ALL}")
            else:
                temp_dir.mkdir()
                print(f"{Fore.WHITE}Created temp directory: {temp_dir}{Style.RESET_ALL}")
        
        # Determine files to process
        files_to_process, temp_files_for_merge = determine_files_to_process(action, selected_indices, processing_order)
        
        # Process files if needed
        if files_to_process:
            total_files = len(files_to_process)
            print(f"{Fore.YELLOW}Processing {total_files} files...{Style.RESET_ALL}")
            
            # Process each file
            for i, (index, filename, file_type) in enumerate(files_to_process):
                # Use original index for temp file naming
                safe_name = temp_dir / f"temp_{index-1}.mp4"
                full_filename = str(input_dir / filename)
                
                print(f"{Fore.CYAN}[{i + 1}/{total_files}] Processing: {filename}{Style.RESET_ALL}")
                
                # Call appropriate processing function
                success = False
                if file_type == 'INTRO':
                    print(f"{Fore.WHITE}  -> Creating 3-second intro with silent audio track...{Style.RESET_ALL}")
                    success = process_intro_file(full_filename, str(safe_name), title_screen_path)
                elif file_type == 'AUDIO':
                    success = process_audio_file(full_filename, str(safe_name), title_screen_path)
                else:  # VIDEO
                    print(f"{Fore.WHITE}  -> Processing video file...{Style.RESET_ALL}")
                    success = process_video_file(full_filename, str(safe_name))
                
                if not success:
                    print(f"{Fore.RED}Processing failed - exiting{Style.RESET_ALL}")
                    sys.exit(1)
        
        # R operation stops here
        if action == 'R':
            if files_to_process:
                print(f"{Fore.GREEN}✓ Re-rendering complete: {len(files_to_process)} temp files updated{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}✓ Re-rendering complete: Selected temp files were already up to date{Style.RESET_ALL}")
            
            print(f"{Fore.YELLOW}Temp files are ready. Use M operation to merge them into final output.{Style.RESET_ALL}")
            print()
            print(f"{Fore.GREEN}=== Process Complete ==={Style.RESET_ALL}")
            sys.exit(0)  # Use sys.exit(0) instead of return
        
        # =============================================================================
        # STAGE 5: FINAL OUTPUT GENERATION AND CLEANUP
        # =============================================================================
        
        # Create final output
        if create_final_output(files_to_process if files_to_process else processing_order, action, selected_indices, temp_files_for_merge):
            print(f"{Fore.GREEN}✓ SUCCESS: Created final output{Style.RESET_ALL}")
            
            # Offer cleanup
            print()
            should_cleanup = get_user_input_with_timeout_cleanup()
            
            if should_cleanup:
                shutil.rmtree(temp_dir)
                print(f"{Fore.GREEN}Cleanup complete - temp directory and files removed!{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Temp directory '{temp_dir}' and files preserved.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ FAILED: Final video not created{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Temp directory '{temp_dir}' and files preserved for debugging.{Style.RESET_ALL}")
        
        print()
        print(f"{Fore.GREEN}=== Process Complete ==={Style.RESET_ALL}")
        sys.exit(0)  # Explicit exit to prevent any fall-through
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Process interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
        sys.exit(1)

# =============================================================================
# CORE PROCESSING FUNCTIONS (v30a)
# =============================================================================

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
        Text overlay shows "Audio only submission: {filename}" at bottom
    """
    try:
        # Find appropriate background image
        background_path, bg_description = find_audio_background(Path(filename).name, title_screen_path)
        
        # Prepare text overlay with proper colon escaping (static text only)
        text_overlay = "Audio only submission"
        text_overlay_escaped = text_overlay.replace(":", "\\\\:")
        
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
        file_type: Type of file being processed ('INTRO', 'VIDEO', 'AUDIO', 'CONCAT')
    """
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
    search_dir = input_dir  # Use INPUT directory if it exists
    
    # 1. Check for same-name PNG (case-insensitive)
    base_name = Path(filename).stem  # Get filename without extension
    
    # Search for case-insensitive match
    for file in search_dir.iterdir():
        if file.is_file() and file.suffix.lower() == '.png':
            if file.stem.lower() == base_name.lower():
                print(f"{Fore.WHITE}  -> Found matching PNG: {file.name}{Style.RESET_ALL}")
                return (file, f"same-name PNG ({file.name})")
    
    # 2. Check for audio_background.png
    audio_bg_path = search_dir / 'audio_background.png'
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
    
    # Wait up to 5 seconds for input with countdown display
    start_time = time.time()
    last_remaining = 5
    
    while time.time() - start_time < 5.0:
        if input_result[0] is not None:
            break
        
        # Calculate remaining time and update display
        elapsed = time.time() - start_time
        remaining = max(0, 5 - int(elapsed))
        
        # Only update display when remaining time changes
        if remaining != last_remaining:
            # Clear the line and reprint with new countdown
            print(f"\r{Fore.YELLOW}Delete temp directory and files? (y/N - defaults to N in {remaining} seconds): {Style.RESET_ALL}", end="", flush=True)
            last_remaining = remaining
        
        time.sleep(0.1)
    
    # Get result or default to 'n'
    response = input_result[0] if input_result[0] is not None else "n"
    
    if input_result[0] is None:
        print("n (timed out)")
    else:
        print()  # Add newline after user input
    
    return response in ['y', 'yes']

# =============================================================================
# PROGRAM ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()# =============================================================================
# PROGRAM ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()
