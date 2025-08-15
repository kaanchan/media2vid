# media2vid_orig.py - Complete Feature Analysis

> **Version Reference:** v30c original script analysis  
> **For Comparison With:** feature/modularize-codebase branch (post-v31)  
> **Last Updated:** August 2025

## Overview
This document provides a comprehensive analysis of the original `media2vid_orig.py` script (v30c), documenting all features, functionality, user interfaces, and processing behaviors to ensure compatibility with the modularized version.

## Version History & Evolution
- **v30c**: Enhanced error handling & logging (current version analyzed)
- **v30b**: Main flow restructuring  
- **v30a**: Core processing function extraction
- **v29B**: Operation behavior and organization
- **v29**: Cache system and timed cleanup
- **v28**: Pure function extraction

## Architecture Overview

### Core Processing Pipeline
1. **Environment Validation**: FFmpeg availability, permissions, directory structure
2. **File Discovery**: Scans INPUT directory for supported media files
3. **User Interaction**: Presents options with timeout and pause functionality
4. **Media Processing**: Type-specific processing with FFmpeg
5. **Final Merge**: Concatenates processed files into timestamped output
6. **Cleanup**: Manages temporary files with user confirmation

### Directory Structure
- `INPUT/`: Source media files (optional organized structure)
- `OUTPUT/`: Final merged video outputs with timestamps  
- `LOGS/`: Processing logs with timestamps
- `temp_/`: Temporary processed files and cache data
- `ARCHIVED/`: Previous processing attempts and backups (via O operation)

## Command Line Interface

### Arguments
- `--log-level`: `silent|quiet|normal|verbose` (default: normal)
- `--no-console`: Disable console output, log to file only
- `--no-file`: Disable file logging, console output only

### Legacy Support
- `--quiet`: Equivalent to `--log-level quiet`
- `--verbose`: Equivalent to `--log-level verbose`  
- `--silent`: Equivalent to `--log-level silent`

### Usage Examples
```bash
python media2vid_orig.py                    # Normal operation with colored output
python media2vid_orig.py --quiet            # Show only warnings and errors  
python media2vid_orig.py --verbose          # Show all debug information
python media2vid_orig.py --silent           # Minimal output, log to file only
```

## File Detection & Processing

### Supported File Types
**Video Extensions (12 formats):**
`.mp4, .mov, .avi, .mkv, .wmv, .flv, .webm, .m4v, .3gp, .ts, .mts, .vob`

**Audio Extensions (9 formats):**
`.mp3, .m4a, .wav, .flac, .aac, .ogg, .wma, .opus, .mp2`

**Image Extensions:**
`.png` (for title screens/intro slides)

### File Categorization
1. **Intro Files**: PNG files (prioritizes `title.png`, then first PNG found)
2. **Video Files**: All supported video formats
3. **Audio Files**: All supported audio formats
4. **Ignored Files**: 
   - Temp files (`temp_*`, `filelist.txt`)
   - Previous outputs (contains 'MERGED')
   - System files
   - Unsupported formats

### File Sorting Logic
- **By Person Name**: Extracts person name from " - PersonName.extension" format
- **Alphabetical**: Falls back to full filename if pattern not found
- **Processing Order**: Intro → Videos → Audio (each group sorted internally)

## User Interface & Operations

### Main Menu Options
- **Y/Enter**: Continue with processing all files
- **P**: Pause countdown (requires Y/Enter to resume)
- **R**: Re-render specific range of files (force recreate temp files)
- **M**: Merge existing temp files (with optional range)
- **C**: Clear cache (delete temp_ directory and .cache files)
- **O**: Organize directory (move files to INPUT/OUTPUT/LOGS structure)
- **N/Q/ESC**: Cancel and exit (Note: ESC removed in modularized version - N/Q sufficient)

### Timeout Behavior
- **Auto-continue**: 20-second countdown with visual timer
- **Pause Support**: P key pauses countdown indefinitely
- **Threading**: Non-blocking input using daemon threads
- **Keyboard Interrupt Handling**: Graceful cancellation support

### Range Selection (R/M Operations)
- **Syntax**: Comma-separated indices or ranges (e.g., "1,3,5-7")
- **Validation**: Checks bounds against discovered files
- **Range Indicators**: Output filenames include range info (Ma_b, Ra_b, M3, R5)

## Processing Specifications

### Video Standardization
- **Resolution**: 1920x1080 (letterbox/pillarbox for aspect ratio preservation)
- **Frame Rate**: 30fps
- **Duration**: 15 seconds (cropped if longer)
- **Video Codec**: H.264 High profile
- **Pixel Format**: yuv420p
- **Quality**: CRF 23 (high quality), medium preset

### Audio Processing
- **Sample Rate**: 48kHz stereo
- **Codec**: AAC ~128kbps
- **Normalization**: EBU R128 loudness to -16 LUFS
- **Conversion**: Mono to stereo, multi-channel downmixing
- **Visualization**: Waveform for audio-only files (cyan, no text overlay)

### Intro Slide Processing
- **Duration**: 3 seconds
- **Format**: PNG converted to standardized video
- **Audio**: Silent track matching other files
- **Priority**: `title.png` → first PNG found

### Audio File Processing
- **Background Search Priority**:
  1. Same filename with `.png` extension
  2. `audio_background.png` in same directory
  3. Title screen (if available)
  4. Black background (fallback)
- **Text Overlay**: "Audio only submission" (static, no filename)
- **Waveform**: Cyan visualization without background text

## Caching System

### Cache Validation
- **Parameter Comparison**: Compares FFmpeg command parameters
- **Modification Time**: Checks source file timestamps
- **Cache Files**: `.cache` JSON files alongside temp files
- **Invalidation**: Manual via C operation or automatic on parameter change

### Cache Information Stored
- Source file path and modification time
- FFmpeg command signature (MD5 hash)
- Processing parameters (duration, resolution, etc.)
- Output file properties (codec, format, etc.)

### Cache Behavior by Operation
- **Normal Processing**: Uses cache if valid
- **R Operation**: Forces cache invalidation for selected files
- **M Operation**: Preserves existing temp files
- **C Operation**: Clears all cache and temp files

## Error Handling & Logging

### Exception Hierarchy
- `VideoProcessingError` (base)
  - `FFmpegError`: Command execution failures
  - `MediaFileError`: Invalid/corrupted media
  - `CacheError`: Cache system issues
  - `EnvironmentError`: FFmpeg missing, permissions, etc.

### Logging System
- **Console Output**: Colored, level-filtered
- **File Output**: Detailed, timestamped logs in LOGS/ directory
- **Custom Levels**: SUCCESS level (25) for completion messages
- **Routing**: Independent console/file control via arguments

### Error Recovery
- **Retry Logic**: Built into FFmpeg execution
- **Graceful Degradation**: Falls back on processing failures
- **Preservation**: Keeps temp files on failure for debugging
- **Validation**: Pre-flight checks for environment and inputs

## File Operations

### O Operation (Directory Organization)
1. Creates INPUT/OUTPUT/LOGS directories if missing
2. Moves media files to INPUT/ with overwrite confirmation
3. Archives previous attempts to ARCHIVED/ subdirectory
4. Preserves existing directory structure
5. 3-second timeout for overwrite prompts (defaults to No)

### C Operation (Cache Clearing)
1. Removes temp_ directory entirely
2. Deletes all .cache files in working directory
3. Provides feedback on cleanup actions
4. Immediate exit after completion

### Cleanup Process
- **Post-Processing**: 5-second timeout prompt for temp file cleanup
- **Default**: Preserve temp files (safer option)
- **Success**: Only offers cleanup after successful completion
- **Failure**: Always preserves temp files for debugging

## Output Generation

### Filename Convention
`DirectoryName-MERGED-yyyymmdd_hhmmss.mp4`
- **Range Operations**: `DirectoryName-Ma_b-yyyymmdd_hhmmss.mp4`
- **Directory Name**: Current working directory, sanitized
- **Length Limit**: First 35 characters of directory name
- **Invalid Characters**: Replaced with underscores

### Concatenation Method
- **Stream Copy**: Uses `-c copy` when possible for speed
- **File List**: Creates `filelist.txt` in temp_ directory
- **Format**: FFmpeg concat demuxer format
- **Validation**: Checks temp file existence before concatenation

## Environment Requirements

### Dependencies
- **FFmpeg**: Must be in PATH, with ffprobe
- **Python**: 3.6 or later with typing support
- **Colorama**: Optional, graceful fallback if missing
- **Standard Library**: pathlib, subprocess, threading, etc.

### System Validation
- **FFmpeg Version**: Extracted and logged for debugging
- **Write Permissions**: Tested in current directory  
- **Disk Space**: No explicit checking (assumes sufficient)
- **Temp Directory**: Created automatically if missing

## Data Structures & Types

### Processing Order Format
`List[Tuple[int, str, str]]` where:
- `int`: 1-based index for display and temp file naming
- `str`: Filename 
- `str`: File type ('INTRO', 'VIDEO', 'AUDIO')

### Media File Categories
```python
{
    'intro': List[str],    # PNG files
    'video': List[str],    # Video files  
    'audio': List[str],    # Audio files
    'ignored': List[str]   # Files excluded from processing
}
```

### User Action Response  
`Tuple[str, Optional[List[int]]]` where:
- `str`: Action code ('Y', 'R', 'M', 'C', 'O')
- `Optional[List[int]]`: Selected indices for R/M operations

## FFmpeg Command Construction

### Base Command Structure
```bash
ffmpeg -y -t 15 -vf [video_filter] -af [audio_filter] 
       -c:v libx264 -preset medium -crf 23 -pix_fmt yuv420p
       -c:a aac -b:a 128k -ar 48000 -ac 2
       [output_path]
```

### Video Filter Chain
- Scale to 1920x1080 with aspect ratio preservation
- Letterbox/pillarbox with black bars
- Color space normalization (bt709, tv range)

### Audio Filter Chain  
- EBU R128 loudness normalization to -16 LUFS
- Sample rate conversion to 48kHz
- Channel layout standardization to stereo

## Special Processing Cases

### Audio Background Search
1. **Exact Match**: `filename.png` (same base name)
2. **Generic**: `audio_background.png` in same directory
3. **Title Screen**: Uses intro PNG if available
4. **Fallback**: Black background with warning

### Codec Name Normalization
- Maps FFmpeg command names to metadata names
- Handles hardware acceleration variants (h264_nvenc → h264)
- Ensures cache compatibility across different encoders

### Range Processing Edge Cases
- **Empty Ranges**: Validates non-empty selection
- **Invalid Indices**: Bounds checking against file count
- **Duplicate Indices**: Automatic deduplication
- **Single Index**: Accepts both single numbers and ranges

## Return Codes & Exit Behavior
- **0**: Success (proper exit code instead of sys.exit)
- **1**: Failure (environment, processing, or user cancellation)
- **KeyboardInterrupt**: Graceful handling with cleanup preservation

This comprehensive analysis covers all major features, behaviors, and edge cases in the original script to ensure complete compatibility assessment with the modularized version.