# media2vid User Guide

> **Version:** feature/modularize-codebase branch (post-v31)  
> **Last Updated:** August 2025  
> **Commit:** 2f843b9 - Update test suite for enhanced functionality compatibility

## Overview

media2vid is a universal video montage creation script that automatically processes mixed media files (video, audio, images) from an INPUT directory and creates a single concatenated video with standardized formatting.

## Quick Start

```bash
# Basic usage
python media2vid.py

# Show only warnings and errors
python media2vid.py --log-level quiet

# Show all debug information  
python media2vid.py --log-level verbose

# Use custom intro image
python media2vid.py --intro-pic my_intro.png

# Use custom audio background for all audio files
python media2vid.py --audio-bg-pic my_background.png
```

## Command Line Options

### Logging Control
- `--log-level {silent,quiet,normal,verbose}` - Set verbosity level (default: normal)
- `--no-console` - Disable console output, log to file only
- `--no-file` - Disable file logging, console output only

### Media Processing
- `--audio-bg-pic FILE` - Background image for all audio files (overrides automatic search)
- `--intro-pic FILE` - Custom intro screen image (overrides automatic PNG detection)

## Interactive Menu Options

When you run the script, you'll see a countdown timer with these options:

- **Y/Enter** - Continue with processing all files
- **P** - Pause countdown (requires Y/Enter to resume)
- **R** - Re-render specific range of files (force recreate temp files)
- **M** - Merge existing temp files (with optional range)
- **C** - Clear cache (delete temp_ directory and .cache files)
- **O** - Organize directory (move files to INPUT/OUTPUT/LOGS structure)
- **N/Q** - Cancel and exit

### Range Selection (R/M Operations)

Use comma-separated indices or ranges:
- `3` - Single file (index 3)
- `1,3,5` - Multiple specific files
- `1-5` - Range from 1 to 5
- `3-` - From 3 to end
- `1,3-5,8-` - Mixed format

## File Support

### Supported Video Formats (12)
`.mp4, .mov, .avi, .mkv, .wmv, .flv, .webm, .m4v, .3gp, .ts, .mts, .vob`

### Supported Audio Formats (9)
`.mp3, .m4a, .wav, .flac, .aac, .ogg, .wma, .opus, .mp2`

### Image Files
`.png` - For intro slides/title screens

## File Naming Convention

For proper sorting, use: `Description - PersonName.extension`

Examples:
- `Interview - John Doe.mp4`
- `Question - Jane Smith.m4a`
- `Response - Bob Wilson.mov`

Files without this format will be sorted alphabetically by full filename.

## Processing Standards

All content is standardized to:
- **Resolution:** 1920x1080 with aspect ratio preservation
- **Frame Rate:** 30fps
- **Duration:** 15 seconds (cropped if longer)
- **Video Codec:** H.264 High profile (yuv420p)
- **Audio:** 48kHz stereo, AAC (~128kbps), EBU R128 normalized to -16 LUFS

## Directory Structure

The script works with the following directory structure:

```
project-folder/
├── INPUT/          # Source media files
├── OUTPUT/         # Final merged videos with timestamps
├── LOGS/           # Processing logs with timestamps
├── temp_/          # Temporary processed files and cache
└── ARCHIVED/       # Previous processing attempts (via O operation)
```

## Processing Order

1. **Intro Files** - PNG images (3 seconds duration)
2. **Video Files** - All supported video formats
3. **Audio Files** - All supported audio formats with waveform visualization

## Audio Background Search Priority

For audio files, the system searches for background images in this order:

1. Same filename with `.png` extension (e.g., `audio.m4a` → `audio.png`)
2. `audio_background.png` in the same directory
3. Custom background from `--audio-bg-pic` option
4. Black background (fallback)

## Output Files

Final videos are saved as:
`DirectoryName-MERGED-yyyymmdd_hhmmss.mp4`

Range operations include indicators:
- `DirectoryName-M1_5-yyyymmdd_hhmmss.mp4` (Merge files 1-5)
- `DirectoryName-R3,7,9-yyyymmdd_hhmmss.mp4` (Re-render files 3,7,9)

## Caching System

The script uses intelligent caching to avoid reprocessing unchanged files:

- Cache files (`.cache`) store processing parameters and metadata
- Files are reprocessed only if source files change or parameters differ
- Use **C** operation to clear all cache and temp files
- Use **R** operation to force regeneration of specific files

## Requirements

- **FFmpeg** - Must be installed and available in PATH
- **Python 3.6+** - With standard library support
- **colorama** - For colored terminal output (`pip install colorama`)
- **Sufficient disk space** - Roughly 2x the size of source content for temp files

## Troubleshooting

### Common Issues

1. **FFmpeg not found** - Ensure FFmpeg is installed and in your PATH
2. **Permission errors** - Check write permissions in the current directory
3. **Files not detected** - Verify file extensions are supported and files aren't hidden/temp files
4. **Audio processing fails** - Check if audio files are corrupted or in unsupported format

### Log Files

Detailed logs are saved in `LOGS/video_processor_yyyymmdd_hhmmss.log` with:
- All processing steps
- FFmpeg commands executed
- Error details and debugging information
- Performance timing information

### Getting Help

Use `python media2vid.py --help` for quick reference of all command line options.