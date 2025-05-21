"""
Signal handling utilities for graceful shutdowns.

This module provides a context manager for handling system signals (like SIGINT, SIGTERM)
in a way that ensures resources are properly cleaned up.
"""
import signal
import sys
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union

# Type variable for the cleanup function
CleanupFunc = Callable[[], None]

class SignalHandler:
    """Handle system signals for graceful shutdown."""
    
    def __init__(self):
        """Initialize the signal handler with default signal handlers."""
        self._original_handlers: Dict[int, Any] = {}
        self._cleanup_functions: List[CleanupFunc] = []
        self._registered = False
        
    def register(self) -> None:
        """Register the signal handlers."""
        if self._registered:
            return
            
        # Handle common interrupt signals
        signals = [signal.SIGINT]  # Ctrl+C
        if hasattr(signal, 'SIGBREAK'):
            signals.append(signal.SIGBREAK)  # Windows console close
        if hasattr(signal, 'SIGTERM'):
            signals.append(signal.SIGTERM)   # Termination signal
            
        for sig in signals:
            self._original_handlers[sig] = signal.getsignal(sig)
            signal.signal(sig, self._handle_signal)
            
        self._registered = True
        
    def unregister(self) -> None:
        """Restore original signal handlers."""
        if not self._registered:
            return
            
        for sig, handler in self._original_handlers.items():
            if callable(handler) or handler in (signal.SIG_IGN, signal.SIG_DFL):
                signal.signal(sig, handler if handler is not None else signal.SIG_DFL)
                
        self._original_handlers.clear()
        self._registered = False
        
    def add_cleanup(self, func: CleanupFunc) -> None:
        """Add a cleanup function to be called on shutdown."""
        if func not in self._cleanup_functions:
            self._cleanup_functions.append(func)
    
    def remove_cleanup(self, func: CleanupFunc) -> None:
        """Remove a cleanup function."""
        if func in self._cleanup_functions:
            self._cleanup_functions.remove(func)
    
    def _handle_signal(self, signum: int, frame) -> None:
        """Handle received signals by running cleanup functions."""
        print(f"\nReceived signal {signal.Signals(signum).name}. Cleaning up...")
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self) -> None:
        """Run all registered cleanup functions in reverse order."""
        for func in reversed(self._cleanup_functions):
            try:
                func()
            except Exception as e:
                print(f"Error during cleanup: {e}", file=sys.stderr)
        self.unregister()

# Global signal handler instance
_signal_handler = SignalHandler()

@contextmanager
def signal_handling(cleanup_func: Optional[CleanupFunc] = None):
    """Context manager for handling signals with optional cleanup function.
    
    Args:
        cleanup_func: Optional function to call on cleanup
        
    Yields:
        The signal handler instance
    """
    _signal_handler.register()
    if cleanup_func:
        _signal_handler.add_cleanup(cleanup_func)
        
    try:
        yield _signal_handler
    finally:
        if cleanup_func:
            _signal_handler.remove_cleanup(cleanup_func)
        _signal_handler.unregister()

def register_cleanup(cleanup_func: CleanupFunc) -> None:
    """Register a cleanup function with the global signal handler."""
    _signal_handler.add_cleanup(cleanup_func)

def unregister_cleanup(cleanup_func: CleanupFunc) -> None:
    """Unregister a cleanup function from the global signal handler."""
    _signal_handler.remove_cleanup(cleanup_func)
