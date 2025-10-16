"""
Tests for HVAC Sleep Time Integration

These tests verify that automations use the new time-based sleep detection APIs
instead of the deprecated night_mode flag system.

Tests cover:
- goodnight.py uses set_sleep_mode() API
- good_morning.py uses set_comfort_mode() API
"""

import pytest
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestHVACSleepTimeIntegration:
    """Tests for HVAC sleep time integration with automations"""

    def test_goodnight_uses_sleep_mode_api(self):
        """Test goodnight.py uses sleep transition API"""
        goodnight_path = Path(__file__).parent.parent / 'automations' / 'goodnight.py'

        if goodnight_path.exists():
            source = goodnight_path.read_text(encoding='utf-8')

            # Verify it uses the new transition layer (which calls set_sleep_mode internally)
            assert 'transition_to_sleep' in source, \
                   "goodnight.py should use transition_to_sleep() API"

    def test_good_morning_uses_comfort_mode_api(self):
        """Test good_morning.py uses wake transition API"""
        morning_path = Path(__file__).parent.parent / 'automations' / 'good_morning.py'

        if morning_path.exists():
            source = morning_path.read_text(encoding='utf-8')

            # Verify it uses the new transition layer (which calls set_comfort_mode internally)
            assert 'transition_to_wake' in source, \
                   "good_morning.py should use transition_to_wake() API"


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
