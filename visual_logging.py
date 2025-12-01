"""
Visual logging utilities for test output with colors and symbols.

Provides three layers of functionality:
1. Core ANSI colors and logging functions (no dependencies)
2. Optional Rich library integration (auto-detected)
3. Structured test result reporting

Usage Examples:
    # Simple logging (like StabilityTestSuite)
    from test_suite_framework.utils import visual_logging as vlog
    vlog.log_pass("Test passed successfully")
    vlog.log_fail("Test failed with error")

    # Structured results (like py_home)
    result = vlog.TestResult(name="Test 1", status="pass", duration=1.5)
    vlog.print_result(result)

    # Batch reporting
    results = [result1, result2, result3]
    vlog.print_summary(results)
"""

from typing import Dict, List, Optional
import sys

# ==============================================================================
# Layer 1: Core ANSI Colors (No Dependencies)
# ==============================================================================

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'
RESET = '\033[0m'

# Unicode symbols for visual scanning
SYMBOL_PASS = '✓'
SYMBOL_FAIL = '✗'
SYMBOL_SKIP = '○'
SYMBOL_WARNING = '⚠'

# ==============================================================================
# Layer 2: Optional Rich Integration
# ==============================================================================

try:
    from rich.console import Console
    _rich_console = Console()
    _has_rich = True
except ImportError:
    _rich_console = None
    _has_rich = False


def has_rich() -> bool:
    """Check if Rich library is available."""
    return _has_rich


def get_console():
    """Get Rich console if available, otherwise None."""
    return _rich_console


# ==============================================================================
# Core Logging Functions
# ==============================================================================

def log_pass(msg: str):
    """Log a passing test with green [PASS] prefix."""
    print(f"{GREEN}[PASS]{RESET} {msg}")


def log_fail(msg: str):
    """Log a failing test with red [FAIL] prefix."""
    print(f"{RED}[FAIL]{RESET} {msg}")


def log_info(msg: str):
    """Log informational message with blue [INFO] prefix."""
    print(f"{BLUE}[INFO]{RESET} {msg}")


def log_skip(msg: str):
    """Log a skipped test with yellow [SKIP] prefix."""
    print(f"{YELLOW}[SKIP]{RESET} {msg}")


def log_error(msg: str):
    """Log an error with red [ERROR] prefix."""
    print(f"{RED}[ERROR]{RESET} {msg}")


def log_warning(msg: str):
    """Log a warning with yellow [WARN] prefix."""
    print(f"{YELLOW}[WARN]{RESET} {msg}")


def log_header(msg: str):
    """Log a header with cyan color."""
    print(f"{CYAN}{msg}{RESET}")


def log_section(msg: str):
    """Log a section header with blue color."""
    print(f"{BLUE}{msg}{RESET}")


# ==============================================================================
# TestResult Class (from py_home)
# ==============================================================================

class TestResult:
    """Store results for a test with optional details and duration tracking.

    Attributes:
        name: Test name or description
        status: Test status ('pass', 'fail', 'skip')
        message: Optional message providing additional context
        details: Optional dictionary of additional details
        duration: Test execution time in seconds (0 if not timed)
    """

    def __init__(
        self,
        name: str,
        status: str,
        message: str = "",
        details: Optional[Dict] = None,
        duration: float = 0
    ):
        self.name = name
        self.status = status  # 'pass', 'fail', 'skip'
        self.message = message
        self.details = details or {}
        self.duration = duration

    @property
    def passed(self) -> bool:
        """Check if test passed."""
        return self.status == 'pass'

    @property
    def failed(self) -> bool:
        """Check if test failed."""
        return self.status == 'fail'

    @property
    def skipped(self) -> bool:
        """Check if test was skipped."""
        return self.status == 'skip'


# ==============================================================================
# Layer 3: Utility Functions
# ==============================================================================

def print_header(text: str, width: int = 70):
    """Print a formatted section header with border.

    Args:
        text: Header text to display
        width: Width of the header border (default: 70)
    """
    print(f"\n{BLUE}{'='*width}")
    print(f"{text}")
    print(f"{'='*width}{RESET}\n")


def print_result(result: TestResult):
    """Print a formatted test result with symbol, status, and details.

    Args:
        result: TestResult object to display
    """
    if result.status == 'pass':
        status = f"{GREEN}{SYMBOL_PASS} PASS{RESET}"
    elif result.status == 'skip':
        status = f"{YELLOW}{SYMBOL_SKIP} SKIP{RESET}"
    else:
        status = f"{RED}{SYMBOL_FAIL} FAIL{RESET}"

    duration_str = f" ({result.duration:.2f}s)" if result.duration > 0 else ""
    print(f"{status} {result.name}{duration_str}")

    if result.message:
        print(f"  {result.message}")
    if result.details:
        for key, value in result.details.items():
            print(f"    {key}: {value}")


def print_summary(results: List[TestResult], show_details: bool = False):
    """Print a summary of test results with pass/fail/skip counts.

    Args:
        results: List of TestResult objects
        show_details: If True, print each individual result before summary
    """
    if show_details:
        for result in results:
            print_result(result)
        print()  # Blank line before summary

    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if r.failed)
    skipped = sum(1 for r in results if r.skipped)
    total = len(results)

    total_duration = sum(r.duration for r in results)

    print_header("Test Summary")
    print(f"{GREEN}{SYMBOL_PASS} Passed:  {passed}/{total}{RESET}")
    print(f"{RED}{SYMBOL_FAIL} Failed:  {failed}/{total}{RESET}")
    print(f"{YELLOW}{SYMBOL_SKIP} Skipped: {skipped}/{total}{RESET}")

    if total_duration > 0:
        print(f"\nTotal duration: {total_duration:.2f}s")

    # Return success if all tests passed or were skipped
    return failed == 0


# ==============================================================================
# Backwards Compatibility
# ==============================================================================

class Colors:
    """Backwards compatibility class for code using Colors.GREEN syntax."""
    GREEN = GREEN
    RED = RED
    BLUE = BLUE
    YELLOW = YELLOW
    CYAN = CYAN
    MAGENTA = MAGENTA
    RESET = RESET
