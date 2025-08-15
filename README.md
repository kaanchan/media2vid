# media2vid

> **Version:** feature/modularize-codebase branch (post-v31)  
> **Last Updated:** August 2025  
> **Commit:** 2f843b9 - Update test suite for enhanced functionality compatibility

Generate video from assorted videos, audio recordings, and pics.

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
