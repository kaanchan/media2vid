# Agent Instructions - Issue #18

**Agent Type:** menu-refactor
**Branch:** agent/menu-refactor-issue-18
**Issue:** https://github.com/kaanchan/media2vid/issues/18
**Title:** Refactor: Create reusable input+countdown function

## Task
Create a unified function for input prompts with countdown timers to replace multiple similar implementations throughout the codebase.

## Current Status: INITIALIZED
**Started:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")
**Agent ID:** agent-menu-refactor-18

## Progress Log
- [x] Branch created
- [ ] Analysis of existing input functions complete
- [ ] Design reusable function signature
- [ ] Implement unified input function
- [ ] Replace existing implementations
- [ ] Testing completed
- [ ] PR created
- [ ] Issue resolved

## Current Implementations to Replace:
- get_user_input_with_timeout_cleanup() - cleanup prompt
- get_overwrite_confirmation() - file overwrite prompt  
- get_user_action() - main menu with complex countdown logic

## Target Function Signature:
```python
def get_input_with_countdown(
    prompt_text: str,
    countdown_time: int = 5,
    accepted_keys: List[str] = None,
    default_response: str = None
) -> Tuple[str, bool]:
    """
    Returns: (user_input, timed_out)
    """
```
