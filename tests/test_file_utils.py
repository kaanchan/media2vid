"""
Tests for file utility functions.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, Mock
import sys
import os

# Import functions from the src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.file_utils import (
    extract_person_name,
    is_temp_file, 
    categorize_media_files
)
from src.config import get_media_extensions
from src.utils import (
    generate_output_filename,
    parse_range,
    format_range_indicator
)

class TestExtractPersonName:
    """Test person name extraction from filenames."""
    
    def test_extract_person_name_with_pattern(self):
        """Test extracting person name from proper format."""
        assert extract_person_name("Interview - John Doe.mp4") == "john doe"
        assert extract_person_name("Question - Jane Smith.mov") == "jane smith"
        assert extract_person_name("Audio - Bob Wilson.m4a") == "bob wilson"
    
    def test_extract_person_name_without_pattern(self):
        """Test fallback to full filename when pattern not found."""
        assert extract_person_name("random_video.mp4") == "random_video.mp4"
        assert extract_person_name("test.mov") == "test.mov"
        assert extract_person_name("no-dash-here.mp4") == "no-dash-here.mp4"
    
    def test_extract_person_name_edge_cases(self):
        """Test edge cases for person name extraction."""
        assert extract_person_name("Title - .mp4") == "title - .mp4"  # No valid name after dash
        assert extract_person_name("NoExtension - Person") == "noextension - person"  # No extension
        assert extract_person_name("Multiple - Dashes - Person Name.mp4") == "dashes - person name"  # Multiple dashes

class TestIsTempFile:
    """Test temporary file detection."""
    
    def test_is_temp_file_true_cases(self, temp_dir):
        """Test files that should be excluded."""
        # Create test files
        temp_files = [
            "temp_0.mp4",
            "temp_123.mp4", 
            "video-MERGED-20240101_120000.mp4",
            "video-M1_5-20240101_120000.mp4",
            "video-R3-20240101_120000.mp4",
            ".hidden",
            "~backup",
            "filelist.txt",
            "script.py",
            "test.ps1"
        ]
        
        for filename in temp_files:
            file_path = temp_dir / filename
            file_path.touch()
            assert is_temp_file(file_path), f"Should exclude {filename}"
    
    def test_is_temp_file_false_cases(self, temp_dir):
        """Test files that should NOT be excluded."""
        valid_files = [
            "video.mp4",
            "audio.m4a", 
            "image.png",
            "normal_file.mov",
            "interview - person.mp4"
        ]
        
        for filename in valid_files:
            file_path = temp_dir / filename
            file_path.touch()
            assert not is_temp_file(file_path), f"Should NOT exclude {filename}"
    
    def test_is_temp_file_directories(self, temp_dir):
        """Test that directories are excluded."""
        dir_path = temp_dir / "subdirectory"
        dir_path.mkdir()
        assert is_temp_file(dir_path)

class TestCategorizeMediaFiles:
    """Test media file categorization."""
    
    def test_categorize_media_files_mixed(self, temp_dir):
        """Test categorization with mixed file types."""
        # Create test files
        files = [
            "video1.mp4",
            "video2.mov", 
            "audio1.m4a",
            "audio2.mp3",
            "intro.png",
            "title.png", 
            "document.txt",
            "script.py"
        ]
        
        file_paths = []
        for filename in files:
            file_path = temp_dir / filename
            file_path.touch()
            file_paths.append(file_path)
        
        result = categorize_media_files(file_paths)
        
        assert set(result['video']) == {'video1.mp4', 'video2.mov'}
        assert set(result['audio']) == {'audio1.m4a', 'audio2.mp3'}
        assert set(result['intro']) == {'intro.png', 'title.png'}
        assert set(result['ignored']) == {'document.txt', 'script.py'}
    
    def test_categorize_media_files_sorting(self, temp_dir):
        """Test that files are sorted by person name."""
        files = [
            "video - Zebra Person.mp4",
            "video - Alpha Person.mov",
            "audio - Beta Person.m4a"
        ]
        
        file_paths = []
        for filename in files:
            file_path = temp_dir / filename
            file_path.touch()
            file_paths.append(file_path)
        
        result = categorize_media_files(file_paths)
        
        # Should be sorted by person name
        assert result['video'] == ['video - Alpha Person.mov', 'video - Zebra Person.mp4']
        assert result['audio'] == ['audio - Beta Person.m4a']

class TestGetMediaExtensions:
    """Test media extension retrieval."""
    
    def test_get_media_extensions_format(self):
        """Test that extensions are returned in correct format."""
        video_ext, audio_ext = get_media_extensions()
        
        assert isinstance(video_ext, set)
        assert isinstance(audio_ext, set)
        
        # Check some known extensions
        assert '.mp4' in video_ext
        assert '.mov' in video_ext
        assert '.mp3' in audio_ext
        assert '.m4a' in audio_ext
        
        # Check extensions are lowercase
        for ext in video_ext | audio_ext:
            assert ext.islower()
            assert ext.startswith('.')

class TestGenerateOutputFilename:
    """Test output filename generation."""
    
    @patch('src.utils.Path.cwd')
    @patch('src.utils.datetime')
    def test_generate_output_filename_basic(self, mock_datetime, mock_cwd):
        """Test basic filename generation."""
        mock_cwd.return_value.name = "test_directory"
        mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
        
        result = generate_output_filename()
        assert result == "test_directory-MERGED-20240101_120000.mp4"
    
    @patch('src.utils.Path.cwd')
    @patch('src.utils.datetime')
    def test_generate_output_filename_with_range(self, mock_datetime, mock_cwd):
        """Test filename generation with range indicator."""
        mock_cwd.return_value.name = "test_directory"
        mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
        
        result = generate_output_filename("M1_5")
        assert result == "test_directory-M1_5-20240101_120000.mp4"
    
    @patch('src.utils.Path.cwd')
    @patch('src.utils.datetime')
    def test_generate_output_filename_sanitization(self, mock_datetime, mock_cwd):
        """Test filename sanitization for invalid characters."""
        mock_cwd.return_value.name = "test<dir>ect:ory"
        mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
        
        result = generate_output_filename()
        assert result == "test_dir_ect_ory-MERGED-20240101_120000.mp4"

class TestParseRange:
    """Test range parsing functionality."""
    
    def test_parse_range_single_number(self):
        """Test parsing single numbers."""
        assert parse_range("3", 10) == [3]
        assert parse_range("1", 5) == [1]
        assert parse_range("10", 10) == [10]
    
    def test_parse_range_range_format(self):
        """Test parsing range format."""
        assert parse_range("1-5", 10) == [1, 2, 3, 4, 5]
        assert parse_range("3-7", 10) == [3, 4, 5, 6, 7]
        assert parse_range("5-1", 10) == [1, 2, 3, 4, 5]  # Should swap
    
    def test_parse_range_empty_string(self):
        """Test parsing empty string (should return all)."""
        assert parse_range("", 5) == [1, 2, 3, 4, 5]
        assert parse_range("  ", 3) == [1, 2, 3]
    
    def test_parse_range_boundary_clamping(self):
        """Test that ranges are clamped to valid boundaries."""
        assert parse_range("0-3", 5) == [1, 2, 3]  # Start clamped to 1
        assert parse_range("3-10", 5) == [3, 4, 5]  # End clamped to max
        assert parse_range("15", 10) == [10]  # Single number clamped
    
    def test_parse_range_invalid_format(self):
        """Test invalid format handling."""
        assert parse_range("abc", 5) == []
        assert parse_range("1-abc", 5) == []
        assert parse_range("abc-5", 5) == []

class TestFormatRangeIndicator:
    """Test range indicator formatting."""
    
    def test_format_range_indicator_empty(self):
        """Test empty range string."""
        assert format_range_indicator("", "M", 10) == "M0"
        assert format_range_indicator("  ", "R", 10) == "R0"
    
    def test_format_range_indicator_single(self):
        """Test single number."""
        assert format_range_indicator("3", "M", 10) == "M3"
        assert format_range_indicator("7", "R", 10) == "R7"
    
    def test_format_range_indicator_range(self):
        """Test range format."""
        assert format_range_indicator("1-5", "M", 10) == "M1_5"
        assert format_range_indicator("3-7", "R", 10) == "R3_7"
    
    def test_format_range_indicator_open_ended(self):
        """Test open-ended range."""
        assert format_range_indicator("3-", "M", 10) == "M3_10"
        assert format_range_indicator("7-", "R", 15) == "R7_15"
    
    def test_format_range_indicator_comma_separated(self):
        """Test comma-separated values."""
        assert format_range_indicator("1,3,5", "M", 10) == "M1,3,5"
        assert format_range_indicator("2,4,6", "R", 10) == "R2,4,6"
    
    def test_format_range_indicator_mixed(self):
        """Test mixed format with ranges and singles."""
        assert format_range_indicator("1,3-5,8-", "M", 10) == "M1,3_5,8_10"
        assert format_range_indicator("2,4-6,9-", "R", 12) == "R2,4_6,9_12"