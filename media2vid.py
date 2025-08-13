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

    - Includes progress tracking for each file processed

    

    OUTPUT & CLEANUP:

    - Creates timestamped output files (DirectoryName-MERGED-yyyymmdd_hhmmss.mp4)

    - Uses optimized concatenation with re-encoding to eliminate timestamp issues

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

        not re.match(r'-MERGED-.*\.mp4$', file_path.name) and  # Not previous merged output files

        not file_path.name.startswith('.') and not file_path.name.startswith('~') and  # Not hidden/temp system files

        file_path.name != 'filelist.txt' and  # Not our concatenation file

        file_path.suffix.lower() not in {'.py', '.ps1'}):  # Not script files

        all_files.append(file_path)



# Separate files into categories

video_files = []

audio_files = []

ignored_files = []



for file_path in all_files:

    extension = file_path.suffix.lower()

    

    if extension in video_extensions:

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



# Display results

print()

print(f"{Fore.GREEN}=== PROCESSING ORDER ==={Style.RESET_ALL}")



if video_files:

    print(f"{Fore.CYAN}VIDEO FILES ({len(video_files)} files):{Style.RESET_ALL}")

    for i, filename in enumerate(video_files, 1):

        print(f"  {i}. {filename}")

else:

    print(f"{Fore.YELLOW}VIDEO FILES: None found{Style.RESET_ALL}")



print()



if audio_files:

    print(f"{Fore.MAGENTA}AUDIO FILES ({len(audio_files)} files):{Style.RESET_ALL}")

    for i, filename in enumerate(audio_files, len(video_files) + 1):

        print(f"  {i}. {filename}")

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

total_media_files = len(video_files) + len(audio_files)

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

print(f"{Fore.GREEN}  <Y> or <Enter> - Continue with processing{Style.RESET_ALL}")

print(f"{Fore.YELLOW}  <P> - Pause countdown (requires Y/Enter to resume){Style.RESET_ALL}")

print(f"{Fore.RED}  <N> - Cancel and exit{Style.RESET_ALL}")

print()



def get_user_input_with_timeout():

    """Handle user input with timeout and pause functionality."""

    timeout_seconds = 20

    paused = False

    current_time = timeout_seconds

    

    # Use threading for non-blocking input

    input_result = [None]

    input_thread = None

    

    def get_input():

        try:

            input_result[0] = input().strip().upper()

        except (EOFError, KeyboardInterrupt):

            input_result[0] = "N"

    

    # Main countdown loop with proper pause handling

    while current_time > 0 and not paused:

        print(f"\r{Fore.CYAN}Auto-continuing in {current_time} seconds... (Press P to pause, Y/Enter to continue, N to cancel): {Style.RESET_ALL}", 

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

                return True

            elif response == 'P':

                paused = True

                print(f"\n{Fore.YELLOW}Countdown PAUSED. Press Y/Enter to continue or N to cancel.{Style.RESET_ALL}")

                break

            elif response == 'N':

                print(f"\n{Fore.RED}Cancelled by user.{Style.RESET_ALL}")

                sys.exit(0)

        

        # Countdown every 10 iterations (1 second)

        if current_time % 10 == 0:

            current_time -= 1

    

    # Handle paused state - wait indefinitely until user input

    while paused:

        print(f"{Fore.YELLOW}PAUSED - Press Y/Enter to continue or N to cancel: {Style.RESET_ALL}", 

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

        elif response == 'N':

            print(f"\n{Fore.RED}Cancelled by user.{Style.RESET_ALL}")

            sys.exit(0)

        else:

            print(f"\n{Fore.RED}Invalid key. Press Y/Enter to continue or N to cancel.{Style.RESET_ALL}")

    

    # Auto-continue message if countdown completed without pause

    if current_time == 0 and not paused:

        print(f"\n{Fore.GREEN}Auto-continuing after timeout...{Style.RESET_ALL}")

    

    return True



# Run the confirmation

get_user_input_with_timeout()

print(f"{Fore.GREEN}Starting processing...{Style.RESET_ALL}")



# Combine all media files for processing loop

all_files = video_files + audio_files

temp_files = []



# =============================================================================

# TEMPORARY FILE DIRECTORY SETUP

# =============================================================================



# Create dedicated temp directory for organized file management

temp_dir = Path("temp_")

if temp_dir.exists():

    # Remove existing temp directory and contents to ensure clean slate

    shutil.rmtree(temp_dir)

    print(f"{Fore.WHITE}Cleared existing temp directory{Style.RESET_ALL}")



temp_dir.mkdir()

print(f"{Fore.WHITE}Created temp directory: {temp_dir}{Style.RESET_ALL}")



# =============================================================================

# INTRO SLIDE PROCESSING (OPTIONAL PNG TO 3-SECOND VIDEO)

# =============================================================================



# Search for PNG files to use as standardized intro slide

intro_images = list(Path('.').glob('*.png'))

has_intro = False

index_offset = 1  # Start main files at temp_1.mp4 if intro exists



if intro_images:

    intro_image = intro_images[0]

    print(f"{Fore.CYAN}[INTRO] Processing intro slide: {intro_image.name}{Style.RESET_ALL}")

    print(f"{Fore.WHITE}  -> Creating 3-second intro with silent audio track...{Style.RESET_ALL}")

    

    # Convert PNG to 3-second video with specifications matching processed media files:

    # VIDEO: 1920x1080, 30fps, H.264 High profile, yuv420p pixel format, CRF 23

    # AUDIO: Silent stereo track at 48kHz, AAC codec, 128kbps bitrate

    # This ensures perfect compatibility during concatenation with no re-encoding needed

    intro_temp_file = temp_dir / "temp_0.mp4"

    

    cmd = [

        'ffmpeg', '-y', '-loop', '1', '-i', str(intro_image),

        '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000',

        '-t', '3',

        '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30',

        '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',

        '-pix_fmt', 'yuv420p', '-profile:v', 'high',

        '-c:a', 'aac', '-ar', '48000', '-b:a', '128k',

        '-shortest', str(intro_temp_file)

    ]

    

    try:

        subprocess.run(cmd, check=True, capture_output=True)

        temp_files.append(str(intro_temp_file))

        has_intro = True

        print(f"{Fore.GREEN}  ✓ Created intro with silent audio: {intro_temp_file}{Style.RESET_ALL}")

    except subprocess.CalledProcessError as e:

        print(f"{Fore.RED}  ✗ FAILED: intro {intro_temp_file}{Style.RESET_ALL}")

        print(f"{Fore.RED}Stopping script - check the error above{Style.RESET_ALL}")

        sys.exit(1)

else:

    print(f"{Fore.YELLOW}No PNG found - skipping intro{Style.RESET_ALL}")

    index_offset = 0



# =============================================================================

# MAIN MEDIA PROCESSING LOOP - STANDARDIZATION TO COMMON FORMAT

# =============================================================================



total_files = len(all_files)

print(f"{Fore.YELLOW}Processing {total_files} main files...{Style.RESET_ALL}")



# Process each file with format standardization for seamless concatenation

for i, filename in enumerate(all_files):

    # Calculate temp file index (offset by intro if present) and create full path

    index = i + index_offset

    safe_name = temp_dir / f"temp_{index}.mp4"

    temp_files.append(str(safe_name))

    

    print(f"{Fore.CYAN}[{i + 1}/{total_files}] Processing: {filename}{Style.RESET_ALL}")

    

    if filename in audio_files:

        # =========================================================================

        # AUDIO FILE PROCESSING: Convert to Waveform Visualization Video

        # =========================================================================

        

        print(f"{Fore.WHITE}  -> Creating waveform video (no text overlay)...{Style.RESET_ALL}")

        

        # Remove any existing temp file to ensure fresh waveform generation

        if safe_name.exists():

            safe_name.unlink()

        

        # Create standardized waveform visualization:

        # - Resample audio to 48kHz stereo with EBU R128 loudness normalization

        # - Generate cyan waveform at 1920x1080 resolution using 'cline' mode

        # - Split audio stream for both output and visualization

        # - Crop to exactly 15 seconds to match video processing

        filter_complex = '[0:a]aresample=48000,pan=stereo|c0=c0|c1=c1,loudnorm,asplit=2[a][vis];[vis]showwaves=s=1920x1080:mode=cline:colors=cyan:scale=lin[wave]'

        

        cmd = [

            'ffmpeg', '-y', '-i', filename, '-t', '15',

            '-filter_complex', filter_complex,

            '-map', '[wave]', '-map', '[a]',

            '-c:v', 'libx264', '-preset', 'medium',

            '-c:a', 'aac', '-ar', '48000',

            str(safe_name)

        ]

        

    else:

        # =========================================================================

        # VIDEO FILE PROCESSING: Standardize Format and Normalize Audio

        # =========================================================================

        

        print(f"{Fore.WHITE}  -> Processing video file...{Style.RESET_ALL}")

        

        # Apply comprehensive standardization to ensure uniform output:

        # VIDEO: Scale to 1920x1080 with aspect ratio preservation, pad with black bars,

        #        standardize to 30fps, force yuv420p pixel format for compatibility

        # AUDIO: Resample to 48kHz stereo, apply EBU R128 loudness normalization,

        #        convert mono to stereo, handle multi-channel downmixing

        # DURATION: Crop to exactly 15 seconds for consistent segment length

        audio_filter = 'aresample=48000,pan=stereo|c0=c0|c1=c1,loudnorm=I=-16:TP=-1.5:LRA=11'

        

        cmd = [

            'ffmpeg', '-y', '-i', filename, '-t', '15',

            '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30',

            '-af', audio_filter,

            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',

            '-c:a', 'aac', '-ar', '48000', '-b:a', '128k',

            str(safe_name)

        ]

    

    # Verify successful processing and exit on failure to prevent corrupted output

    try:

        subprocess.run(cmd, check=True, capture_output=True)

        print(f"{Fore.GREEN}  ✓ Created: {safe_name}{Style.RESET_ALL}")

    except subprocess.CalledProcessError as e:

        print(f"{Fore.RED}  ✗ FAILED: {safe_name}{Style.RESET_ALL}")

        print(f"{Fore.RED}Stopping script - check the error above{Style.RESET_ALL}")

        sys.exit(1)



# =============================================================================

# FINAL CONCATENATION AND OUTPUT GENERATION

# =============================================================================



print()

print(f"{Fore.GREEN}=== Creating File List ==={Style.RESET_ALL}")



# Generate concatenation input file listing all processed temp files in order

# Use relative paths for filelist.txt to work with ffmpeg concat demuxer

filelist_path = Path('filelist.txt')

with filelist_path.open('w', encoding='ascii') as f:

    for temp_file in temp_files:

        f.write(f"file '{temp_file}'\n")



print(f"Created filelist.txt with {len(temp_files)} entries")



print()

print(f"{Fore.GREEN}=== Final Concatenation ==={Style.RESET_ALL}")



# Concatenate all standardized temp files using re-encoding for perfect compatibility

# Re-encoding eliminates any remaining timestamp inconsistencies and ensures clean output

# Slightly slower than stream copy but guarantees perfect sync and eliminates warnings

cmd = [

    'ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'filelist.txt',

    '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',

    '-c:a', 'aac', '-b:a', '128k',

    final_output_file

]



try:

    subprocess.run(cmd, check=True)

except subprocess.CalledProcessError as e:

    print(f"{Fore.RED}✗ FAILED: Final concatenation failed{Style.RESET_ALL}")

    sys.exit(1)



# =============================================================================

# COMPLETION, CLEANUP, AND USER FEEDBACK

# =============================================================================



# Verify successful output creation and provide cleanup options

if Path(final_output_file).exists():

    print(f"{Fore.GREEN}✓ SUCCESS: Created {final_output_file}{Style.RESET_ALL}")

    

    # Offer optional cleanup of temporary processing files and directory

    print()

    cleanup = input(f"{Fore.YELLOW}Ready to cleanup temp files and directory. Do you want to delete temp directory? (y/n): {Style.RESET_ALL}").strip().lower()

    

    if cleanup in ['y', 'yes']:

        shutil.rmtree(temp_dir)

        filelist_path.unlink()

        print(f"{Fore.GREEN}Cleanup complete - temp directory and filelist removed!{Style.RESET_ALL}")

    else:

        print(f"{Fore.YELLOW}Temp directory '{temp_dir}' and files preserved for inspection.{Style.RESET_ALL}")

else:

    # Preserve temp files for debugging if final output failed

    print(f"{Fore.RED}✗ FAILED: Final video not created{Style.RESET_ALL}")

    print(f"{Fore.YELLOW}Temp directory '{temp_dir}' and files preserved for debugging.{Style.RESET_ALL}")



print()

print(f"{Fore.GREEN}=== Process Complete ==={Style.RESET_ALL}")
