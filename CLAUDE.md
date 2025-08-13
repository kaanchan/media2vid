# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a video montage creation script (`merge_media2mp4-DEV.py`) that processes multiple media files (video, audio, images) from an INPUT directory and creates a merged video montage. The script handles different media types with appropriate processing:

- **Video files**: Direct processing with standardization
- **Audio files**: Creates video with waveform visualization and background images
- **PNG files**: Converts to video with specified duration
- **Mixed media**: Automatically detects and processes each type appropriately

## Key Commands

### Running the Script
```bash
python merge_media2mp4-DEV.py                    # Normal operation with colored output
python merge_media2mp4-DEV.py --quiet            # Show only warnings and errors  
python merge_media2mp4-DEV.py --verbose          # Show all debug information
python merge_media2mp4-DEV.py --silent           # Minimal output, log to file only
```

### Dependencies
The script requires:
- **FFmpeg**: Must be installed and available in PATH for video processing
- **Python packages**: colorama (for colored terminal output)
- **Standard library**: pathlib, subprocess, argparse, logging, datetime, typing, dataclasses, enum

## Architecture

### Core Processing Pipeline
1. **Environment Validation**: Checks for FFmpeg availability
2. **File Discovery**: Scans INPUT directory for supported media files
3. **User Interaction**: Presents options for processing (All, Range, Individual, etc.)
4. **Media Processing**: Processes each file based on type using FFmpeg
5. **Final Merge**: Concatenates all processed files into final output
6. **Cleanup**: Manages temporary files and cache

### Key Functions
- `process_video_file()`: Handles video file processing and standardization
- `process_audio_file()`: Creates video from audio with waveform visualization  
- `process_intro_file()`: Converts PNG images to video format
- `run_ffmpeg_with_error_handling()`: Centralized FFmpeg execution with error handling
- `build_base_ffmpeg_cmd()`: Constructs standardized FFmpeg parameters

### Directory Structure
- `INPUT/`: Source media files for processing
- `OUTPUT/`: Final merged video outputs with timestamps
- `temp_/`: Temporary processed files and cache data
- `LOGS/`: Processing logs with timestamps
- `ARCHIVED/`: Previous processing attempts and backups

### Caching System
The script implements file-based caching using `.cache` files to avoid reprocessing unchanged media files. Cache validation checks file modification times and processing parameters.

### Output Standardization
All processed videos are standardized to:
- Resolution: 1920x1080
- Frame rate: 30fps
- Video codec: H.264 (yuv420p)
- Audio codec: AAC (48kHz, stereo)