#!/usr/bin/env python3
"""
Universal video montage creation script - Modularized Version

This is the main driver script using the modularized src/ directory structure.
Automatically processes mixed media files into a single concatenated video 
with standardized formatting.

VERSION: v31 - MODULARIZED ARCHITECTURE (Complete Feature Set)
CHANGES:
- REFACTORED: Extracted all functionality into focused modules in src/ directory
- CREATED: Professional package structure following industry standards
- MAINTAINED: Complete backward compatibility with original functionality
- IMPROVED: Testability with comprehensive test suite (70/75 tests passing)
- ADDED: Clear separation of concerns across 12 specialized modules
- RESTORED: All sophisticated features from original (timeout, pause, merge modes, etc.)

Architecture:
- src/config.py: Configuration and constants
- src/cli.py: Command line interface  
- src/logging_setup.py: Logging configuration
- src/environment.py: Environment validation
- src/file_utils.py: File discovery and categorization
- src/utils.py: General utility functions
- src/cache_system.py: Intelligent caching system
- src/ffmpeg_utils.py: FFmpeg command building and execution
- src/processors/: Specialized media processors (intro, audio, video)
- src/exceptions.py: Custom exception classes
- tests/: Comprehensive test suite
- README.md: Professional documentation
"""

import sys
import traceback
import subprocess
import threading
import time
import shutil
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import from modularized structure
from src.cli import parse_arguments
from src.logging_setup import setup_logging
from src.environment import validate_environment
from src.file_utils import discover_media_files, categorize_media_files, extract_person_name, is_temp_file
from src.utils import generate_output_filename, format_range_indicator, parse_range
from src.config import input_dir, output_dir, logs_dir, get_media_extensions
from src.exceptions import VideoProcessingError, FFmpegError, EnvironmentError

class UserInterruptError(Exception):
    """User chose to interrupt the process."""
    pass

try:
    from colorama import Fore, Style, init
    init()
except ImportError:
    class Fore:
        RED = GREEN = YELLOW = BLUE = CYAN = MAGENTA = WHITE = ""
    class Style:
        RESET_ALL = DIM = BRIGHT = ""

def create_processing_order(categorized_files):
    """Create numbered processing order from categorized files."""
    processing_order = []
    
    # Add intro files first
    for filename in categorized_files.get('intro', []):
        temp_path = f"temp_/temp_{len(processing_order)}.mp4"
        processing_order.append((len(processing_order) + 1, filename, 'INTRO'))
    
    # Add video files
    for filename in categorized_files.get('video', []):
        temp_path = f"temp_/temp_{len(processing_order)}.mp4"
        processing_order.append((len(processing_order) + 1, filename, 'VIDEO'))
    
    # Add audio files
    for filename in categorized_files.get('audio', []):
        temp_path = f"temp_/temp_{len(processing_order)}.mp4"
        processing_order.append((len(processing_order) + 1, filename, 'AUDIO'))
    
    return processing_order

def display_processing_order(processing_order: List[Tuple[int, str, str]], ignored_files: List[str]) -> None:
    """Display the numbered processing order to the user."""
    print(f"\n{Fore.CYAN}📋 Processing Order:{Style.RESET_ALL}")
    for index, filename, file_type in processing_order:
        person_name = extract_person_name(Path(filename).name)
        
        # Use emoticons instead of text for file types
        if file_type == 'INTRO':
            type_icon = f"{Fore.MAGENTA}🖼️ {Style.RESET_ALL}"
        elif file_type == 'VIDEO':
            type_icon = f"{Fore.BLUE}🎥{Style.RESET_ALL}"
        else:  # AUDIO
            type_icon = f"{Fore.GREEN}🎵{Style.RESET_ALL}"
        
        # Show person name with filename in parentheses
        display_name = f"{person_name} ({Path(filename).name})"
        print(f"{Fore.WHITE}{index:2d}.{Style.RESET_ALL} {type_icon} {display_name}")
    
    if ignored_files:
        print(f"\n{Fore.YELLOW}📝 Ignored Files:{Style.RESET_ALL}")
        for filename in ignored_files:
            print(f"   {Fore.YELLOW}⊘{Style.RESET_ALL} {filename}")
    print()

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
    
    # Default to "n" if timeout
    response = input_result[0] or "n"
    print(f"\n{Fore.CYAN}Response: {response}{Style.RESET_ALL}")
    
    return response.lower() in ['y', 'yes']

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
    
    # First pass: Handle -MERGED- files specifically
    for file_path in current_dir.iterdir():
        if not file_path.is_file():
            continue
            
        # Skip files already in target directories
        if file_path.parent.name in ['INPUT', 'OUTPUT', 'LOGS']:
            continue
            
        # Handle -MERGED- files specifically (including range indicators like -M1_2- and -M3-)
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
    
    # Second pass: Handle regular media files (excluding temp files and merged files)
    for file_path in current_dir.iterdir():
        if not file_path.is_file():
            continue
            
        # Skip files already in target directories
        if file_path.parent.name in ['INPUT', 'OUTPUT', 'LOGS']:
            continue
            
        # Skip temp files and already processed merged files
        if is_temp_file(file_path):
            continue
            
        # Handle media files
        if file_path.suffix.lower() in all_extensions:
            # Don't move merged files again (already handled in first pass)
            if re.search(r'-(merged|M\d+(_\d+)?)-', file_path.name, re.IGNORECASE):
                continue
                
            destination = input_path / file_path.name
            
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
        
        # Handle log files
        elif file_path.suffix.lower() == '.log':
            destination = logs_path / file_path.name
            
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
    
    print(f"\n{Fore.GREEN}Organization complete: {moved_count} files moved, {skipped_count} skipped{Style.RESET_ALL}")

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
    print(f"{Fore.CYAN}=== CONFIRMATION ==={Style.RESET_ALL}")
    print("Ready to process media files.")
    print("")
    print("Options:")
    print(f"{Fore.GREEN}  <Y> or <Enter> - Continue with processing all files{Style.RESET_ALL}")
    print("  <P> - Pause countdown (requires Y/Enter to resume)")
    print(f"{Fore.CYAN}  <R> - Re-render specific range of files (force recreate temp files){Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}  <M> - Merge existing temp files (with optional range){Style.RESET_ALL}")
    print("  <C> - Clear cache (delete temp_ directory and .cache files)")
    print("  <O> - Organize directory (move files to INPUT/OUTPUT/LOGS)")
    print(f"{Fore.RED}  <N/Q/ESC> - Cancel and exit{Style.RESET_ALL}")
    print("")
    
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
            
        print(f"\r{Fore.CYAN}Auto-continuing in {remaining} seconds... ([Y/Enter]/P/R=re-render/M=merge/C/O/[N/Q/Esc]): {Style.RESET_ALL}", 
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
                print(f"\n{Fore.YELLOW}Countdown PAUSED. Press [Y/Enter] to continue, R for range, M for merge, C to clear cache, O to organize, or [N/Q/Esc] to cancel.{Style.RESET_ALL}")
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
            elif response in ['N', 'Q', '\x1b']:
                print(f"\n{Fore.RED}Cancelled by user.{Style.RESET_ALL}")
                raise UserInterruptError("User cancelled")
    
    # Handle paused state - wait indefinitely until user input
    while paused:
        print(f"{Fore.YELLOW}PAUSED - Options: [Y/Enter]/R/M/C/O/[N/Q/Esc]: {Style.RESET_ALL}", end="", flush=True)
        
        # Reset input for paused state
        input_result[0] = None
        input_thread = threading.Thread(target=get_input, daemon=True)
        input_thread.start()
        
        # Wait for input indefinitely when paused
        while input_result[0] is None:
            time.sleep(0.1)
        
        response = input_result[0]
        if response in ['Y', '']:
            print(f"\n{Fore.GREEN}Resuming...{Style.RESET_ALL}")
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
        elif response in ['N', 'Q', '\x1b']:
            print(f"\n{Fore.RED}Cancelled by user.{Style.RESET_ALL}")
            raise UserInterruptError("User cancelled")
        else:
            print(f"\n{Fore.RED}Invalid option: {response}. Please try again.{Style.RESET_ALL}")
    
    # If timeout occurred, default to Y
    if not paused and 'action' not in locals():
        print(f"\n{Fore.GREEN}Timeout - continuing with all files...{Style.RESET_ALL}")
        action = 'Y'
    
    # Handle range selection for R and M operations
    selected_indices = None
    if action in ['R', 'M']:
        while True:
            try:
                range_input = input(f"{Fore.YELLOW}Enter range (e.g., '3', '1-5', '3-', or Enter for all): {Style.RESET_ALL}").strip()
                
                if not range_input:
                    selected_indices = None
                    break
                else:
                    # Use the parse_range function from utils
                    from src.utils import parse_range
                    # We need to get the total number of files to pass to parse_range
                    # This will be handled in the calling function
                    selected_indices = range_input
                    break
                    
            except (EOFError, KeyboardInterrupt):
                raise UserInterruptError("User cancelled during range selection")
    
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
    
    raise SystemExit(0)  # Use proper exception instead of sys.exit

def determine_files_to_process(action: str, selected_indices: Optional[str], processing_order: List[Tuple[int, str, str]]) -> Tuple[List[Tuple[int, str, str]], List[str]]:
    """
    Determine which files need processing based on user action.
    
    Args:
        action: User action ('Y', 'R', 'M')
        selected_indices: Selected range string for R/M operations
        processing_order: Complete processing order list
        
    Returns:
        Tuple of (files_to_process, temp_files_for_merge)
        - files_to_process: List of files that need processing
        - temp_files_for_merge: List of temp file paths for merge operations
    """
    temp_files_for_merge = []
    total_files = len(processing_order)
    
    # Parse range if provided
    if selected_indices:
        indices = parse_range(selected_indices, total_files)
    else:
        indices = list(range(1, total_files + 1))
    
    if action == 'M':
        # Handle merge mode - check which temp files exist
        files_to_create = []
        temp_dir = Path("temp_")
        
        for index, filename, file_type in processing_order:
            if index in indices:
                temp_file_path = temp_dir / f"temp_{index-1}.mp4"
                temp_files_for_merge.append(str(temp_file_path))
                
                if not temp_file_path.exists():
                    files_to_create.append((index, filename, file_type))
        
        if files_to_create:
            print(f"{Fore.YELLOW}Need to create {len(files_to_create)} missing temp files first...{Style.RESET_ALL}")
            return files_to_create, temp_files_for_merge
        else:
            print(f"{Fore.GREEN}All required temp files exist - proceeding with merge...{Style.RESET_ALL}")
            return [], temp_files_for_merge
    
    elif action in ['Y', 'R']:
        # Handle normal processing or re-render mode
        files_to_process = []
        for index, filename, file_type in processing_order:
            if index in indices:
                files_to_process.append((index, filename, file_type))
        
        return files_to_process, temp_files_for_merge
    
    return [], temp_files_for_merge

def create_final_output(files_processed: List[Tuple[int, str, str]], action: str, selected_indices: Optional[str], temp_files_for_merge: List[str] = None) -> bool:
    """Create the final concatenated output video."""
    if not files_processed and not temp_files_for_merge:
        return False
    
    # Create filelist for concatenation
    temp_dir = Path("temp_")
    temp_dir.mkdir(exist_ok=True)
    
    filelist_path = temp_dir / "filelist.txt"
    
    with open(filelist_path, 'w') as f:
        if temp_files_for_merge and action == 'M':
            # Use provided temp files for merge
            for temp_path in temp_files_for_merge:
                if Path(temp_path).exists():
                    f.write(f"file '{temp_path}'\n")
        else:
            # Use processed files
            for index, _, _ in files_processed:
                temp_path = f"temp_/temp_{index-1}.mp4"
                if Path(temp_path).exists():
                    f.write(f"file '{temp_path}'\n")
    
    # Generate output filename with range indicator
    if selected_indices and action in ['R', 'M']:
        from src.utils import parse_range
        indices = parse_range(selected_indices, len(files_processed)) if selected_indices else []
        range_indicator = format_range_indicator(indices, action)
    else:
        range_indicator = ""
    
    output_filename = generate_output_filename(range_indicator)
    # Use configured output directory instead of hardcoded "OUTPUT"
    from src.config import output_dir as configured_output_dir
    configured_output_dir.mkdir(exist_ok=True)
    output_path = configured_output_dir / output_filename
    
    # Build concatenation command
    from src.ffmpeg_utils import run_ffmpeg_with_error_handling
    
    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', str(filelist_path),
        '-c', 'copy',
        str(output_path)
    ]
    
    print(f"\n{Fore.MAGENTA}🎞️  Creating final output: {output_filename}{Style.RESET_ALL}")
    
    return run_ffmpeg_with_error_handling(
        cmd, 
        f"final concatenation to {output_filename}",
        str(output_path),
        str(filelist_path),
        'CONCAT'
    )

def main() -> int:
    """
    Main orchestration function for video processing workflow using modularized architecture.
    
    Returns:
        0 on success, 1 on failure (proper exit codes)
    """
    try:
        # Parse arguments and setup logging
        args = parse_arguments()
        
        # Setup logging based on command line arguments
        console_output = not args.no_console
        file_output = not args.no_file
        logger = setup_logging(args.log_level, console_output, file_output)
        
        logger.info("=== Starting Video Processing ===", extra={'color': 'green'})
        
        # Environment validation
        try:
            validate_environment(logger)
        except EnvironmentError as e:
            logger.error(f"Environment validation failed: {e}")
            return 1
        
        # File discovery  
        logger.info("Auto-detecting and sorting media files...")
        categorized_files = discover_media_files(input_dir)
        
        # Show directory structure status
        logger.info("Directory structure:")
        logger.info(f"  INPUT: {input_dir}")
        logger.info(f"  OUTPUT: {output_dir}")
        logger.info(f"  LOGS: {logs_dir}")
        
        # Check for empty INPUT directory warning
        if input_dir.name == "INPUT" and input_dir.exists():
            input_files = [f for f in input_dir.iterdir() if not is_temp_file(f)]
            if not input_files:
                logger.warning("INPUT directory exists but is empty!")
                logger.warning("Use O operation to organize files into INPUT directory.")
        
        # Check if we have any files
        total_files_count = sum(len(files) for files in categorized_files.values() if files)
        if total_files_count == 0:
            logger.warning("No valid media files found for processing")
            return 0
        
        # Create processing order
        processing_order = create_processing_order(categorized_files)
        total_files = len(processing_order)
        logger.info(f"Found {total_files} media files for processing")
        
        # Display order and get user action
        ignored_files = categorized_files.get('ignored', [])
        display_processing_order(processing_order, ignored_files)
        
        while True:
            action, selected_indices = get_user_action()
            
            # Handle special operations
            if action in ['C', 'O']:
                handle_special_operations(action)
                # This will exit via SystemExit, but just in case:
                continue
            
            # Determine files to process
            files_to_process, temp_files_for_merge = determine_files_to_process(action, selected_indices, processing_order)
            
            if not files_to_process and not temp_files_for_merge:
                logger.warning("No files selected for processing")
                continue
            else:
                break
        
        # Process files if needed
        if files_to_process:
            logger.info(f"🎯 Processing {len(files_to_process)} selected files...")
            
            # Import processing functions
            from src.processors.intro_processor import process_intro_file
            from src.processors.audio_processor import process_audio_file  
            from src.processors.video_processor import process_video_file
            
            # Ensure temp directory exists
            Path("temp_").mkdir(exist_ok=True)
            
            failed_files = []
            
            for index, filename, file_type in files_to_process:
                logger.info(f"[{index}/{total_files}] Processing {file_type}: {Path(filename).name}")
                
                # CRITICAL FIX: Construct full path using input directory
                full_filename = str(input_dir / filename)
                temp_path = f"temp_/temp_{index-1}.mp4"
                success = False
                
                if file_type == 'INTRO':
                    success = process_intro_file(full_filename, temp_path)
                elif file_type == 'AUDIO':
                    success = process_audio_file(full_filename, temp_path)
                elif file_type == 'VIDEO':
                    success = process_video_file(full_filename, temp_path)
                
                if not success:
                    logger.error(f"Failed to process {file_type} file: {Path(filename).name}")
                    failed_files.append(filename)
            
            if failed_files:
                logger.warning(f"⚠️  {len(failed_files)} files failed processing")
        else:
            logger.info("🎯 Using existing temp files for merge...")
        
        # Create final output
        success = create_final_output(files_to_process, action, selected_indices, temp_files_for_merge)
        
        if success:
            logger.info("✅ Video montage creation completed successfully!")
            return 0
        else:
            logger.error("❌ Failed to create final merged video")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Process interrupted by user")
        return 1
    except UserInterruptError as e:
        print(f"\n🛑 {e}")
        return 1
    except SystemExit as e:
        # Handle special operations that exit cleanly
        return e.code if e.code is not None else 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)