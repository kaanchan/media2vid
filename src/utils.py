"""
General utility functions for media2vid.
"""
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

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

def format_range_indicator(range_str: str, operation: str, max_files: int) -> str:
    """
    Format range indicator for filename according to comprehensive naming convention.
    
    Naming Convention:
    1. Single: "3" → "M3"
    2. Range: "16-18" → "M16_18"  
    3. Open-ended: "17-" → "M17_N" (where N = max_files)
    4. Comma-separated: "1,3,5" → "M1,3,5"
    5. Mixed: "1,3-5,17-" → "M1,3_5,17_N"
    
    Args:
        range_str: Original range string from user input
        operation: 'M' for merge or 'R' for re-render
        max_files: Maximum file index for resolving open-ended ranges
        
    Returns:
        Formatted range indicator string for filename
    """
    if not range_str or not range_str.strip():
        return f"{operation}0"
    
    # Split by comma and process each part
    parts = [part.strip() for part in range_str.split(',')]
    formatted_parts = []
    
    for part in parts:
        if not part:
            continue
            
        if '-' in part:
            # Handle range (including open-ended)
            range_parts = part.split('-', 1)
            start_str = range_parts[0].strip()
            end_str = range_parts[1].strip()
            
            if not end_str:
                # Open-ended range: "17-" → "17_N"
                formatted_parts.append(f"{start_str}_{max_files}")
            else:
                # Complete range: "16-18" → "16_18"
                formatted_parts.append(f"{start_str}_{end_str}")
        else:
            # Single number: "3" → "3"
            formatted_parts.append(part)
    
    # Join parts with comma and prefix with operation
    range_part = ','.join(formatted_parts)
    return f"{operation}{range_part}"

def parse_range(range_str: str, max_files: int) -> List[int]:
    """
    Parse range string with full support for complex range syntax.
    
    Supported formats:
    - Single: '3' → [3]
    - Range: '1-5' → [1, 2, 3, 4, 5]  
    - Open-ended: '3-' → [3, 4, ..., max_files]
    - Comma-separated: '1,3,5' → [1, 3, 5]
    - Mixed: '1,3-5,8-' → [1, 3, 4, 5, 8, 9, ..., max_files]
    - Empty: '' → [1, 2, ..., max_files] (all files)
    
    Args:
        range_str: String containing range specification
        max_files: Maximum valid file index
        
    Returns:
        List of unique indices within valid range (1 to max_files), sorted
        
    Examples:
        >>> parse_range('1-5', 10)
        [1, 2, 3, 4, 5]
        >>> parse_range('3-', 10)  
        [3, 4, 5, 6, 7, 8, 9, 10]
        >>> parse_range('1,3,5-7', 10)
        [1, 3, 5, 6, 7]
    """
    range_str = range_str.strip()
    
    # Empty string means all files
    if not range_str:
        return list(range(1, max_files + 1))
    
    indices = set()  # Use set to avoid duplicates
    
    # Split by comma for multiple ranges/numbers
    parts = [part.strip() for part in range_str.split(',')]
    
    for part in parts:
        if not part:
            continue
            
        if '-' in part:
            # Handle range (including open-ended)
            range_parts = part.split('-', 1)
            try:
                start_str = range_parts[0].strip()
                end_str = range_parts[1].strip()
                
                start = int(start_str)
                
                # Handle open-ended range (e.g., '3-')
                if not end_str:
                    end = max_files
                else:
                    end = int(end_str)
                
                # Swap if backwards
                if start > end:
                    start, end = end, start
                    
                # Clamp to valid range
                start = max(1, start)
                end = min(max_files, end)
                
                # Add all numbers in range
                for i in range(start, end + 1):
                    indices.add(i)
                    
            except ValueError:
                print(f"Invalid range format: '{part}'. Use format like '1-5' or '3-'.")
                continue
        else:
            # Handle single number
            try:
                num = int(part)
                # Clamp to valid range
                num = max(1, min(max_files, num))
                indices.add(num)
            except ValueError:
                print(f"Invalid number format: '{part}'.")
                continue
    
    # Return sorted list of unique indices
    return sorted(list(indices))

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
            print(f"Need to create {len(files_to_create)} missing temp files first...")
            return files_to_create, temp_files_for_merge
        else:
            print(f"All temp files exist, proceeding to merge...")
            return [], temp_files_for_merge
    
    elif action == 'R':
        # Handle re-render mode - filter by selected indices
        return [item for item in processing_order if item[0] in selected_indices], temp_files_for_merge
    
    else:
        # Normal processing - all files
        return processing_order, temp_files_for_merge

def get_user_input_with_timeout_cleanup():
    """Handle cleanup prompt with 5-second timeout defaulting to preserve files."""
    import threading
    import time
    
    try:
        from colorama import Fore, Style
    except ImportError:
        class Fore:
            YELLOW = ""
        class Style:
            RESET_ALL = ""
    
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