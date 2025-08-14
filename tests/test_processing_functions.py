"""
Tests for core processing functions.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, Mock, call
import sys
import os

# Import functions from the src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.processors.intro_processor import process_intro_file
from src.processors.audio_processor import process_audio_file
from src.processors.video_processor import process_video_file
from src.file_utils import find_audio_background

class TestProcessIntroFile:
    """Test intro file processing."""
    
    @patch('src.ffmpeg_utils.run_ffmpeg_with_error_handling')
    @patch('src.ffmpeg_utils.get_video_filter')
    @patch('src.ffmpeg_utils.build_base_ffmpeg_cmd')
    def test_process_intro_file_success(self, mock_build_cmd, mock_video_filter, mock_run_ffmpeg):
        """Test successful intro file processing."""
        mock_video_filter.return_value = 'scale=1920:1080'
        mock_build_cmd.return_value = ['-c:v', 'libx264', '-t', '3', 'output.mp4']
        mock_run_ffmpeg.return_value = True
        
        result = process_intro_file('input.png', 'output.mp4')
        
        assert result is True
        mock_run_ffmpeg.assert_called_once()
        
        # Check that the command includes PNG input and silent audio
        args, kwargs = mock_run_ffmpeg.call_args
        cmd = args[0]
        cmd_str = ' '.join(cmd)
        assert 'input.png' in cmd_str
        assert 'anullsrc' in cmd_str
        assert 'output.mp4' in cmd_str
    
    @patch('src.ffmpeg_utils.run_ffmpeg_with_error_handling')
    def test_process_intro_file_failure(self, mock_run_ffmpeg):
        """Test intro file processing failure."""
        mock_run_ffmpeg.return_value = False
        
        result = process_intro_file('input.png', 'output.mp4')
        
        assert result is False
    
    @patch('src.ffmpeg_utils.run_ffmpeg_with_error_handling')
    @patch('src.ffmpeg_utils.get_video_filter')
    @patch('src.ffmpeg_utils.build_base_ffmpeg_cmd')
    def test_process_intro_file_custom_duration(self, mock_build_cmd, mock_video_filter, mock_run_ffmpeg):
        """Test intro file processing with custom duration."""
        mock_video_filter.return_value = 'scale=1920:1080'
        mock_build_cmd.return_value = ['-c:v', 'libx264', '-t', '5', 'output.mp4']
        mock_run_ffmpeg.return_value = True
        
        result = process_intro_file('input.png', 'output.mp4', duration=5)
        
        assert result is True
        # Check that build_base_ffmpeg_cmd was called with custom duration
        mock_build_cmd.assert_called_once()
        args, kwargs = mock_build_cmd.call_args
        assert kwargs.get('duration') == 5
    
    @patch('src.ffmpeg_utils.run_ffmpeg_with_error_handling')
    def test_process_intro_file_exception(self, mock_run_ffmpeg):
        """Test intro file processing handles exceptions."""
        mock_run_ffmpeg.side_effect = Exception("Test error")
        
        result = process_intro_file('input.png', 'output.mp4')
        
        assert result is False

class TestProcessAudioFile:
    """Test audio file processing."""
    
    @patch('src.ffmpeg_utils.run_ffmpeg_with_error_handling')
    @patch('src.file_utils.find_audio_background')
    @patch('src.ffmpeg_utils.get_audio_filter')
    @patch('src.ffmpeg_utils.build_base_ffmpeg_cmd')
    def test_process_audio_file_with_background(self, mock_build_cmd, mock_audio_filter, mock_find_bg, mock_run_ffmpeg):
        """Test audio file processing with background image."""
        mock_find_bg.return_value = (Path('background.png'), 'background image')
        mock_audio_filter.return_value = 'aresample=48000'
        mock_build_cmd.return_value = ['-c:v', 'libx264', 'output.mp4']
        mock_run_ffmpeg.return_value = True
        
        result = process_audio_file('input.m4a', 'output.mp4')
        
        assert result is True
        mock_run_ffmpeg.assert_called_once()
        
        # Check command includes background image and audio overlay
        args, kwargs = mock_run_ffmpeg.call_args
        cmd = args[0]
        assert 'background.png' in ' '.join(cmd)
        assert 'input.m4a' in cmd
        assert 'drawtext' in ' '.join(cmd)
        assert 'Audio only submission' in ' '.join(cmd)
    
    @patch('src.ffmpeg_utils.run_ffmpeg_with_error_handling')
    @patch('src.file_utils.find_audio_background')
    @patch('src.ffmpeg_utils.get_audio_filter')
    @patch('src.ffmpeg_utils.build_base_ffmpeg_cmd')
    def test_process_audio_file_no_background(self, mock_build_cmd, mock_audio_filter, mock_find_bg, mock_run_ffmpeg):
        """Test audio file processing without background image."""
        mock_find_bg.return_value = (None, 'black background')
        mock_audio_filter.return_value = 'aresample=48000'
        mock_build_cmd.return_value = ['-c:v', 'libx264', 'output.mp4']
        mock_run_ffmpeg.return_value = True
        
        result = process_audio_file('input.m4a', 'output.mp4')
        
        assert result is True
        
        # Check command uses black background
        args, kwargs = mock_run_ffmpeg.call_args
        cmd = args[0]
        assert 'color=black' in ' '.join(cmd)
        assert 'input.m4a' in cmd
    
    @patch('src.ffmpeg_utils.run_ffmpeg_with_error_handling')
    @patch('src.file_utils.find_audio_background')
    def test_process_audio_file_background_fallback(self, mock_find_bg, mock_run_ffmpeg):
        """Test audio file processing with background image fallback."""
        mock_find_bg.return_value = (Path('background.png'), 'background image')
        # First call fails (background image), second succeeds (black background)
        mock_run_ffmpeg.side_effect = [False, True]
        
        result = process_audio_file('input.m4a', 'output.mp4')
        
        assert result is True
        assert mock_run_ffmpeg.call_count == 2
        
        # Check that second call uses black background
        second_call_args = mock_run_ffmpeg.call_args_list[1][0]
        cmd = second_call_args[0]
        assert 'color=black' in ' '.join(cmd)
    
    @patch('src.ffmpeg_utils.run_ffmpeg_with_error_handling')
    def test_process_audio_file_exception(self, mock_run_ffmpeg):
        """Test audio file processing handles exceptions."""
        mock_run_ffmpeg.side_effect = Exception("Test error")
        
        result = process_audio_file('input.m4a', 'output.mp4')
        
        assert result is False

class TestProcessVideoFile:
    """Test video file processing."""
    
    @patch('src.ffmpeg_utils.run_ffmpeg_with_error_handling')
    @patch('src.ffmpeg_utils.get_video_filter')
    @patch('src.ffmpeg_utils.get_audio_filter')
    @patch('src.ffmpeg_utils.build_base_ffmpeg_cmd')
    def test_process_video_file_success(self, mock_build_cmd, mock_audio_filter, mock_video_filter, mock_run_ffmpeg):
        """Test successful video file processing."""
        mock_video_filter.return_value = 'scale=1920:1080'
        mock_audio_filter.return_value = 'aresample=48000'
        mock_build_cmd.return_value = ['-c:v', 'libx264', 'output.mp4']
        mock_run_ffmpeg.return_value = True
        
        result = process_video_file('input.mp4', 'output.mp4')
        
        assert result is True
        mock_run_ffmpeg.assert_called_once()
        
        # Check command includes input file and filters
        args, kwargs = mock_run_ffmpeg.call_args
        cmd = args[0]
        assert 'input.mp4' in cmd
        assert '-vf' in cmd
        assert '-af' in cmd
        assert 'output.mp4' in cmd
    
    @patch('src.ffmpeg_utils.run_ffmpeg_with_error_handling')
    def test_process_video_file_failure(self, mock_run_ffmpeg):
        """Test video file processing failure."""
        mock_run_ffmpeg.return_value = False
        
        result = process_video_file('input.mp4', 'output.mp4')
        
        assert result is False
    
    @patch('src.ffmpeg_utils.run_ffmpeg_with_error_handling')
    def test_process_video_file_exception(self, mock_run_ffmpeg):
        """Test video file processing handles exceptions."""
        mock_run_ffmpeg.side_effect = Exception("Test error")
        
        result = process_video_file('input.mp4', 'output.mp4')
        
        assert result is False

class TestFindAudioBackground:
    """Test audio background finding logic."""
    
    def test_find_audio_background_same_name(self, mock_input_dir):
        """Test finding background with same name as audio file."""
        # Create matching PNG file
        audio_file = "test_audio - Person.m4a"
        png_file = "test_audio - Person.png"
        (mock_input_dir / png_file).touch()
        
        with patch('src.config.input_dir', mock_input_dir):
            result_path, description = find_audio_background(audio_file)
        
        assert result_path.name == png_file
        assert 'same-name PNG' in description
    
    def test_find_audio_background_case_insensitive(self, mock_input_dir):
        """Test case-insensitive matching for background."""
        audio_file = "TEST_AUDIO.m4a"
        png_file = "test_audio.PNG"  # Different case
        (mock_input_dir / png_file).touch()
        
        with patch('src.config.input_dir', mock_input_dir):
            result_path, description = find_audio_background(audio_file)
        
        assert result_path.name == png_file
        assert 'same-name PNG' in description
    
    def test_find_audio_background_audio_background_png(self, mock_input_dir):
        """Test finding audio_background.png."""
        audio_file = "some_audio.m4a"
        bg_file = "audio_background.png"
        (mock_input_dir / bg_file).touch()
        
        with patch('src.config.input_dir', mock_input_dir):
            result_path, description = find_audio_background(audio_file)
        
        assert result_path.name == bg_file
        assert 'audio_background.png' in description
    
    def test_find_audio_background_custom_path(self, mock_input_dir):
        """Test using custom background path."""
        audio_file = "some_audio.m4a"
        custom_bg = mock_input_dir / "custom.png"
        custom_bg.touch()
        
        with patch('src.config.input_dir', mock_input_dir):
            result_path, description = find_audio_background(audio_file, str(custom_bg))
        
        assert result_path == custom_bg
        assert 'custom background' in description
    
    def test_find_audio_background_none_found(self, mock_input_dir):
        """Test when no background is found."""
        audio_file = "some_audio.m4a"
        
        with patch('src.config.input_dir', mock_input_dir):
            result_path, description = find_audio_background(audio_file)
        
        assert result_path is None
        assert 'black background' in description
    
    def test_find_audio_background_priority_order(self, mock_input_dir):
        """Test that background finding follows priority order."""
        audio_file = "test_audio.m4a"
        
        # Create all possible backgrounds
        same_name = "test_audio.png"
        audio_bg = "audio_background.png"
        custom_bg = mock_input_dir / "custom.png"
        
        (mock_input_dir / same_name).touch()
        (mock_input_dir / audio_bg).touch()
        custom_bg.touch()
        
        with patch('src.config.input_dir', mock_input_dir):
            # Test custom background takes priority
            result_path, description = find_audio_background(audio_file, str(custom_bg))
            assert result_path == custom_bg
            assert 'custom background' in description
            
            # Test same-name PNG takes priority over audio_background.png when no custom
            result_path, description = find_audio_background(audio_file, None)
            assert result_path.name == same_name
            assert 'same-name PNG' in description
    
    def test_find_audio_background_title_screen_missing(self, mock_input_dir):
        """Test when title screen path exists but file doesn't."""
        audio_file = "some_audio.m4a"
        title_screen = mock_input_dir / "nonexistent.png"
        # Don't create the file
        
        with patch('src.config.input_dir', mock_input_dir):
            result_path, description = find_audio_background(audio_file, title_screen)
        
        assert result_path is None
        assert 'black background' in description