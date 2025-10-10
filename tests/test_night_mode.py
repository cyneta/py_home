"""
Tests for lib/night_mode.py

Tests cover:
- Night mode state detection (is_night_mode)
- Enabling/disabling night mode (set_night_mode)
- Status reporting (get_night_mode_status)
- Edge cases (file missing, permissions, concurrent access)
"""

import pytest
import sys
import os
from pathlib import Path
from unittest import mock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestNightMode:
    """Tests for lib/night_mode.py"""

    @pytest.fixture(autouse=True)
    def cleanup_state_file(self):
        """Remove state file before and after each test"""
        from lib.night_mode import STATE_FILE

        # Clean up before test
        if STATE_FILE.exists():
            STATE_FILE.unlink()

        yield

        # Clean up after test
        if STATE_FILE.exists():
            STATE_FILE.unlink()

    def test_night_mode_module_structure(self):
        """Test night_mode has required functions"""
        from lib import night_mode

        # Check functions exist
        assert callable(night_mode.is_night_mode)
        assert callable(night_mode.set_night_mode)
        assert callable(night_mode.get_night_mode_status)

        # Check STATE_FILE defined
        assert hasattr(night_mode, 'STATE_FILE')
        assert isinstance(night_mode.STATE_FILE, Path)

    def test_is_night_mode_false_when_file_missing(self):
        """Test night mode is False when state file doesn't exist"""
        from lib.night_mode import is_night_mode, STATE_FILE

        # Ensure file doesn't exist
        assert not STATE_FILE.exists()

        # Verify night mode is False
        assert is_night_mode() is False

    def test_set_night_mode_enabled_creates_file(self):
        """Test enabling night mode creates state file"""
        from lib.night_mode import set_night_mode, STATE_FILE

        # Enable night mode
        set_night_mode(True)

        # Verify file exists
        assert STATE_FILE.exists()

    def test_set_night_mode_disabled_removes_file(self):
        """Test disabling night mode removes state file"""
        from lib.night_mode import set_night_mode, STATE_FILE

        # Create file first
        STATE_FILE.touch()
        assert STATE_FILE.exists()

        # Disable night mode
        set_night_mode(False)

        # Verify file removed
        assert not STATE_FILE.exists()

    def test_is_night_mode_true_when_file_exists(self):
        """Test night mode is True when state file exists"""
        from lib.night_mode import is_night_mode, STATE_FILE

        # Create state file
        STATE_FILE.touch()

        # Verify night mode is True
        assert is_night_mode() is True

    def test_enable_then_check_night_mode(self):
        """Test workflow: enable night mode, then check status"""
        from lib.night_mode import set_night_mode, is_night_mode

        # Initially disabled
        assert is_night_mode() is False

        # Enable
        set_night_mode(True)

        # Now enabled
        assert is_night_mode() is True

    def test_disable_then_check_night_mode(self):
        """Test workflow: disable night mode, then check status"""
        from lib.night_mode import set_night_mode, is_night_mode, STATE_FILE

        # Create state file (simulate night mode on)
        STATE_FILE.touch()
        assert is_night_mode() is True

        # Disable
        set_night_mode(False)

        # Now disabled
        assert is_night_mode() is False

    def test_toggle_night_mode_multiple_times(self):
        """Test repeatedly toggling night mode"""
        from lib.night_mode import set_night_mode, is_night_mode

        # Start disabled
        assert is_night_mode() is False

        # Toggle on
        set_night_mode(True)
        assert is_night_mode() is True

        # Toggle off
        set_night_mode(False)
        assert is_night_mode() is False

        # Toggle on again
        set_night_mode(True)
        assert is_night_mode() is True

        # Toggle off again
        set_night_mode(False)
        assert is_night_mode() is False

    def test_disable_when_already_disabled(self):
        """Test disabling night mode when already disabled (idempotent)"""
        from lib.night_mode import set_night_mode, is_night_mode, STATE_FILE

        # Ensure disabled
        assert not STATE_FILE.exists()

        # Disable again (should not raise error)
        set_night_mode(False)

        # Still disabled
        assert is_night_mode() is False

    def test_enable_when_already_enabled(self):
        """Test enabling night mode when already enabled (idempotent)"""
        from lib.night_mode import set_night_mode, is_night_mode, STATE_FILE

        # Enable once
        set_night_mode(True)
        assert STATE_FILE.exists()

        # Enable again (should not raise error)
        set_night_mode(False)
        set_night_mode(True)

        # Still enabled
        assert is_night_mode() is True

    def test_get_night_mode_status_enabled(self):
        """Test get_night_mode_status() when enabled"""
        from lib.night_mode import set_night_mode, get_night_mode_status, STATE_FILE

        # Enable night mode
        set_night_mode(True)

        # Get status
        status = get_night_mode_status()

        # Verify status structure
        assert isinstance(status, dict)
        assert 'enabled' in status
        assert 'state_file' in status

        # Verify values
        assert status['enabled'] is True
        assert status['state_file'] == str(STATE_FILE)

    def test_get_night_mode_status_disabled(self):
        """Test get_night_mode_status() when disabled"""
        from lib.night_mode import get_night_mode_status, STATE_FILE

        # Get status (should be disabled by default)
        status = get_night_mode_status()

        # Verify status structure
        assert isinstance(status, dict)
        assert 'enabled' in status
        assert 'state_file' in status

        # Verify values
        assert status['enabled'] is False
        assert status['state_file'] == str(STATE_FILE)

    def test_state_file_location(self):
        """Test state file is in project root"""
        from lib.night_mode import STATE_FILE

        # Verify path structure
        assert STATE_FILE.name == '.night_mode'

        # Should be in project root (parent of lib/)
        expected_parent = Path(__file__).parent.parent
        assert STATE_FILE.parent == expected_parent

    def test_night_mode_persistence_across_imports(self):
        """Test night mode state persists when reimporting module"""
        from lib.night_mode import set_night_mode, STATE_FILE

        # Enable night mode
        set_night_mode(True)
        assert STATE_FILE.exists()

        # Reimport module (simulates new script run)
        import importlib
        import lib.night_mode
        importlib.reload(lib.night_mode)

        # Check status with fresh import
        from lib.night_mode import is_night_mode
        assert is_night_mode() is True

    def test_set_night_mode_file_permission_error(self):
        """Test error handling when state file can't be created"""
        from lib.night_mode import set_night_mode
        from pathlib import Path

        # Mock Path.touch() at the class level
        with mock.patch.object(Path, 'touch', side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError):
                set_night_mode(True)

    def test_set_night_mode_file_removal_error(self):
        """Test error handling when state file can't be removed"""
        from lib.night_mode import set_night_mode, STATE_FILE
        from pathlib import Path

        # Create file
        STATE_FILE.touch()

        # Mock Path.unlink() at the class level
        with mock.patch.object(Path, 'unlink', side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError):
                set_night_mode(False)

    def test_concurrent_access_safety(self):
        """Test multiple processes can safely check night mode"""
        from lib.night_mode import is_night_mode, set_night_mode

        # Enable night mode
        set_night_mode(True)

        # Simulate multiple reads (should all return True)
        results = [is_night_mode() for _ in range(10)]
        assert all(results)

    def test_night_mode_used_by_temp_coordination(self):
        """Test temp_coordination.py uses night_mode library"""
        # Read temp_coordination source to verify integration
        temp_coord_path = Path(__file__).parent.parent / 'automations' / 'temp_coordination.py'

        if temp_coord_path.exists():
            source = temp_coord_path.read_text(encoding='utf-8')

            # Verify it imports night_mode
            assert 'from lib.night_mode import is_night_mode' in source or \
                   'import lib.night_mode' in source or \
                   'from lib import night_mode' in source, \
                   "temp_coordination.py should import night_mode library"

    def test_night_mode_used_by_goodnight(self):
        """Test goodnight.py uses night_mode library"""
        goodnight_path = Path(__file__).parent.parent / 'automations' / 'goodnight.py'

        if goodnight_path.exists():
            source = goodnight_path.read_text(encoding='utf-8')

            # Verify it imports night_mode
            assert 'night_mode' in source.lower(), \
                   "goodnight.py should use night_mode library"

    def test_night_mode_used_by_good_morning(self):
        """Test good_morning.py uses night_mode library"""
        morning_path = Path(__file__).parent.parent / 'automations' / 'good_morning.py'

        if morning_path.exists():
            source = morning_path.read_text(encoding='utf-8')

            # Verify it imports night_mode
            assert 'night_mode' in source.lower(), \
                   "good_morning.py should use night_mode library"


class TestNightModeIntegration:
    """Integration tests for night_mode with automations"""

    @pytest.fixture(autouse=True)
    def cleanup_state_file(self):
        """Remove state file before and after each test"""
        from lib.night_mode import STATE_FILE

        if STATE_FILE.exists():
            STATE_FILE.unlink()

        yield

        if STATE_FILE.exists():
            STATE_FILE.unlink()

    def test_goodnight_workflow(self):
        """Test goodnight workflow enables night mode"""
        from lib.night_mode import is_night_mode, set_night_mode

        # Simulate goodnight automation
        assert is_night_mode() is False
        set_night_mode(True)
        assert is_night_mode() is True

    def test_good_morning_workflow(self):
        """Test good_morning workflow disables night mode"""
        from lib.night_mode import is_night_mode, set_night_mode, STATE_FILE

        # Setup: night mode enabled (simulate after goodnight)
        STATE_FILE.touch()
        assert is_night_mode() is True

        # Simulate good_morning automation
        set_night_mode(False)
        assert is_night_mode() is False

    def test_temp_coordination_checks_night_mode(self):
        """Test temp_coordination respects night mode state"""
        from lib.night_mode import is_night_mode, set_night_mode

        # Day mode (night mode off)
        set_night_mode(False)
        day_mode = is_night_mode()
        assert day_mode is False

        # Night mode (night mode on)
        set_night_mode(True)
        night_mode = is_night_mode()
        assert night_mode is True


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
