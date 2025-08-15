# media2vid API Reference - Reusable Components

> **Version:** feature/modularize-codebase branch (post-v31)  
> **Last Updated:** August 2025  
> **Commit:** 2f843b9 - Update test suite for enhanced functionality compatibility

## Overview

This document describes the reusable functions and classes available for integration into other Python programs. The modular architecture of media2vid provides several useful components for media processing, file management, and FFmpeg operations.

## Core Modules

### `src.file_utils` - File Discovery and Management

#### `discover_media_files(search_dir: Path) -> Dict[str, List[str]]`

Discovers and categorizes all media files in a directory.

```python
from pathlib import Path
from src.file_utils import discover_media_files

# Discover files in a directory
files = discover_media_files(Path("./media"))
print(files['video'])  # List of video filenames
print(files['audio'])  # List of audio filenames  
print(files['intro'])  # List of PNG filenames
print(files['ignored']) # List of ignored filenames
```

**Returns:** Dictionary with keys `'video'`, `'audio'`, `'intro'`, `'ignored'`

#### `extract_person_name(filename: str) -> str`

Extracts person name from filename for sorting.

```python
from src.file_utils import extract_person_name

# Extract person name from " - PersonName.ext" format
name = extract_person_name("Interview - John Doe.mp4")
print(name)  # "john doe"

# Fallback to full filename if pattern not found
name = extract_person_name("random_video.mp4")  
print(name)  # "random_video.mp4"
```

#### `find_audio_background(filename: str, custom_bg_path: Optional[str] = None) -> Tuple[Optional[Path], str]`

Finds appropriate background image for audio file processing.

```python
from src.file_utils import find_audio_background

# Search for background image with priority hierarchy
bg_path, description = find_audio_background("audio.m4a")
if bg_path:
    print(f"Using: {bg_path} ({description})")
else:
    print("Using black background")

# With custom background
bg_path, desc = find_audio_background("audio.m4a", "/path/to/custom.png")
```

**Search Priority:**
1. Custom background (if specified)
2. Same filename with .png extension
3. `audio_background.png` in same directory
4. Black background (fallback)

#### `find_intro_image(all_png_files: List[str], custom_intro_path: Optional[str] = None) -> Optional[str]`

Smart intro image detection with priority logic.

```python
from src.file_utils import find_intro_image

png_files = ["title.png", "intro_pic.png", "other.png"]

# Auto-detection logic
intro = find_intro_image(png_files)
print(intro)  # "intro_pic.png" (if multiple PNGs, looks for intro_pic.png)

# With custom intro
intro = find_intro_image(png_files, "/path/to/custom_intro.png")
```

**Priority Logic:**
1. Custom intro (if specified)
2. Single PNG → use as intro
3. Multiple PNGs → look for `intro_pic.png`
4. No intro_pic.png found → no intro

### `src.ffmpeg_utils` - FFmpeg Operations

#### `build_base_ffmpeg_cmd(output_path: str, duration: int = 15, use_gpu: bool = False) -> List[str]`

Constructs standardized FFmpeg command with consistent parameters.

```python
from src.ffmpeg_utils import build_base_ffmpeg_cmd

# Basic command for 15-second output
cmd = build_base_ffmpeg_cmd("output.mp4")

# Custom duration
cmd = build_base_ffmpeg_cmd("output.mp4", duration=30)

# GPU acceleration
cmd = build_base_ffmpeg_cmd("output.mp4", use_gpu=True)
```

#### `get_video_filter() -> str` and `get_audio_filter() -> str`

Get standardized filter chains for consistent processing.

```python
from src.ffmpeg_utils import get_video_filter, get_audio_filter

# Standard video filter (1920x1080, 30fps, aspect ratio preservation)
vf = get_video_filter()
print(vf)  # "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30"

# Standard audio filter (48kHz stereo, EBU R128 normalization)
af = get_audio_filter()
print(af)  # "aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.5:LRA=11"
```

#### `get_stream_info(file_path: str) -> Dict[str, Optional[Dict[str, str]]]`

Extract media file information using ffprobe.

```python
from src.ffmpeg_utils import get_stream_info

info = get_stream_info("video.mp4")
print(info['video']['codec'])      # "h264"
print(info['video']['resolution']) # "1920x1080"
print(info['video']['fps'])        # "30.0"
print(info['audio']['codec'])      # "aac"
print(info['audio']['sample_rate']) # "48000"
```

#### `run_ffmpeg_with_error_handling(cmd, description, output_path, source_file, file_type) -> bool`

Execute FFmpeg commands with comprehensive error handling and caching.

```python
from src.ffmpeg_utils import run_ffmpeg_with_error_handling

cmd = ['ffmpeg', '-i', 'input.mp4', '-t', '15', 'output.mp4']
success = run_ffmpeg_with_error_handling(
    cmd=cmd,
    description="Converting video",
    output_path="output.mp4", 
    source_file="input.mp4",
    file_type="VIDEO"
)

if success:
    print("Processing completed successfully")
else:
    print("Processing failed - check logs")
```

### `src.cache_system` - Intelligent Caching

#### `is_cached_file_valid(temp_file: Path, source_file: str, current_cache: Dict) -> bool`

Check if cached file is still valid and can be reused.

```python
from pathlib import Path
from src.cache_system import is_cached_file_valid, get_cache_info

# Check if temp file is valid
cache_info = get_cache_info(ffmpeg_cmd, "VIDEO", "source.mp4")
is_valid = is_cached_file_valid(Path("temp_1.mp4"), "source.mp4", cache_info)

if is_valid:
    print("Using cached file")
else:
    print("Need to regenerate")
```

#### `get_cache_info(cmd: List[str], file_type: str, source_file: str) -> Dict`

Generate cache information for FFmpeg command validation.

```python
from src.cache_system import get_cache_info

cmd = ['ffmpeg', '-i', 'input.mp4', '-c:v', 'libx264', 'output.mp4']
cache_info = get_cache_info(cmd, "VIDEO", "input.mp4")
print(cache_info['expected']['video_codec'])  # "libx264"
print(cache_info['expected']['duration'])     # 15.0
```

### `src.utils` - Utility Functions

#### `parse_range(range_str: str, max_files: int) -> List[int]`

Parse range strings into list of indices.

```python
from src.utils import parse_range

# Various range formats
indices = parse_range("1,3,5", 10)     # [1, 3, 5]
indices = parse_range("1-5", 10)       # [1, 2, 3, 4, 5]
indices = parse_range("3-", 10)        # [3, 4, 5, 6, 7, 8, 9, 10]
indices = parse_range("1,3-5,8-", 10)  # [1, 3, 4, 5, 8, 9, 10]
```

#### `format_range_indicator(range_str: str, operation: str, max_files: int) -> str`

Format range string into output filename indicator.

```python
from src.utils import format_range_indicator

# Generate filename indicators
indicator = format_range_indicator("1-5", "M", 10)    # "M1_5"
indicator = format_range_indicator("1,3,5", "R", 10)  # "R1,3,5"
indicator = format_range_indicator("3-", "M", 10)     # "M3_10"
```

#### `generate_output_filename(range_indicator: Optional[str] = None) -> str`

Generate timestamped output filename.

```python
from src.utils import generate_output_filename

# Basic merged filename
filename = generate_output_filename()
print(filename)  # "DirectoryName-MERGED-20250815_143022.mp4"

# With range indicator
filename = generate_output_filename("M1_5")
print(filename)  # "DirectoryName-M1_5-20250815_143022.mp4"
```

### `src.processors` - Media Processing

#### Video Processor
```python
from src.processors.video_processor import process_video_file

success = process_video_file("input.mp4", "temp_1.mp4")
```

#### Audio Processor  
```python
from src.processors.audio_processor import process_audio_file

success = process_audio_file("input.m4a", "temp_2.mp4", 
                            custom_bg_path="background.png")
```

#### Intro Processor
```python
from src.processors.intro_processor import process_intro_file

success = process_intro_file("intro.png", "temp_0.mp4", duration=3)
```

### `src.config` - Configuration Management

#### `get_media_extensions() -> Tuple[Set[str], Set[str]]`

Get supported file extensions.

```python
from src.config import get_media_extensions

video_ext, audio_ext = get_media_extensions()
print(video_ext)  # {'.mp4', '.mov', '.avi', ...}
print(audio_ext)  # {'.mp3', '.m4a', '.wav', ...}
```

#### Configuration Variables
```python
from src.config import input_dir, output_dir, temp_dir, logs_dir, use_cache

print(input_dir)   # Path to INPUT directory
print(output_dir)  # Path to OUTPUT directory  
print(temp_dir)    # Path to temp_ directory
print(use_cache)   # Boolean cache setting
```

## Integration Examples

### Basic Media Processing Pipeline

```python
from pathlib import Path
from src.file_utils import discover_media_files, create_processing_order
from src.processors.video_processor import process_video_file
from src.processors.audio_processor import process_audio_file

# Discover files
files = discover_media_files(Path("./media"))

# Create processing order
order = create_processing_order(
    files['intro'], files['video'], files['audio']
)

# Process each file
for index, filename, file_type in order:
    output_path = f"temp_{index}.mp4"
    
    if file_type == "VIDEO":
        success = process_video_file(filename, output_path)
    elif file_type == "AUDIO":
        success = process_audio_file(filename, output_path)
    
    if not success:
        print(f"Failed to process {filename}")
```

### Custom Cache Validation

```python
from pathlib import Path
from src.cache_system import is_cached_file_valid, get_cache_info

def process_with_cache(input_file: str, output_file: str, ffmpeg_cmd: List[str]):
    temp_path = Path(output_file)
    cache_info = get_cache_info(ffmpeg_cmd, "VIDEO", input_file)
    
    if is_cached_file_valid(temp_path, input_file, cache_info):
        print(f"Using cached file: {output_file}")
        return True
    
    # Process file...
    print(f"Processing {input_file} -> {output_file}")
    # ... run FFmpeg command ...
    return True
```

### Range Processing Integration

```python
from src.utils import parse_range, format_range_indicator

def process_selected_files(range_str: str, all_files: List[str]):
    indices = parse_range(range_str, len(all_files))
    
    # Process selected files
    selected_files = [all_files[i-1] for i in indices]  # Convert to 0-based
    
    # Generate output filename with range indicator
    range_indicator = format_range_indicator(range_str, "M", len(all_files))
    output_filename = f"output-{range_indicator}.mp4"
    
    return selected_files, output_filename
```

## Error Handling

All functions use custom exception hierarchy from `src.exceptions`:

```python
from src.exceptions import VideoProcessingError, FFmpegError, MediaFileError

try:
    success = process_video_file("input.mp4", "output.mp4")
except FFmpegError as e:
    print(f"FFmpeg error: {e}")
except MediaFileError as e:
    print(f"Media file error: {e}")
except VideoProcessingError as e:
    print(f"General processing error: {e}")
```

## Configuration and Logging

```python
from src.logging_setup import setup_logging
from src.config import use_cache

# Setup logging
logger = setup_logging("normal", enable_console=True, enable_file=True)

# Check configuration
if use_cache:
    logger.info("Caching is enabled")
else:
    logger.info("Caching is disabled")
```

This modular design allows you to reuse specific components in your own projects while maintaining the robust error handling, caching, and processing standards of the media2vid system.