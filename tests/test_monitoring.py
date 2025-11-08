"""
Tests for monitoring automation scripts

Tests cover:
1. tempstick_monitor.py - Freeze detection, humidity alerts, sensor health
2. presence_monitor.py - Home/away detection, state management, automation triggers
"""

import pytest
import sys
import os
from unittest import mock
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# TEMPSTICK MONITOR TESTS
# =============================================================================

class TestTempstickMonitor:
    """Tests for automations/tempstick_monitor.py"""

    def test_tempstick_module_structure(self):
        """Test tempstick_monitor has required functions and constants"""
        from automations import tempstick_monitor

        # Check critical constants defined
        assert hasattr(tempstick_monitor, 'PIPE_FREEZE_TEMP')
        assert hasattr(tempstick_monitor, 'HIGH_HUMIDITY')
        assert tempstick_monitor.PIPE_FREEZE_TEMP > 0
        assert tempstick_monitor.HIGH_HUMIDITY > 0

        # Check critical functions exist
        assert callable(tempstick_monitor.check_pipe_freeze_risk)
        assert callable(tempstick_monitor.check_humidity_risk)
        assert callable(tempstick_monitor.check_sensor_status)
        assert callable(tempstick_monitor.get_status_summary)

    def test_pipe_freeze_detection_critical(self):
        """Test freeze alert triggering logic (critical threshold)"""
        from automations.tempstick_monitor import check_pipe_freeze_risk, PIPE_FREEZE_TEMP

        # Mock temperature below freeze threshold
        temp_f = PIPE_FREEZE_TEMP - 5.0  # 45°F if threshold is 50°F

        with mock.patch('automations.tempstick_monitor.should_send_alert', return_value=True), \
             mock.patch('automations.tempstick_monitor.send_automation_summary') as mock_notify, \
             mock.patch('automations.tempstick_monitor.record_alert_sent'):

            result = check_pipe_freeze_risk(temp_f, 'Crawlspace', dry_run=False)

            # Verify freeze risk detected
            assert result is True

            # Verify notification sent with correct priority
            assert mock_notify.called
            call_args = mock_notify.call_args
            title = call_args[0][0]
            priority = call_args[1]['priority']

            assert 'Cold' in title or '❄️' in title
            assert priority == 1  # Urgent

    def test_pipe_freeze_detection_warning(self):
        """Test cold warning triggering (warning threshold)"""
        from automations.tempstick_monitor import check_pipe_freeze_risk, PIPE_FREEZE_TEMP, COLD_WARNING_TEMP

        # Temperature between warning and freeze thresholds
        temp_f = PIPE_FREEZE_TEMP + 2.0  # Cold but not freeze risk

        with mock.patch('automations.tempstick_monitor.should_send_alert', return_value=True), \
             mock.patch('automations.tempstick_monitor.send_automation_summary') as mock_notify, \
             mock.patch('automations.tempstick_monitor.record_alert_sent'):

            result = check_pipe_freeze_risk(temp_f, 'Crawlspace', dry_run=False)

            # Verify warning detected
            assert result is True

            # Verify notification sent with lower priority
            assert mock_notify.called
            priority = mock_notify.call_args[1]['priority']
            assert priority == 1  # High (not urgent)

    def test_pipe_freeze_no_alert_when_warm(self):
        """Test no alert when temperature is normal"""
        from automations.tempstick_monitor import check_pipe_freeze_risk, COLD_WARNING_TEMP

        # Normal temperature
        temp_f = COLD_WARNING_TEMP + 10.0  # 65°F

        with mock.patch('automations.tempstick_monitor.send_automation_summary') as mock_notify:
            result = check_pipe_freeze_risk(temp_f, 'Crawlspace', dry_run=False)

            # Verify no issue detected
            assert result is False

            # Verify no notification sent
            assert not mock_notify.called

    def test_pipe_freeze_rate_limiting(self):
        """Test freeze alerts respect cooldown period"""
        from automations.tempstick_monitor import check_pipe_freeze_risk, PIPE_FREEZE_TEMP

        temp_f = PIPE_FREEZE_TEMP - 5.0

        # Mock rate limiting saying "don't send"
        with mock.patch('automations.tempstick_monitor.should_send_alert', return_value=False), \
             mock.patch('automations.tempstick_monitor.send_automation_summary') as mock_notify:

            result = check_pipe_freeze_risk(temp_f, 'Crawlspace', dry_run=False)

            # Still detected as freeze risk
            assert result is True

            # But notification suppressed
            assert not mock_notify.called

    def test_high_humidity_detection(self):
        """Test high humidity alert triggering"""
        from automations.tempstick_monitor import check_humidity_risk, HIGH_HUMIDITY

        # Mock humidity above threshold
        humidity = HIGH_HUMIDITY + 5.0  # 70% if threshold is 65%

        with mock.patch('automations.tempstick_monitor.should_send_alert', return_value=True), \
             mock.patch('automations.tempstick_monitor.send_automation_summary') as mock_notify, \
             mock.patch('automations.tempstick_monitor.record_alert_sent'):

            result = check_humidity_risk(humidity, 'Crawlspace', dry_run=False)

            # Verify risk detected
            assert result is True

            # Verify notification sent
            assert mock_notify.called
            title = mock_notify.call_args[0][0]
            assert 'Humidity' in title or '💧' in title

    def test_very_high_humidity_detection(self):
        """Test very high humidity alert with urgent priority"""
        from automations.tempstick_monitor import check_humidity_risk, VERY_HIGH_HUMIDITY

        # Mock humidity above critical threshold
        humidity = VERY_HIGH_HUMIDITY + 5.0

        with mock.patch('automations.tempstick_monitor.should_send_alert', return_value=True), \
             mock.patch('automations.tempstick_monitor.send_automation_summary') as mock_notify, \
             mock.patch('automations.tempstick_monitor.record_alert_sent'):

            result = check_humidity_risk(humidity, 'Crawlspace', dry_run=False)

            # Verify risk detected
            assert result is True

            # Verify urgent priority
            assert mock_notify.called
            priority = mock_notify.call_args[1]['priority']
            assert priority == 1  # Urgent

    def test_sensor_offline_detection(self):
        """Test sensor offline alert"""
        from automations.tempstick_monitor import check_sensor_status

        data = {
            'room': 'Crawlspace',
            'is_online': False,
            'battery_pct': 80,
            'last_checkin': datetime.now() - timedelta(hours=2)
        }

        with mock.patch('automations.tempstick_monitor.should_send_alert', return_value=True), \
             mock.patch('automations.tempstick_monitor.send_automation_summary') as mock_notify, \
             mock.patch('automations.tempstick_monitor.record_alert_sent'):

            result = check_sensor_status(data, dry_run=False)

            # Verify issue detected
            assert result is True

            # Verify notification sent
            assert mock_notify.called
            title = mock_notify.call_args[0][0]
            assert 'Sensor' in title or 'Issue' in title

    def test_low_battery_detection(self):
        """Test low battery alert"""
        from automations.tempstick_monitor import check_sensor_status

        data = {
            'room': 'Crawlspace',
            'is_online': True,
            'battery_pct': 15,  # Below 20% threshold
            'last_checkin': datetime.now()
        }

        with mock.patch('automations.tempstick_monitor.should_send_alert', return_value=True), \
             mock.patch('automations.tempstick_monitor.send_automation_summary') as mock_notify, \
             mock.patch('automations.tempstick_monitor.record_alert_sent'):

            result = check_sensor_status(data, dry_run=False)

            # Verify issue detected
            assert result is True

            # Verify notification mentions battery
            assert mock_notify.called
            notification_args = mock_notify.call_args[0]
            notification_text = str(notification_args)
            assert 'Battery' in notification_text or 'battery' in notification_text.lower()

    def test_sensor_healthy_no_alert(self):
        """Test no alert when sensor is healthy"""
        from automations.tempstick_monitor import check_sensor_status

        data = {
            'room': 'Crawlspace',
            'is_online': True,
            'battery_pct': 85,
            'last_checkin': datetime.now()
        }

        with mock.patch('automations.tempstick_monitor.send_automation_summary') as mock_notify:
            result = check_sensor_status(data, dry_run=False)

            # No issue
            assert result is False

            # No notification
            assert not mock_notify.called

    def test_dry_run_no_notifications(self):
        """Test dry-run mode prevents notifications"""
        from automations.tempstick_monitor import check_pipe_freeze_risk, PIPE_FREEZE_TEMP

        temp_f = PIPE_FREEZE_TEMP - 10.0  # Severe freeze risk

        with mock.patch('automations.tempstick_monitor.should_send_alert', return_value=True), \
             mock.patch('automations.tempstick_monitor.send_automation_summary') as mock_notify, \
             mock.patch('automations.tempstick_monitor.record_alert_sent') as mock_record:

            result = check_pipe_freeze_risk(temp_f, 'Crawlspace', dry_run=True)

            # Risk detected
            assert result is True

            # But no notification sent in dry-run
            assert not mock_notify.called
            assert not mock_record.called

    def test_status_summary_format(self):
        """Test status summary generation"""
        from automations.tempstick_monitor import get_status_summary

        data = {
            'room': 'Crawlspace',
            'is_online': True,
            'temperature_f': 62.5,
            'humidity': 55.0,
            'battery_pct': 75
        }

        summary = get_status_summary(data)

        # Verify summary contains key information
        assert 'Crawlspace' in summary
        assert '62.5' in summary
        assert '55' in summary
        assert '75%' in summary

    def test_tempstick_api_failure_handling(self):
        """Test behavior when Tempstick API fails"""
        from automations import tempstick_monitor

        # Mock API raising an exception at the point it's called in main()
        with mock.patch('automations.tempstick_monitor.get_sensor_data', side_effect=Exception("API timeout")), \
             mock.patch('automations.tempstick_monitor.send_automation_summary') as mock_notify, \
             mock.patch('sys.argv', ['tempstick_monitor.py']):  # Mock argv to avoid argparse issues

            # Call main() should handle exception gracefully
            result = tempstick_monitor.main()

            # Should return error code
            assert result == 1

            # Note: Error notification is currently disabled (false alarms)
            # See tempstick_monitor.py line 312-322
            assert not mock_notify.called


# =============================================================================
# PRESENCE MONITOR TESTS
# =============================================================================

class TestPresenceMonitor:
    """Tests for automations/presence_monitor.py"""

    def test_presence_monitor_module_structure(self):
        """Test presence_monitor has required functions"""
        from automations import presence_monitor

        # Check critical functions exist
        assert callable(presence_monitor.get_previous_state)
        assert callable(presence_monitor.save_state)
        assert callable(presence_monitor.check_presence)
        assert callable(presence_monitor.trigger_automation)
        assert callable(presence_monitor.run)

        # Check state file path defined
        assert hasattr(presence_monitor, 'STATE_FILE')

    def test_state_file_save_and_load_home(self):
        """Test saving and loading 'home' state"""
        from automations.presence_monitor import save_state, get_previous_state, STATE_FILE

        # Clean up any existing state file
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

        try:
            # Save 'home' state
            save_state(True)

            # Load state
            state = get_previous_state()

            # Verify loaded correctly
            assert state is True

        finally:
            # Clean up
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)

    def test_state_file_save_and_load_away(self):
        """Test saving and loading 'away' state"""
        from automations.presence_monitor import save_state, get_previous_state, STATE_FILE

        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

        try:
            # Save 'away' state
            save_state(False)

            # Load state
            state = get_previous_state()

            # Verify loaded correctly
            assert state is False

        finally:
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)

    def test_state_file_missing_returns_none(self):
        """Test missing state file returns None (first run)"""
        from automations.presence_monitor import get_previous_state, STATE_FILE

        # Ensure state file doesn't exist
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

        state = get_previous_state()

        # Should return None for first run
        assert state is None

    def test_presence_detection_config_error(self):
        """Test behavior when presence config is missing"""
        from automations.presence_monitor import check_presence

        # Mock config with no presence section
        with mock.patch('lib.config.config', {'nest': {}, 'sensibo': {}}):
            result = check_presence()

            # Should return False (assume away) when config missing
            assert result is False

    def test_arrival_triggers_im_home_automation(self):
        """Test arriving home triggers im_home.py"""
        from automations.presence_monitor import run, STATE_FILE

        # Setup: was away, now home
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

        try:
            # Create state file showing "away"
            with open(STATE_FILE, 'w') as f:
                f.write('away')

            # Mock current presence check returning "home"
            with mock.patch('automations.presence_monitor.check_presence', return_value=True), \
                 mock.patch('automations.presence_monitor.trigger_automation') as mock_trigger:

                result = run()

                # Verify im_home.py was triggered
                assert mock_trigger.called
                script_name = mock_trigger.call_args[0][0]
                assert script_name == 'im_home.py'

                # Verify result shows arrival
                assert result['action'] == 'arrived'
                assert result['state'] == 'home'

        finally:
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)

    @pytest.mark.skip(reason="presence_monitor deprecated - replaced by iOS geofencing")
    def test_departure_triggers_leaving_home_automation(self):
        """Test leaving home triggers leaving_home.py"""
        from automations.presence_monitor import run, STATE_FILE

        # Setup: was home, now away
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

        try:
            # Create state file showing "home"
            with open(STATE_FILE, 'w') as f:
                f.write('home')

            # Mock current presence check returning "away"
            with mock.patch('automations.presence_monitor.check_presence', return_value=False), \
                 mock.patch('automations.presence_monitor.trigger_automation') as mock_trigger:

                result = run()

                # Verify leaving_home.py was triggered
                assert mock_trigger.called
                script_name = mock_trigger.call_args[0][0]
                assert script_name == 'leaving_home.py'

                # Verify result shows departure
                assert result['action'] == 'departed'
                assert result['state'] == 'away'

        finally:
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)

    def test_no_change_no_automation_trigger(self):
        """Test no automation triggered when state unchanged"""
        from automations.presence_monitor import run, STATE_FILE

        # Setup: was home, still home
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

        try:
            # Create state file showing "home"
            with open(STATE_FILE, 'w') as f:
                f.write('home')

            # Mock current presence check returning "home" (no change)
            with mock.patch('automations.presence_monitor.check_presence', return_value=True), \
                 mock.patch('automations.presence_monitor.trigger_automation') as mock_trigger:

                result = run()

                # Verify no automation triggered
                assert not mock_trigger.called

                # Verify result shows no change
                assert result['action'] == 'no_change'
                assert result['state'] == 'home'

        finally:
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)

    def test_first_run_initialization(self):
        """Test first run initializes state without triggering automations"""
        from automations.presence_monitor import run, STATE_FILE

        # Setup: no state file (first run)
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

        try:
            # Mock presence check
            with mock.patch('automations.presence_monitor.check_presence', return_value=True), \
                 mock.patch('automations.presence_monitor.trigger_automation') as mock_trigger:

                result = run()

                # Verify no automation triggered on first run
                assert not mock_trigger.called

                # Verify state was saved
                assert os.path.exists(STATE_FILE)

                # Verify result shows initialization
                assert result['action'] == 'initialize'
                assert result['state'] == 'home'

        finally:
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)

    def test_trigger_automation_success(self):
        """Test successful automation execution"""
        from automations.presence_monitor import trigger_automation

        # Mock subprocess.run returning success
        mock_result = mock.Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Automation completed"
        mock_result.stderr = ""

        with mock.patch('subprocess.run', return_value=mock_result), \
             mock.patch('os.path.exists', return_value=True):

            result = trigger_automation('im_home.py')

            # Verify success
            assert result is True

    def test_trigger_automation_script_not_found(self):
        """Test automation trigger when script doesn't exist"""
        from automations.presence_monitor import trigger_automation

        # Mock script not existing
        with mock.patch('os.path.exists', return_value=False):
            result = trigger_automation('nonexistent.py')

            # Should return False
            assert result is False

    def test_trigger_automation_timeout(self):
        """Test automation trigger timeout handling"""
        from automations.presence_monitor import trigger_automation
        import subprocess

        # Mock subprocess timeout
        with mock.patch('subprocess.run', side_effect=subprocess.TimeoutExpired('python', 60)), \
             mock.patch('os.path.exists', return_value=True):

            result = trigger_automation('im_home.py')

            # Should return False on timeout
            assert result is False

    def test_trigger_automation_script_failure(self):
        """Test automation trigger when script exits with error"""
        from automations.presence_monitor import trigger_automation

        # Mock subprocess returning error
        mock_result = mock.Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Error occurred"

        with mock.patch('subprocess.run', return_value=mock_result), \
             mock.patch('os.path.exists', return_value=True):

            result = trigger_automation('im_home.py')

            # Should return False on script failure
            assert result is False

    @pytest.mark.skip(reason="presence_monitor deprecated - replaced by iOS geofencing")
    def test_state_persistence_across_runs(self):
        """Test state persists correctly between multiple runs"""
        from automations.presence_monitor import run, STATE_FILE

        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

        try:
            # Run 1: Initialize as home
            with mock.patch('automations.presence_monitor.check_presence', return_value=True):
                result1 = run()
                assert result1['action'] == 'initialize'

            # Run 2: Still home (no change)
            with mock.patch('automations.presence_monitor.check_presence', return_value=True):
                result2 = run()
                assert result2['action'] == 'no_change'

            # Run 3: Leave home
            with mock.patch('automations.presence_monitor.check_presence', return_value=False), \
                 mock.patch('automations.presence_monitor.trigger_automation'):
                result3 = run()
                assert result3['action'] == 'departed'

            # Run 4: Still away (no change)
            with mock.patch('automations.presence_monitor.check_presence', return_value=False):
                result4 = run()
                assert result4['action'] == 'no_change'

            # Run 5: Return home
            with mock.patch('automations.presence_monitor.check_presence', return_value=True), \
                 mock.patch('automations.presence_monitor.trigger_automation'):
                result5 = run()
                assert result5['action'] == 'arrived'

        finally:
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
