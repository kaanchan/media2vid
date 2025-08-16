# Agent Instructions - Issue #19

**Agent Type:** cache-optimizer
**Branch:** agent/cache-optimizer-issue-19
**Issue:** https://github.com/kaanchan/media2vid/issues/19
**Title:** Cache invalidation: duration parameter changed despite no input changes

## Task
Fix cache invalidation logic where duration parameter changes are incorrectly triggering cache invalidation despite no actual input changes.

## Current Status: INITIALIZED
**Started:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")
**Agent ID:** agent-cache-optimizer-19

## Progress Log
- [x] Branch created
- [x] Analysis of cache validation logic
- [x] Identify root cause of false invalidation
- [x] Design improved cache key strategy
- [x] Implement cache validation fixes
- [x] Testing with various scenarios
- [ ] Performance impact validation
- [ ] PR created
- [ ] Issue resolved

## ⚡ SOLUTION IMPLEMENTED

### Key Changes Made:
1. **src/cache_system.py:108-113** - Use command duration directly instead of min() calculation
2. **src/cache_system.py:257-262** - Validate actual ≤ command duration with tolerance

### Fix Summary:
- **Before**: `duration = min(ffprobe_result, command_duration)` → non-deterministic
- **After**: `duration = command_duration` → deterministic cache keys
- **Validation**: Ensures actual duration ≤ command duration (respects min() in processing)

### Test Results:
✅ **Deterministic cache keys**: Same command produces identical cache parameters
✅ **No false invalidation**: Duration parameter changes no longer trigger unnecessary reprocessing

## ⚡ ROOT CAUSE IDENTIFIED

**File:** `src/cache_system.py` lines 104-123
**Issue:** Duration parameter calculation is inconsistent between runs

### The Problem:
Line 119: `expected_params['duration'] = min(source_duration, command_duration)`

When `-t` parameter is used, the cache system:
1. Gets source file duration via ffprobe (e.g., 45.673s)
2. Gets command duration from `-t` parameter (e.g., 15.0s)  
3. Uses `min(source_duration, command_duration)` = 15.0s

BUT: source_duration from ffprobe can vary slightly between runs due to:
- Floating point precision differences
- FFprobe timing variations 
- File system timestamp resolution

This causes cache invalidation even when no actual input changed!

## Focus Areas:
- Cache key generation logic
- File modification time validation
- Parameter comparison accuracy
- Duration parameter handling
