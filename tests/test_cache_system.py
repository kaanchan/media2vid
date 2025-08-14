"""
Tests for cache system functionality.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock, mock_open
import sys
import os

# Import functions from the src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.cache_system import (
    normalize_codec_name,
    get_cache_info,
    is_cached_file_valid,
    save_cache_info
)

class TestNormalizeCodecName:
    """Test codec name normalization."""
    
    def test_normalize_video_codecs(self):
        """Test video codec normalization."""
        assert normalize_codec_name('libx264') == 'h264'
        assert normalize_codec_name('h264_nvenc') == 'h264'
        assert normalize_codec_name('h264_qsv') == 'h264'
        assert normalize_codec_name('libx265') == 'hevc'
        assert normalize_codec_name('hevc_nvenc') == 'hevc'
    
    def test_normalize_audio_codecs(self):
        """Test audio codec normalization."""
        assert normalize_codec_name('libfdk_aac') == 'aac'
        assert normalize_codec_name('aac') == 'aac'
        assert normalize_codec_name('libmp3lame') == 'mp3'
        assert normalize_codec_name('libopus') == 'opus'
    
    def test_normalize_unknown_codecs(self):
        """Test that unknown codecs pass through."""
        assert normalize_codec_name('unknown_codec') == 'unknown_codec'
        assert normalize_codec_name('CUSTOM') == 'custom'
    
    def test_normalize_case_insensitive(self):
        """Test case insensitive normalization."""
        assert normalize_codec_name('LIBX264') == 'h264'
        assert normalize_codec_name('H264_NVENC') == 'h264'
        assert normalize_codec_name('AAC') == 'aac'

class TestGetCacheInfo:
    """Test cache information generation."""
    
    @patch('subprocess.run')
    def test_get_cache_info_basic(self, mock_run):
        """Test basic cache info generation."""
        # Mock ffprobe output for duration
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"format": {"duration": "15.5"}}'
        )
        
        cmd = [
            'ffmpeg', '-y', '-i', 'input.mp4',
            '-c:v', 'libx264', '-crf', '23',
            '-c:a', 'aac', '-ar', '48000',
            '-t', '15', 'output.mp4'
        ]
        
        result = get_cache_info(cmd, 'VIDEO', 'input.mp4')
        
        assert result['file_type'] == 'VIDEO'
        assert result['source_file'] == 'input.mp4'
        assert result['expected']['video_codec'] == 'libx264'
        assert result['expected']['crf'] == '23'
        assert result['expected']['audio_codec'] == 'aac'
        assert result['expected']['sample_rate'] == '48000'
        assert result['expected']['duration'] == 15.0  # min of source and command
    
    @patch('subprocess.run')
    def test_get_cache_info_with_filters(self, mock_run):
        """Test cache info with video/audio filters."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"format": {"duration": "20.0"}}'
        )
        
        cmd = [
            'ffmpeg', '-y', '-i', 'input.mp4',
            '-vf', 'scale=1920:1080,fps=30',
            '-af', 'aresample=48000',
            '-t', '15', 'output.mp4'
        ]
        
        result = get_cache_info(cmd, 'VIDEO', 'input.mp4')
        
        assert result['expected']['video_filter'] == 'scale=1920:1080,fps=30'
        assert result['expected']['audio_filter'] == 'aresample=48000'
        assert result['expected']['resolution'] == '1920x1080'
    
    @patch('subprocess.run')
    def test_get_cache_info_ffprobe_failure(self, mock_run):
        """Test cache info when ffprobe fails."""
        mock_run.return_value = Mock(returncode=1, stdout='', stderr='error')
        
        cmd = ['ffmpeg', '-y', '-t', '10', 'output.mp4']
        result = get_cache_info(cmd, 'VIDEO', 'input.mp4')
        
        # Should fall back to command duration
        assert result['expected']['duration'] == 10.0

class TestIsCachedFileValid:
    """Test cache validation logic."""
    
    def test_cache_disabled(self):
        """Test that validation returns False when cache disabled."""
        with patch('src.config.use_cache', False):
            result = is_cached_file_valid(Path('dummy'), 'source', {})
            assert result is False
    
    def test_temp_file_missing(self, temp_dir):
        """Test validation when temp file doesn't exist."""
        temp_file = temp_dir / "temp_0.mp4"
        
        with patch('src.config.use_cache', True):
            result = is_cached_file_valid(temp_file, 'source', {})
            assert result is False
    
    def test_temp_file_empty(self, temp_dir):
        """Test validation when temp file is empty."""
        temp_file = temp_dir / "temp_0.mp4"
        temp_file.touch()  # Creates empty file
        
        with patch('src.config.use_cache', True):
            result = is_cached_file_valid(temp_file, 'source', {})
            assert result is False
    
    def test_source_newer_than_temp(self, temp_dir):
        """Test validation when source file is newer."""
        temp_file = temp_dir / "temp_0.mp4"
        source_file = temp_dir / "source.mp4"
        
        # Create temp file first
        temp_file.write_text("content")
        # Then source file (newer)
        source_file.write_text("content")
        
        with patch('src.config.use_cache', True):
            result = is_cached_file_valid(temp_file, str(source_file), {})
            assert result is False
    
    @patch('src.ffmpeg_utils.get_stream_info')
    def test_cache_validation_success(self, mock_stream_info, temp_dir):
        """Test successful cache validation."""
        temp_file = temp_dir / "temp_0.mp4"
        cache_file = temp_dir / "temp_0.cache"
        source_file = temp_dir / "source.mp4"
        
        # Create files with temp newer than source
        source_file.write_text("content")
        import time
        time.sleep(0.01)  # Ensure different modification times
        temp_file.write_text("content")
        
        # Create cache file
        cache_data = {
            'expected': {
                'video_codec': 'libx264',
                'audio_codec': 'aac',
                'resolution': '1920x1080',
                'duration': 15.0
            }
        }
        cache_file.write_text(json.dumps(cache_data))
        
        # Mock stream info to match expected
        mock_stream_info.return_value = {
            'video': {
                'codec': 'h264',
                'resolution': '1920x1080',
                'pix_fmt': 'yuv420p'
            },
            'audio': {
                'codec': 'aac',
                'sample_rate': '48000'
            }
        }
        
        # Mock ffprobe for duration check
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout='{"format": {"duration": "15.1"}}'
            )
            
            with patch('src.config.use_cache', True):
                current_cache = {'expected': cache_data['expected']}
                result = is_cached_file_valid(temp_file, str(source_file), current_cache)
                assert result is True
    
    def test_cache_validation_codec_mismatch(self, temp_dir):
        """Test cache validation with codec mismatch."""
        temp_file = temp_dir / "temp_0.mp4"
        cache_file = temp_dir / "temp_0.cache"
        source_file = temp_dir / "source.mp4"
        
        # Create files
        source_file.write_text("content")
        temp_file.write_text("content")
        
        cache_data = {
            'expected': {
                'video_codec': 'libx264',
                'resolution': '1920x1080'
            }
        }
        cache_file.write_text(json.dumps(cache_data))
        
        with patch('src.config.use_cache', True):
            # Different codec in current expected
            current_cache = {
                'expected': {
                    'video_codec': 'libx265',  # Different!
                    'resolution': '1920x1080'
                }
            }
            result = is_cached_file_valid(temp_file, str(source_file), current_cache)
            assert result is False

class TestSaveCacheInfo:
    """Test cache info saving."""
    
    def test_save_cache_info_success(self, temp_dir):
        """Test successful cache info saving."""
        temp_file = temp_dir / "temp_0.mp4"
        cache_file = temp_dir / "temp_0.cache"
        
        cache_data = {
            'command': 'ffmpeg -i input -o output',
            'expected': {'codec': 'h264'},
            'created': '2024-01-01 12:00:00'
        }
        
        with patch('src.config.use_cache', True):
            save_cache_info(temp_file, cache_data)
            
            assert cache_file.exists()
            saved_data = json.loads(cache_file.read_text())
            assert saved_data == cache_data
    
    def test_save_cache_info_disabled(self, temp_dir):
        """Test that cache info is not saved when cache disabled."""
        temp_file = temp_dir / "temp_0.mp4"
        cache_file = temp_dir / "temp_0.cache"
        
        cache_data = {'test': 'data'}
        
        with patch('src.config.use_cache', False):
            save_cache_info(temp_file, cache_data)
            
            assert not cache_file.exists()
    
    def test_save_cache_info_write_failure(self, temp_dir):
        """Test cache saving handles write failures gracefully."""
        temp_file = temp_dir / "temp_0.mp4"
        
        with patch('src.config.use_cache', True):
            with patch('builtins.open', side_effect=OSError("Permission denied")):
                # Should not raise exception
                save_cache_info(temp_file, {'test': 'data'})