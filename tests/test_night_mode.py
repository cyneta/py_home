"""
Tests for HVAC Sleep Time Integration

These tests verify that automations use the new time-based sleep detection
(is_sleep_time from lib.hvac_logic) instead of the deprecated night_mode flag system.

Tests cover:
- temp_coordination.py uses is_sleep_time()
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

    def test_temp_coordination_uses_sleep_time_logic(self):
        """Test temp_coordination.py uses sleep time logic"""
        # Read temp_coordination source to verify integration
        temp_coord_path = Path(__file__).parent.parent / 'automations' / 'temp_coordination.py'

        if temp_coord_path.exists():
            source = temp_coord_path.read_text(encoding='utf-8')

            # Verify it imports is_sleep_time from hvac_logic (new architecture)
            assert 'from lib.hvac_logic import is_sleep_time' in source or \
                   'import lib.hvac_logic' in source, \
                   "temp_coordination.py should import is_sleep_time from lib.hvac_logic"

    def test_goodnight_uses_sleep_mode_api(self):
        """Test goodnight.py uses sleep mode API"""
        goodnight_path = Path(__file__).parent.parent / 'automations' / 'goodnight.py'

        if goodnight_path.exists():
            source = goodnight_path.read_text(encoding='utf-8')

            # Verify it uses the new sleep mode API
            assert 'set_sleep_mode' in source, \
                   "goodnight.py should use set_sleep_mode() API"

    def test_good_morning_uses_comfort_mode_api(self):
        """Test good_morning.py uses comfort mode API"""
        morning_path = Path(__file__).parent.parent / 'automations' / 'good_morning.py'

        if morning_path.exists():
            source = morning_path.read_text(encoding='utf-8')

            # Verify it uses the new comfort mode API (exits sleep mode)
            assert 'set_comfort_mode' in source, \
                   "good_morning.py should use set_comfort_mode() API"


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
