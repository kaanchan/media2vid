"""
File management and discovery utilities for media2vid.
"""
import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from .config import get_media_extensions

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

def create_processing_order(intro_files: List[str], video_files: List[str], audio_files: List[str], custom_intro_path: Optional[str] = None) -> List[Tuple[int, str, str]]:
    """
    Create numbered processing order from categorized media files.
    
    Uses smart intro detection logic instead of just using first PNG found.
    
    Assigns sequential numbers to files in processing order:
    1. Intro file (PNG) - smart detection based on multiple PNG logic
    2. Video files - in sorted order
    3. Audio files - in sorted order
    
    Args:
        intro_files: List of PNG filenames (all PNGs found)
        video_files: List of video filenames (pre-sorted)
        audio_files: List of audio filenames (pre-sorted)
        custom_intro_path: Optional path to custom intro image from --intro-pic
        
    Returns:
        List of tuples: (index, filename, file_type)
        Example: [(1, 'intro_pic.png', 'INTRO'), (2, 'video.mp4', 'VIDEO'), ...]
    """
    processing_order = []
    current_index = 1
    
    # Smart intro detection
    intro_image = find_intro_image(intro_files, custom_intro_path)
    if intro_image:
        processing_order.append((current_index, intro_image, 'INTRO'))
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

def find_audio_background(filename: str, custom_bg_path: Optional[str] = None) -> Tuple[Optional[Path], str]:
    """
    Find appropriate background image for audio file following the hierarchy:
    0. Custom background (if specified via --audio-bg-pic)
    1. Same filename with .png extension (case-insensitive)
    2. audio_background.png (case-insensitive)
    3. None (will use black background)
    
    Returns: (Path or None, description string)
    """
    from .config import input_dir
    
    search_dir = input_dir  # Use INPUT directory if it exists
    
    # 0. Check for custom background image first
    if custom_bg_path:
        custom_path = Path(custom_bg_path)
        if custom_path.exists():
            print(f"  -> Using custom background image: {custom_path.name}")
            return (custom_path, f"custom background ({custom_path.name})")
        else:
            print(f"  -> Custom background not found: {custom_bg_path}")
            # Continue with normal search if custom path doesn't exist
    
    # 1. Check for same-name PNG (case-insensitive)
    base_name = Path(filename).stem  # Get filename without extension
    
    # Search for case-insensitive match
    for file in search_dir.iterdir():
        if file.is_file() and file.suffix.lower() == '.png':
            if file.stem.lower() == base_name.lower():
                print(f"  -> Found matching PNG: {file.name}")
                return (file, f"same-name PNG ({file.name})")
    
    # 2. Check for audio_background.png (case-insensitive)
    for file in search_dir.iterdir():
        if file.is_file() and file.suffix.lower() == '.png':
            if file.stem.lower() == 'audio_background':
                print(f"  -> Found generic audio background: {file.name}")
                return (file, f"audio_background ({file.name})")
    
    # 3. No image found - will use black background
    print(f"  -> No background image found, using black background")
    return (None, "black background")

def find_intro_image(all_png_files: List[str], custom_intro_path: Optional[str] = None) -> Optional[str]:
    """
    Find appropriate intro image based on smart detection logic.
    
    Priority order:
    0. Custom intro (if specified via --intro-pic)
    1. Single PNG → use as intro
    2. Multiple PNGs → look for intro_pic.png (case-insensitive)  
    3. Multiple PNGs, no intro_pic.png → no intro screen
    
    Args:
        all_png_files: List of all PNG filenames found
        custom_intro_path: Optional custom intro path from --intro-pic
        
    Returns:
        Filename of intro image to use, or None if no intro should be created
    """
    from .config import input_dir
    
    # 0. Check for custom intro image first
    if custom_intro_path:
        custom_path = Path(custom_intro_path)
        if custom_path.exists():
            print(f"  -> Using custom intro image: {custom_path.name}")
            return custom_path.name
        else:
            print(f"  -> Custom intro not found: {custom_intro_path}, falling back to auto-detection")
            # Continue with normal detection if custom path doesn't exist
    
    # 1. Single PNG → use as intro (existing behavior)
    if len(all_png_files) == 1:
        print(f"  -> Single PNG found, using as intro: {all_png_files[0]}")
        return all_png_files[0]
    
    # 2. Multiple PNGs → look for intro_pic.png (case-insensitive)
    elif len(all_png_files) > 1:
        print(f"  -> Multiple PNGs found ({len(all_png_files)}), searching for intro_pic.png...")
        
        # Search for intro_pic.png (case-insensitive)
        for png_file in all_png_files:
            if Path(png_file).stem.lower() == 'intro_pic':
                print(f"  -> Found intro_pic file: {png_file}")
                return png_file
        
        # No intro_pic.png found
        print(f"  -> No intro_pic.png found among {len(all_png_files)} PNG files, skipping intro screen")
        return None
    
    # 3. No PNG files
    print(f"  -> No PNG files found, no intro screen")
    return None