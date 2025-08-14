"""
Custom exception classes for media2vid.
"""
from typing import List

class VideoProcessingError(Exception):
    """Base exception for video processing errors."""
    pass

class FFmpegError(VideoProcessingError):
    """FFmpeg command execution failed."""
    def __init__(self, message: str, command: List[str], exit_code: int, stderr: str = ""):
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr
        super().__init__(message)

class MediaFileError(VideoProcessingError):
    """Media file invalid or corrupted."""
    pass

class CacheError(VideoProcessingError):
    """Cache system error."""
    pass

class EnvironmentError(VideoProcessingError):
    """Environment setup error (FFmpeg missing, permissions, etc.)."""
    pass