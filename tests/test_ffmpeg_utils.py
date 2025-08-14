"""
Tests for FFmpeg utility functions.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, Mock, call
import subprocess
import sys
import os

# Import functions from the src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.ffmpeg_utils import (
    build_base_ffmpeg_cmd,
    get_video_filter,
    get_audio_filter,
    get_stream_info,
    run_ffmpeg_with_error_handling
)

class TestBuildBaseFfmpegCmd:
    """Test FFmpeg command building."""
    
    def test_build_base_ffmpeg_cmd_default(self):
        """Test default command building."""
        cmd = build_base_ffmpeg_cmd("output.mp4")
        
        assert cmd[0:2] == ['ffmpeg', '-y']
        assert 'output.mp4' in cmd
        assert '-c:v' in cmd
        assert '-c:a' in cmd
        assert '-t' in cmd
        
        # Check default duration
        t_index = cmd.index('-t')
        assert cmd[t_index + 1] == '15'
    
    def test_build_base_ffmpeg_cmd_custom_duration(self):
        """Test command building with custom duration."""
        cmd = build_base_ffmpeg_cmd("output.mp4", duration=30)
        
        t_index = cmd.index('-t')
        assert cmd[t_index + 1] == '30'
    
    def test_build_base_ffmpeg_cmd_gpu_encoding(self):
        """Test GPU encoding option."""
        cmd = build_base_ffmpeg_cmd("output.mp4", use_gpu=True)
        
        # Should use h264_nvenc instead of libx264
        c_v_index = cmd.index('-c:v')
        assert cmd[c_v_index + 1] == 'h264_nvenc'
    
    def test_build_base_ffmpeg_cmd_cpu_encoding(self):
        """Test CPU encoding (default)."""
        cmd = build_base_ffmpeg_cmd("output.mp4", use_gpu=False)
        
        # Should use libx264
        c_v_index = cmd.index('-c:v')
        assert cmd[c_v_index + 1] == 'libx264'
    
    def test_build_base_ffmpeg_cmd_required_params(self):
        """Test that required parameters are present."""
        cmd = build_base_ffmpeg_cmd("output.mp4")
        
        # Check for required video parameters
        assert '-pix_fmt' in cmd
        assert 'yuv420p' in cmd
        assert '-profile:v' in cmd
        assert 'high' in cmd
        
        # Check for required audio parameters
        assert '-c:a' in cmd
        assert 'aac' in cmd
        assert '-ar' in cmd
        assert '48000' in cmd
        assert '-b:a' in cmd
        assert '128k' in cmd

class TestGetVideoFilter:
    """Test video filter generation."""
    
    def test_get_video_filter_components(self):
        """Test that video filter contains required components."""
        filter_str = get_video_filter()
        
        assert 'scale=1920:1080' in filter_str
        assert 'force_original_aspect_ratio=decrease' in filter_str
        assert 'pad=1920:1080' in filter_str
        assert 'setsar=1' in filter_str
        assert 'fps=30' in filter_str
    
    def test_get_video_filter_format(self):
        """Test video filter format."""
        filter_str = get_video_filter()
        
        # Should be a single filter chain with comma separators
        assert isinstance(filter_str, str)
        assert ',' in filter_str
        # Should not contain semicolons (which would indicate multiple chains)
        assert ';' not in filter_str

class TestGetAudioFilter:
    """Test audio filter generation."""
    
    def test_get_audio_filter_components(self):
        """Test that audio filter contains required components."""
        filter_str = get_audio_filter()
        
        assert 'aresample=48000' in filter_str
        assert 'aformat=channel_layouts=stereo' in filter_str
        assert 'loudnorm' in filter_str
        assert 'I=-16' in filter_str  # Target loudness
        assert 'TP=-1.5' in filter_str  # True peak
    
    def test_get_audio_filter_format(self):
        """Test audio filter format."""
        filter_str = get_audio_filter()
        
        # Should be a single filter chain with comma separators
        assert isinstance(filter_str, str)
        assert ',' in filter_str

class TestGetStreamInfo:
    """Test stream information extraction."""
    
    @patch('subprocess.run')
    def test_get_stream_info_success(self, mock_run):
        """Test successful stream info extraction."""
        # Mock ffprobe output
        mock_output = {
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
                    "channels": 2,
                    "channel_layout": "stereo"
                }
            ]
        }
        
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(mock_output)
        )
        
        result = get_stream_info("test.mp4")
        
        assert result['video']['codec'] == 'h264'
        assert result['video']['resolution'] == '1920x1080'
        assert result['video']['fps'] == '30.0'
        assert result['video']['pix_fmt'] == 'yuv420p'
        
        assert result['audio']['codec'] == 'aac'
        assert result['audio']['sample_rate'] == '48000'
        assert result['audio']['channels'] == 2
        assert result['audio']['channel_layout'] == 'stereo'
    
    @patch('subprocess.run')
    def test_get_stream_info_video_only(self, mock_run):
        """Test stream info for video-only file."""
        mock_output = {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1280,
                    "height": 720,
                    "pix_fmt": "yuv420p",
                    "r_frame_rate": "25/1"
                }
            ]
        }
        
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(mock_output)
        )
        
        result = get_stream_info("video_only.mp4")
        
        assert result['video'] is not None
        assert result['audio'] is None
        assert result['video']['resolution'] == '1280x720'
        assert result['video']['fps'] == '25.0'
    
    @patch('subprocess.run')
    def test_get_stream_info_audio_only(self, mock_run):
        """Test stream info for audio-only file."""
        mock_output = {
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "mp3",
                    "sample_rate": "44100",
                    "channels": 2
                }
            ]
        }
        
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(mock_output)
        )
        
        result = get_stream_info("audio_only.mp3")
        
        assert result['video'] is None
        assert result['audio'] is not None
        assert result['audio']['codec'] == 'mp3'
        assert result['audio']['sample_rate'] == '44100'
    
    @patch('subprocess.run')
    def test_get_stream_info_fps_parsing(self, mock_run):
        """Test various fps format parsing."""
        test_cases = [
            ("30/1", "30.0"),
            ("60000/1001", "59.9"),
            ("25/1", "25.0"),
            ("invalid", "unknown"),
            ("0/1", "unknown")  # Division by zero
        ]
        
        for r_frame_rate, expected_fps in test_cases:
            mock_output = {
                "streams": [
                    {
                        "codec_type": "video",
                        "codec_name": "h264",
                        "width": 1920,
                        "height": 1080,
                        "r_frame_rate": r_frame_rate
                    }
                ]
            }
            
            mock_run.return_value = Mock(
                returncode=0,
                stdout=json.dumps(mock_output)
            )
            
            result = get_stream_info("test.mp4")
            assert result['video']['fps'] == expected_fps
    
    @patch('subprocess.run')
    def test_get_stream_info_failure(self, mock_run):
        """Test stream info when ffprobe fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'ffprobe')
        
        result = get_stream_info("nonexistent.mp4")
        
        assert result == {'video': None, 'audio': None}
    
    @patch('subprocess.run')
    def test_get_stream_info_invalid_json(self, mock_run):
        """Test stream info with invalid JSON output."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="invalid json"
        )
        
        result = get_stream_info("test.mp4")
        
        assert result == {'video': None, 'audio': None}

class TestRunFfmpegWithErrorHandling:
    """Test FFmpeg execution with error handling."""
    
    @patch('src.cache_system.save_cache_info')
    @patch('src.ffmpeg_utils.print_stream_info')
    @patch('src.cache_system.is_cached_file_valid')
    @patch('subprocess.run')
    def test_run_ffmpeg_success(self, mock_run, mock_cache_valid, mock_print_info, mock_save_cache):
        """Test successful FFmpeg execution."""
        mock_cache_valid.return_value = False  # Force execution
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        with patch('src.config.use_cache', True):
            result = run_ffmpeg_with_error_handling(
                ['ffmpeg', '-i', 'input.mp4', 'output.mp4'],
                "test conversion",
                "output.mp4",
                "input.mp4",
                "VIDEO"
            )
        
        assert result is True
        mock_run.assert_called_once()
        mock_save_cache.assert_called_once()
        mock_print_info.assert_called_once()
    
    @patch('src.cache_system.is_cached_file_valid')
    @patch('src.ffmpeg_utils.print_stream_info')
    def test_run_ffmpeg_cache_hit(self, mock_print_info, mock_cache_valid):
        """Test cache hit (no FFmpeg execution needed)."""
        mock_cache_valid.return_value = True
        
        with patch('src.config.use_cache', True):
            with patch('subprocess.run') as mock_run:
                result = run_ffmpeg_with_error_handling(
                    ['ffmpeg', '-i', 'input.mp4', 'output.mp4'],
                    "test conversion",
                    "output.mp4",
                    "input.mp4",
                    "VIDEO"
                )
        
        assert result is True
        mock_run.assert_not_called()  # Should not execute FFmpeg
        mock_print_info.assert_called_once()
    
    @patch('src.cache_system.is_cached_file_valid')
    @patch('subprocess.run')
    def test_run_ffmpeg_failure(self, mock_run, mock_cache_valid):
        """Test FFmpeg execution failure."""
        mock_cache_valid.return_value = False
        mock_run.side_effect = subprocess.CalledProcessError(
            1, 'ffmpeg', stderr="Error: input file not found"
        )
        
        with patch('src.config.use_cache', True):
            result = run_ffmpeg_with_error_handling(
                ['ffmpeg', '-i', 'input.mp4', 'output.mp4'],
                "test conversion",
                "output.mp4",
                "input.mp4",
                "VIDEO"
            )
        
        assert result is False
    
    @patch('subprocess.run')
    def test_run_ffmpeg_cache_disabled(self, mock_run):
        """Test FFmpeg execution with cache disabled."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        with patch('src.config.use_cache', False):
            result = run_ffmpeg_with_error_handling(
                ['ffmpeg', '-i', 'input.mp4', 'output.mp4'],
                "test conversion",
                "output.mp4",
                "input.mp4",
                "VIDEO"
            )
        
        assert result is True
        mock_run.assert_called_once()
    
    @patch('src.cache_system.is_cached_file_valid')
    @patch('subprocess.run')
    def test_run_ffmpeg_concat_no_cache(self, mock_run, mock_cache_valid):
        """Test that CONCAT type never uses cache."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        with patch('src.config.use_cache', True):
            result = run_ffmpeg_with_error_handling(
                ['ffmpeg', '-f', 'concat', '-i', 'list.txt', 'output.mp4'],
                "concatenation",
                "output.mp4",
                "list.txt",
                "CONCAT"
            )
        
        assert result is True
        mock_cache_valid.assert_not_called()  # Should not check cache for CONCAT
        mock_run.assert_called_once()
    
    @patch('src.cache_system.is_cached_file_valid')
    @patch('subprocess.run')
    def test_run_ffmpeg_cleanup_on_failure(self, mock_run, mock_cache_valid, temp_dir):
        """Test cleanup when FFmpeg fails."""
        mock_cache_valid.return_value = False
        mock_run.side_effect = subprocess.CalledProcessError(1, 'ffmpeg')
        
        output_file = temp_dir / "output.mp4"
        cache_file = temp_dir / "output.cache"
        
        # Create files that should be cleaned up
        output_file.touch()
        cache_file.touch()
        
        with patch('src.config.use_cache', True):
            result = run_ffmpeg_with_error_handling(
                ['ffmpeg', '-i', 'input.mp4', str(output_file)],
                "test conversion",
                str(output_file),
                "input.mp4",
                "VIDEO"
            )
        
        assert result is False
        # Files should be cleaned up after failure
        assert not output_file.exists()
        assert not cache_file.exists()