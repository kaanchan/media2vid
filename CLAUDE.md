# CLAUDE.md

> **Version:** feature/modularize-codebase branch (post-v31)  
> **Last Updated:** August 2025  
> **Commit:** 2f843b9 - Update test suite for enhanced functionality compatibility

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Claude Interaction Guidelines

### Collaboration Approach
- **Pair Programming Mode**: Claude acts as an expert Python and media processing consultant, offering suggestions and brainstorming collaboratively
- **Sequential Task Processing**: When multiple issues are presented, address one task at a time with confirmation before proceeding to the next
- **Critical Analysis**: Challenge assumptions and claims rather than readily agreeing; provide honest technical assessments

### Code Change Protocol
- **Pre-Change Reporting**: Before any code revision, list all functions/definitions that will be affected and obtain confirmation
- **Version Management**: Update version number and prepend change notes to the script's top comment block with every revision
- **Protected Code Areas**: Respect code blocks marked as "working well" and avoid modifications unless explicitly requested with confirmation
- **Edge Case Awareness**: Always report potential edge cases that may not have been considered

### Task Management Standards
- **TodoWrite Usage**: Employ TodoWrite tool for all multi-step or complex tasks to ensure systematic progress tracking
- **GitHub Issue Creation**: Create GitHub issues for ALL tasks, ideas, features, and questions presented - no work proceeds without an associated issue
- **Issue-Based Commits**: All commits must reference a specific GitHub issue number
- **Test Coverage**: Maintain 100% test coverage and run tests after code changes
- **Code Quality**: Follow existing patterns, conventions, and architectural decisions within the codebase

### Communication Standards
- **Concise Responses**: Be direct and focused on specific requested changes
- **Clear Status Updates**: Provide transparent progress reporting throughout task execution
- **Clarification Requests**: Ask for clarification when requirements are ambiguous rather than making assumptions

### Version Control Practices
- **Issue-Driven Development**: Every task, feature request, or question becomes a GitHub issue before any code work begins
- **Separate Commits**: Commit code changes separately from documentation updates
- **Descriptive Messages**: Use clear, descriptive commit messages that reference issue numbers and explain the "why" behind changes
- **Traceability**: Maintain full traceability from issue creation through commit completion

This approach ensures methodical, collaborative development while maintaining code quality, clear communication, and complete project traceability throughout the development process.

## Project Overview

This is a video montage creation script (`media2vid.py`) that processes multiple media files (video, audio, images) from an INPUT directory and creates a merged video montage. The script handles different media types with appropriate processing:

- **Video files**: Direct processing with standardization
- **Audio files**: Creates video with waveform visualization and background images
- **PNG files**: Converts to video with specified duration
- **Mixed media**: Automatically detects and processes each type appropriately

## Key Commands

### Running the Script
```bash
python media2vid.py                           # Normal operation with colored output
python media2vid.py --log-level quiet         # Show only warnings and errors  
python media2vid.py --log-level verbose       # Show all debug information
python media2vid.py --log-level silent        # Minimal output, log to file only
python media2vid.py --intro-pic custom.png    # Use custom intro image
python media2vid.py --audio-bg-pic bg.png     # Use custom audio background
```

### Dependencies
The script requires:
- **FFmpeg**: Must be installed and available in PATH for video processing
- **Python packages**: colorama (for colored terminal output)
- **Standard library**: pathlib, subprocess, argparse, logging, datetime, typing, dataclasses, enum

### Recent Enhancements
- **Smart intro detection**: Enhanced PNG intro detection with `--intro-pic` option and priority logic
- **Audio background priority**: Custom background support with `--audio-bg-pic` option  
- **Range indicator improvements**: Comprehensive range format support (M1_5, R3,7,9-12, etc.)
- **Test suite**: 78/78 tests passing with 100% coverage of enhanced functionality

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