"""
Async Helper Utilities

Reusable utilities for running async operations with timeouts.
Use via composition to add timeout support to any class.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


class AsyncRunner:
    """
    Helper for running async operations in sync context with timeout support.

    Usage (composition pattern):
        class MyAPI:
            def __init__(self):
                self._async = AsyncRunner()

            def get_data(self, timeout=5):
                async def _fetch():
                    return await some_async_operation()

                return self._async.run(_fetch(), timeout=timeout)
    """

    def __init__(self):
        self._loop = None

    def _get_loop(self):
        """Get or create event loop"""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop

    def run(self, coro, timeout=None):
        """
        Run async coroutine in sync context with optional timeout.

        Args:
            coro: Async coroutine to execute
            timeout: Timeout in seconds (None = no timeout)

        Returns:
            Result from coroutine

        Raises:
            asyncio.TimeoutError: If operation exceeds timeout
            Exception: Any exception raised by the coroutine

        Example:
            async def fetch_data():
                await asyncio.sleep(2)
                return "data"

            runner = AsyncRunner()
            result = runner.run(fetch_data(), timeout=5)  # Returns "data"
            result = runner.run(fetch_data(), timeout=1)  # Raises TimeoutError
        """
        loop = self._get_loop()

        if timeout:
            coro = asyncio.wait_for(coro, timeout=timeout)

        return loop.run_until_complete(coro)


# Convenience function for one-off usage
def run_async(coro, timeout=None):
    """
    Run async coroutine with optional timeout (convenience function).

    Args:
        coro: Async coroutine to execute
        timeout: Timeout in seconds (None = no timeout)

    Returns:
        Result from coroutine

    Raises:
        asyncio.TimeoutError: If operation exceeds timeout

    Example:
        async def my_operation():
            return await some_api_call()

        result = run_async(my_operation(), timeout=5)
    """
    runner = AsyncRunner()
    return runner.run(coro, timeout=timeout)


__all__ = ['AsyncRunner', 'run_async']
