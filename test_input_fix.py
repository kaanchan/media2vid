#!/usr/bin/env python3
"""
Test script to verify the sequential input fix for double entry issue.
This isolates the cleanup prompt behavior.
"""

import threading
import time
import sys
from colorama import Fore, Style, init

# Initialize colorama
init()

def get_user_input_with_timeout_cleanup() -> bool:
    """
    Handle cleanup prompt with 5-second timeout defaulting to preserve files.
    Uses sequential thread prevention to avoid double input issues.
    
    Returns:
        True if user wants to delete temp files, False otherwise (default)
    """
    import sys
    
    # Sequential input handling - prevent multiple competing threads
    input_result = [None]
    input_lock = threading.Lock()
    
    def get_single_input():
        """Single input handler using sys.stdin.readline() for better thread behavior."""
        try:
            user_input = sys.stdin.readline().strip().lower()
            input_result[0] = user_input
        except (EOFError, KeyboardInterrupt):
            input_result[0] = "n"
    
    def wait_for_input():
        """Ensure only one input thread exists at a time."""
        with input_lock:
            # Reset result and start new thread
            input_result[0] = None
            new_thread = threading.Thread(target=get_single_input, daemon=True, name="cleanup_input")
            new_thread.start()
            return new_thread
    
    print(f"{Fore.YELLOW}Delete temp directory and files? (y/N - defaults to N in 5 seconds): {Style.RESET_ALL}", end="", flush=True)
    
    # Start input thread
    input_thread = wait_for_input()
    
    # Wait up to 5 seconds for input
    start_time = time.time()
    while time.time() - start_time < 5.0:
        if input_result[0] is not None:
            response = input_result[0]
            print(f"\n{Fore.CYAN}Response: {response if response else 'n'}{Style.RESET_ALL}")
            return response in ['y', 'yes']
        time.sleep(0.1)
    
    print("n (timed out)")
    return False

def main():
    """Test the input function multiple times."""
    print("=== Testing Sequential Input Prevention ===")
    print("This should work with SINGLE Enter/N input (not double)")
    print()
    
    for i in range(3):
        print(f"\n--- Test {i+1}/3 ---")
        result = get_user_input_with_timeout_cleanup()
        print(f"Result: {'DELETE' if result else 'PRESERVE'}")
        
        # Small delay between tests
        time.sleep(0.5)
    
    print(f"\n{Fore.GREEN}All tests completed!{Style.RESET_ALL}")

if __name__ == "__main__":
    main()