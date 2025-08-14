"""
Pytest configuration and fixtures for media2vid tests.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path so we can import media2vid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def mock_input_dir(temp_dir):
    """Create a mock INPUT directory with test files."""
    input_dir = temp_dir / "INPUT"
    input_dir.mkdir()
    
    # Create test media files
    test_files = [
        "test_video - Person1.mp4",
        "another_video - Person2.mov", 
        "audio_file - Person3.m4a",
        "intro.png",
        "Who are you now.png"
    ]
    
    for filename in test_files:
        (input_dir / filename).touch()
    
    return input_dir

@pytest.fixture
def mock_output_dir(temp_dir):
    """Create a mock OUTPUT directory."""
    output_dir = temp_dir / "OUTPUT"
    output_dir.mkdir()
    return output_dir

@pytest.fixture
def mock_temp_dir(temp_dir):
    """Create a mock temp_ directory."""
    temp_cache_dir = temp_dir / "temp_"
    temp_cache_dir.mkdir()
    return temp_cache_dir

@pytest.fixture
def mock_ffmpeg():
    """Mock FFmpeg subprocess calls."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        yield mock_run

@pytest.fixture
def mock_ffprobe():
    """Mock ffprobe calls with sample output."""
    sample_output = {
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "pix_fmt": "yuv420p",
                "r_frame_rate": "30/1"
            },
            {
                "codec_type": "audio", 
                "codec_name": "aac",
                "sample_rate": "48000",
                "channels": 2
            }
        ],
        "format": {
            "duration": "15.0"
        }
    }
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout=str(sample_output).replace("'", '"'),
            stderr=""
        )
        yield mock_run

@pytest.fixture
def sample_media_files():
    """Sample media file data for testing."""
    return {
        'video': ['test_video - Person1.mp4', 'another_video - Person2.mov'],
        'audio': ['audio_file - Person3.m4a'],
        'intro': ['intro.png', 'Who are you now.png'],
        'ignored': ['README.md', 'script.py']
    }