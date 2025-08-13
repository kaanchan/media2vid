#!/usr/bin/env python3
"""
Universal video montage creation script that automatically processes mixed media files 
into a single concatenated video with standardized formatting.

DESCRIPTION:
    This Python script performs comprehensive video montage creation with the following features:
    
    FILE DETECTION & SORTING:
    - Auto-detects all video and audio files in the current directory
    - Supports 12 video formats (.mp4, .mov, .avi, .mkv, .wmv, .flv, .webm, .m4v, .3gp, .ts, .mts, .vob)
    - Supports 9 audio formats (.mp3, .m4a, .wav, .flac, .aac, .ogg, .wma, .opus, .mp2)
    - Intelligently excludes temp files, previous merged outputs, and system files
    - Sorts files alphabetically by person name (text after " - " in filename)
    - Processes videos first, then audio files
    
    INTRO SLIDE SUPPORT:
    - Automatically detects PNG files for use as 3-second intro slides
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
    
    USER INTERACTION:
    - Displays comprehensive file categorization and processing order
    - Shows ignored files with reasons for exclusion
    - Provides 20-second countdown with interactive pause/continue/cancel options
    - Range processing (R) and selective merging (M) options
    - Includes progress tracking for each file processed
    
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
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional

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
# FFMPEG COMMAND BUILDER - CENTRALIZED STANDARDIZATION
# =============================================================================

def build_base_ffmpeg_cmd(output_path: str, duration: int = 15) -> List[str]:
    """
    Build the base FFmpeg command with standardized output settings.
    All processed files will have identical specs for seamless concatenation.
    """
    return [
        'ffmpeg', '-y',  # Base command with overwrite
        # OUTPUT VIDEO SPECS: 1920x1080, 30fps, H.264 High profile, yuv420p, CRF 23
        # Force colorspace consistency to prevent concatenation issues
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
        '-pix_fmt', 'yuv420p', '-profile:v', 'high',
        '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
        # OUTPUT AUDIO SPECS: 48kHz stereo, AAC, 128kbps
        '-c:a', 'aac', '-ar', '48000', '-b:a', '128k',
        # DURATION: Crop to specified seconds for consistency
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
    return 'aresample=48000,channelmap=channel_layout=stereo,loudnorm=I=-16:TP=-1.5:LRA=11'

def get_stream_info(file_path: str) -> dict:
    """Get basic stream information from a media file."""
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

def print_stream_info(file_path: str, prefix: str = "  "):
    """Print formatted stream information."""
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

def run_ffmpeg_with_error_handling(cmd: List[str], description: str, output_path: str) -> bool:
    """
    Execute FFmpeg command with comprehensive error handling and cleanup.
    Returns True on success, False on failure.
    """
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"{Fore.GREEN}  ✓ Created: {output_path}{Style.RESET_ALL}")
        
        # Show stream info for the created file
        print_stream_info(output_path)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}  ✗ FAILED: {description}{Style.RESET_ALL}")
        print(f"{Fore.RED}Command: {' '.join(cmd)}{Style.RESET_ALL}")
        if e.stderr:
            print(f"{Fore.RED}Error: {e.stderr[:200]}...{Style.RESET_ALL}")
        
        # Clean up failed output file
        if Path(output_path).exists():
            Path(output_path).unlink()
            
        return False

def parse_range(range_str: str, max_files: int) -> List[int]:
    """Parse range string like '1-5' or '3' into list of indices."""
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

# =============================================================================
# INITIALIZATION AND OUTPUT FILENAME GENERATION
# =============================================================================

print(f"{Fore.GREEN}=== Starting Video Processing ==={Style.RESET_ALL}")

# Generate timestamped output filename to avoid conflicts with previous runs
current_dir = Path.cwd().name
sanitized_dir_name = re.sub(r'[<>:"/\\|?*]', '_', current_dir)
output_base_name = sanitized_dir_name[:35]  # First 35 characters
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
final_output_file = f"{output_base_name}-MERGED-{timestamp}.mp4"

print(f"{Fore.YELLOW}Output file will be: {final_output_file}{Style.RESET_ALL}")

# =============================================================================
# FILE LISTS - AUTO-DETECTED AND SORTED WITH COMPREHENSIVE FILTERING
# =============================================================================

print(f"{Fore.YELLOW}Auto-detecting and sorting media files...{Style.RESET_ALL}")

# Define comprehensive media extensions (case will be handled in matching)
video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.ts', '.mts', '.vob'}
audio_extensions = {'.mp3', '.m4a', '.wav', '.flac', '.aac', '.ogg', '.wma', '.opus', '.mp2'}

# Get all files in current directory, excluding temp files and system files
all_files = []
for file_path in Path('.').iterdir():
    if (file_path.is_file() and 
        not re.match(r'^temp_\d+\.mp4$', file_path.name) and  # Not temp_*.mp4 files
        not re.search(r'-MERGED-.*\.mp4$', file_path.name) and  # Not previous merged output files
        not file_path.name.startswith('.') and not file_path.name.startswith('~') and  # Not hidden/temp system files
        file_path.name != 'filelist.txt' and  # Not our concatenation file
        file_path.suffix.lower() not in {'.py', '.ps1'}):  # Not script files
        all_files.append(file_path)

# Separate files into categories
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

# Sort both media arrays by person name (text after " - "), case-insensitive
def extract_person_name(filename: str) -> str:
    """Extract person name from filename for sorting."""
    match = re.search(r' - (.+)\.[^.]+$', filename)
    return match.group(1).lower() if match else filename.lower()

video_files.sort(key=extract_person_name)
audio_files.sort(key=extract_person_name)

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
    shutil.rmtree(temp_dir)
    print(f"{Fore.WHITE}Cleared existing temp directory{Style.RESET_ALL}")

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
            
        elif file_type == 'AUDIO':
            print(f"{Fore.CYAN}[{i + 1}/{total_files}] Processing: {filename}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}  -> Creating waveform video (no text overlay)...{Style.RESET_ALL}")
            
            # Remove any existing temp file to ensure fresh waveform generation
            if safe_name.exists():
                safe_name.unlink()
            
            # Create standardized waveform visualization with proper audio handling
            filter_complex = f'[0:a]{get_audio_filter()},asplit=2[a][vis];[vis]showwaves=s=1920x1080:mode=cline:colors=cyan:scale=lin[wave]'
            
            cmd = [
                'ffmpeg', '-y', '-i', filename,
                '-filter_complex', filter_complex,
                '-map', '[wave]', '-map', '[a]'
            ] + build_base_ffmpeg_cmd(safe_name)[2:]  # Skip 'ffmpeg -y' from base
            
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
        if not run_ffmpeg_with_error_handling(cmd, f"file {filename}", str(safe_name)):
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

if not run_ffmpeg_with_error_handling(cmd, "final concatenation", final_output_file):
    print(f"{Fore.RED}Final concatenation failed - falling back to re-encoding...{Style.RESET_ALL}")
    
    # Fallback: Use re-encoding if stream copy fails due to edge cases
    cmd_fallback = [
        'ffmpeg', '-f', 'concat', '-safe', '0', '-i', str(filelist_path),
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
        '-c:a', 'aac', '-b:a', '128k',
        final_output_file
    ]
    
    if not run_ffmpeg_with_error_handling(cmd_fallback, "final concatenation (re-encoding)", final_output_file):
        print(f"{Fore.RED}Both stream copy and re-encoding failed{Style.RESET_ALL}")
        sys.exit(1)

# =============================================================================
# COMPLETION, CLEANUP, AND USER FEEDBACK
# =============================================================================

# Verify successful output creation and provide cleanup options
if Path(final_output_file).exists():
    print(f"{Fore.GREEN}✓ SUCCESS: Created {final_output_file}{Style.RESET_ALL}")
    
    # Offer optional cleanup of temporary processing files and directory
    print()
    cleanup_input = input(f"{Fore.YELLOW}Delete temp directory and files? (y/N): {Style.RESET_ALL}").strip().lower()
    
    if cleanup_input in ['y', 'yes']:
        shutil.rmtree(temp_dir)
        print(f"{Fore.GREEN}Cleanup complete - temp directory and files removed!{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}Temp directory '{temp_dir}' and files preserved for inspection.{Style.RESET_ALL}")
else:
    # Preserve temp files for debugging if final output failed
    print(f"{Fore.RED}✗ FAILED: Final video not created{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Temp directory '{temp_dir}' and files preserved for debugging.{Style.RESET_ALL}")

print()
print(f"{Fore.GREEN}=== Process Complete ==={Style.RESET_ALL}")
