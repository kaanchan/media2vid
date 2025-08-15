# media2vid Testing Guide

> **Version:** feature/modularize-codebase branch (post-v31)  
> **Last Updated:** August 2025  
> **Commit:** 2f843b9 - Update test suite for enhanced functionality compatibility  
> **Test Status:** 78/78 tests passing (100% pass rate)

## Overview

This document describes the comprehensive test suite for media2vid, including available tests, how to run them, and how to interpret results. The test suite ensures reliability, compatibility, and regression prevention across all functionality.

## Test Structure

### Test Organization

```
tests/
├── __init__.py
├── conftest.py              # Pytest configuration and fixtures
├── requirements.txt         # Test dependencies
├── test_cache_system.py     # Cache validation and management tests
├── test_ffmpeg_utils.py     # FFmpeg operations and utilities tests  
├── test_file_utils.py       # File discovery and management tests
└── test_processing_functions.py  # Media processing workflow tests
```

### Test Coverage Summary

| Module | Test File | Test Count | Coverage |
|--------|-----------|------------|----------|
| Cache System | `test_cache_system.py` | 16 tests | Cache validation, info storage, normalization |
| FFmpeg Utils | `test_ffmpeg_utils.py` | 21 tests | Command building, stream info, error handling |
| File Utils | `test_file_utils.py` | 23 tests | File discovery, categorization, sorting |
| Processing Functions | `test_processing_functions.py` | 18 tests | Video, audio, intro processing workflows |
| **Total** | **4 test files** | **78 tests** | **100% pass rate** |

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Dependencies include:
# - pytest>=7.0.0
# - pytest-mock>=3.6.1
# - pytest-cov>=4.0.0
```

### Basic Test Execution

```bash
# Run all tests
python -m pytest tests/

# Run with verbose output
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_cache_system.py

# Run specific test class
python -m pytest tests/test_file_utils.py::TestExtractPersonName

# Run specific test function
python -m pytest tests/test_ffmpeg_utils.py::TestGetStreamInfo::test_get_stream_info_success
```

### Test Output Options

```bash
# Short format (default)
python -m pytest tests/ --tb=short

# Show full traceback on failures
python -m pytest tests/ --tb=long

# Stop on first failure
python -m pytest tests/ -x

# Show test durations
python -m pytest tests/ --durations=10

# Generate coverage report
python -m pytest tests/ --cov=src --cov-report=html
```

### Quick Test Script

Use the included test runner:

```bash
# Run all tests with summary
python run_tests.py

# The script provides:
# - Quick pass/fail summary
# - Failed test details
# - Performance timing
# - Coverage information
```

## Test Categories

### 1. Cache System Tests (`test_cache_system.py`)

Tests the intelligent caching system that avoids reprocessing unchanged files.

#### Key Test Classes:

**`TestNormalizeCodecName`** - Codec name normalization
```bash
python -m pytest tests/test_cache_system.py::TestNormalizeCodecName -v
```
- Tests video codec mapping (libx264 → h264, h264_nvenc → h264)
- Tests audio codec mapping (libfdk_aac → aac, libmp3lame → mp3)
- Tests case insensitive handling
- Tests unknown codec passthrough

**`TestGetCacheInfo`** - Cache information generation
```bash
python -m pytest tests/test_cache_system.py::TestGetCacheInfo -v
```
- Tests FFmpeg command parameter extraction
- Tests video/audio filter parsing
- Tests duration calculation from source files
- Tests fallback behavior when ffprobe fails

**`TestIsCachedFileValid`** - Cache validation logic
```bash
python -m pytest tests/test_cache_system.py::TestIsCachedFileValid -v
```
- Tests modification time comparison
- Tests parameter matching against stored cache
- Tests cache disabled scenarios
- Tests file existence validation

**`TestSaveCacheInfo`** - Cache persistence
```bash
python -m pytest tests/test_cache_system.py::TestSaveCacheInfo -v
```
- Tests JSON cache file creation
- Tests cache disabled behavior
- Tests write failure handling

### 2. FFmpeg Utils Tests (`test_ffmpeg_utils.py`)

Tests FFmpeg command construction, stream analysis, and error handling.

#### Key Test Classes:

**`TestBuildBaseFfmpegCmd`** - Command construction
```bash
python -m pytest tests/test_ffmpeg_utils.py::TestBuildBaseFfmpegCmd -v
```
- Tests default command parameters
- Tests custom duration handling
- Tests GPU vs CPU encoding options
- Tests required parameter inclusion

**`TestGetVideoFilter` / `TestGetAudioFilter`** - Filter chains
```bash
python -m pytest tests/test_ffmpeg_utils.py::TestGetVideoFilter -v
python -m pytest tests/test_ffmpeg_utils.py::TestGetAudioFilter -v
```
- Tests video filter components (scale, pad, fps)
- Tests audio filter components (resample, loudnorm)
- Tests filter format validation

**`TestGetStreamInfo`** - Media analysis
```bash
python -m pytest tests/test_ffmpeg_utils.py::TestGetStreamInfo -v
```
- Tests video stream parsing (codec, resolution, fps)
- Tests audio stream parsing (codec, sample rate, channels)
- Tests FPS calculation from r_frame_rate
- Tests edge cases (video-only, audio-only, invalid files)

**`TestRunFfmpegWithErrorHandling`** - Command execution
```bash
python -m pytest tests/test_ffmpeg_utils.py::TestRunFfmpegWithErrorHandling -v
```
- Tests successful FFmpeg execution
- Tests cache hit scenarios
- Tests failure handling and cleanup
- Tests different file types (VIDEO, AUDIO, CONCAT)

### 3. File Utils Tests (`test_file_utils.py`)

Tests file discovery, categorization, and utility functions.

#### Key Test Classes:

**`TestExtractPersonName`** - Name extraction logic
```bash
python -m pytest tests/test_file_utils.py::TestExtractPersonName -v
```
- Tests " - PersonName.ext" pattern extraction
- Tests fallback to full filename
- Tests edge cases (empty names, multiple dashes)

**`TestIsTempFile`** - File filtering
```bash
python -m pytest tests/test_file_utils.py::TestIsTempFile -v
```
- Tests temp file exclusion (temp_*.mp4)
- Tests previous output exclusion (*-MERGED-*)
- Tests system file exclusion (.hidden, ~backup)
- Tests valid file inclusion

**`TestCategorizeMediaFiles`** - File categorization
```bash
python -m pytest tests/test_file_utils.py::TestCategorizeMediaFiles -v
```
- Tests video/audio/intro/ignored categorization
- Tests sorting by person name
- Tests extension case handling

**`TestParseRange` / `TestFormatRangeIndicator`** - Range processing
```bash
python -m pytest tests/test_file_utils.py::TestParseRange -v
python -m pytest tests/test_file_utils.py::TestFormatRangeIndicator -v
```
- Tests range parsing (1,3,5-7, 3-, etc.)
- Tests boundary validation and clamping
- Tests range indicator formatting (M1_5, R3,7,9)

### 4. Processing Functions Tests (`test_processing_functions.py`)

Tests the core media processing workflows.

#### Key Test Classes:

**`TestProcessIntroFile`** - PNG to video conversion
```bash
python -m pytest tests/test_processing_functions.py::TestProcessIntroFile -v
```
- Tests intro slide processing with silent audio
- Tests custom duration handling
- Tests failure scenarios and error handling

**`TestProcessAudioFile`** - Audio to video with visualization
```bash
python -m pytest tests/test_processing_functions.py::TestProcessAudioFile -v
```
- Tests waveform visualization generation
- Tests background image integration
- Tests fallback to black background
- Tests text overlay ("Audio only submission")

**`TestProcessVideoFile`** - Video standardization
```bash
python -m pytest tests/test_processing_functions.py::TestProcessVideoFile -v
```
- Tests video filter application
- Tests audio filter application
- Tests standardization to 1920x1080@30fps

**`TestFindAudioBackground`** - Background search logic
```bash
python -m pytest tests/test_processing_functions.py::TestFindAudioBackground -v
```
- Tests same-name PNG priority
- Tests audio_background.png fallback
- Tests custom background path priority
- Tests case-insensitive matching

## Test Fixtures and Utilities

### Available Fixtures (`conftest.py`)

```python
# Temporary directory for test files
def test_some_function(temp_dir):
    test_file = temp_dir / "test.mp4"
    test_file.touch()

# Mock INPUT directory with test files
def test_file_discovery(mock_input_dir):
    (mock_input_dir / "video.mp4").touch()
    (mock_input_dir / "audio.m4a").touch()
```

### Mocking Patterns

The test suite uses extensive mocking to avoid external dependencies:

```python
# Mock subprocess calls
@patch('subprocess.run')
def test_ffmpeg_execution(mock_run):
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

# Mock file system operations  
@patch('pathlib.Path.exists')
def test_file_validation(mock_exists):
    mock_exists.return_value = True

# Mock print functions to avoid encoding issues
@patch('builtins.print')
def test_output_functions(mock_print):
    # Test without actual console output
```

## Interpreting Test Results

### Success Indicators

```
============================= test session starts =============================
...
tests/test_cache_system.py ................                              [ 20%]
tests/test_ffmpeg_utils.py .....................                         [ 47%]
tests/test_file_utils.py .......................                         [ 76%]
tests/test_processing_functions.py ..................                    [100%]

============================= 78 passed in 0.29s ==============================
```

- **Dots (.)** = Passing tests
- **F** = Failed tests
- **E** = Error in test execution
- **x** = Expected failure (xfail)
- **s** = Skipped tests

### Failure Analysis

When tests fail, pytest provides detailed information:

```
================================== FAILURES ===================================
________________________ TestGetStreamInfo.test_fps_parsing ________________________

def test_fps_parsing(self):
>       assert result['video']['fps'] == "30.0"
E       AssertionError: assert '0.0' != '30.0'
E         
E         - 30.0
E         + 0.0

tests/test_ffmpeg_utils.py:252: AssertionError
```

**Common Failure Types:**
- **Assertion errors** - Expected vs actual value mismatches
- **Mock call errors** - Incorrect function call patterns
- **Import errors** - Missing dependencies or module issues
- **Timeout errors** - Tests taking too long (usually external calls)

### Performance Monitoring

```bash
# Show slowest tests
python -m pytest tests/ --durations=10

# Profile test execution
python -m pytest tests/ --profile

# Memory usage monitoring  
python -m pytest tests/ --memray
```

## Coverage Analysis

### Generate Coverage Reports

```bash
# Terminal coverage report
python -m pytest tests/ --cov=src

# HTML coverage report
python -m pytest tests/ --cov=src --cov-report=html

# Coverage with missing lines
python -m pytest tests/ --cov=src --cov-report=term-missing
```

### Coverage Targets

| Module | Current Coverage | Target |
|--------|------------------|---------|
| src/cache_system.py | ~95% | 90%+ |
| src/ffmpeg_utils.py | ~90% | 85%+ |
| src/file_utils.py | ~98% | 95%+ |
| src/processors/*.py | ~85% | 80%+ |
| **Overall** | **~92%** | **85%+** |

## Adding New Tests

### Test Naming Convention

```python
class TestNewFeature:
    """Test new feature functionality."""
    
    def test_new_feature_basic_case(self):
        """Test basic functionality works."""
        
    def test_new_feature_edge_case(self):
        """Test edge case handling."""
        
    def test_new_feature_error_case(self):
        """Test error scenarios."""
```

### Test Structure Template

```python
import pytest
from unittest.mock import patch, Mock
from src.module import function_to_test

class TestNewFunction:
    """Test new function."""
    
    def test_success_case(self):
        """Test successful execution."""
        result = function_to_test("valid_input")
        assert result == "expected_output"
    
    @patch('src.module.external_dependency')
    def test_with_mocking(self, mock_dependency):
        """Test with external dependencies mocked."""
        mock_dependency.return_value = "mocked_value"
        result = function_to_test("input")
        assert result == "expected"
        mock_dependency.assert_called_once_with("input")
    
    def test_error_handling(self):
        """Test error scenarios."""
        with pytest.raises(SpecificError):
            function_to_test("invalid_input")
```

## Continuous Integration

### Test Automation

The test suite is designed for CI/CD integration:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    python -m pytest tests/ --junitxml=test-results.xml
    
- name: Upload coverage
  run: |
    python -m pytest tests/ --cov=src --cov-report=xml
```

### Quality Gates

- **Minimum pass rate:** 100% (all tests must pass)
- **Coverage threshold:** 85% overall coverage
- **Performance:** Tests complete within 60 seconds
- **No external dependencies:** All external calls mocked

## Troubleshooting Tests

### Common Issues

1. **Import errors** - Check PYTHONPATH and module structure
2. **Mock assertion failures** - Verify call patterns match implementation
3. **Timing issues** - Use proper fixtures for file creation timing
4. **Platform differences** - Use Path objects for cross-platform compatibility

### Debug Mode

```bash
# Run tests with debug output
python -m pytest tests/ -s -vv --tb=long

# Drop into debugger on failure
python -m pytest tests/ --pdb

# Run specific test with debug
python -m pytest tests/test_file_utils.py::TestExtractPersonName::test_edge_cases -s -vv
```

The comprehensive test suite ensures media2vid maintains high quality and reliability across all functionality, with detailed coverage of core processing, error handling, and edge cases.