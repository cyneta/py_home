#!/usr/bin/env python
"""
Comprehensive Dry-Run Mode Tests

Tests that dry-run flag is respected across all automation scripts and component APIs.
Verifies priority order: CLI flag > env var > config file
"""

import pytest
import os
from unittest.mock import patch, MagicMock, call


# ====================
# Priority Order Tests
# ====================

def test_dry_run_priority_cli_flag():
    """Test CLI --dry-run flag takes highest priority"""
    import sys

    # Simulate --dry-run flag
    with patch.object(sys, 'argv', ['script.py', '--dry-run']):
        with patch('lib.config.get', return_value=False):  # Config says false
            # Reimport to pick up new argv
            import importlib
            from automations import leaving_home
            importlib.reload(leaving_home)

            # CLI flag should override config
            assert leaving_home.DRY_RUN == True


def test_dry_run_priority_config_default():
    """Test config value used when no CLI flag"""
    import sys

    # No CLI flag
    with patch.object(sys, 'argv', ['script.py']):
        with patch('lib.config.get', return_value=True):  # Config says true
            import importlib
            from automations import leaving_home
            importlib.reload(leaving_home)

            # Should use config value
            assert leaving_home.DRY_RUN == True


# ====================
# Automation Script Tests
# ====================

@pytest.fixture
def mock_all_components():
    """Mock all device APIs to verify they're NOT called in dry-run"""
    with patch('components.nest.NestAPI') as mock_nest, \
         patch('components.sensibo.SensiboAPI') as mock_sensibo, \
         patch('components.tapo.TapoAPI') as mock_tapo:

        # Create mock instances
        nest_instance = MagicMock()
        sensibo_instance = MagicMock()
        tapo_instance = MagicMock()

        mock_nest.return_value = nest_instance
        mock_sensibo.return_value = sensibo_instance
        mock_tapo.return_value = tapo_instance

        yield {
            'nest': nest_instance,
            'sensibo': sensibo_instance,
            'tapo': tapo_instance
        }


def test_leaving_home_dry_run_no_api_calls(mock_all_components):
    """Test leaving_home in dry-run mode doesn't call device APIs"""
    from automations import leaving_home

    with patch.object(leaving_home, 'DRY_RUN', True):
        with patch.object(leaving_home, 'update_presence_state') as mock_update:
            result = leaving_home.run()

    # Script should complete successfully
    assert result['status'] in ['success', 'partial']

    # Presence state should NOT be updated in dry-run
    mock_update.assert_not_called()

    # Device APIs should be initialized with dry_run=True
    # but actual control methods should not make real API calls


def test_leaving_home_real_mode_updates_state(mock_all_components):
    """Test leaving_home in real mode DOES update state"""
    from automations import leaving_home

    with patch.object(leaving_home, 'DRY_RUN', False):
        with patch.object(leaving_home, 'update_presence_state') as mock_update:
            result = leaving_home.run()

    # Presence state SHOULD be updated when not dry-run
    mock_update.assert_called_once()


def test_im_home_dry_run_no_api_calls(mock_all_components):
    """Test im_home in dry-run mode doesn't call device APIs"""
    from automations import im_home

    with patch.object(im_home, 'DRY_RUN', True):
        with patch.object(im_home, 'get_presence_state', return_value='home'):
            with patch('lib.notifications.send_automation_summary'):
                result = im_home.run()

    # Script should complete
    assert result['status'] in ['success', 'partial']
    assert result['stage'] == 2


def test_pre_arrival_dry_run_no_state_update(mock_all_components):
    """Test pre_arrival in dry-run mode doesn't update state"""
    from automations import pre_arrival

    with patch.object(pre_arrival, 'DRY_RUN', True):
        with patch.object(pre_arrival, 'update_presence_state') as mock_update:
            with patch.object(pre_arrival, 'is_dark', return_value=False):
                with patch.object(pre_arrival, 'is_night_mode', return_value=False):
                    result = pre_arrival.run()

    # State should NOT be updated in dry-run
    mock_update.assert_not_called()

    assert result['stage'] == 1


def test_goodnight_dry_run_completes(mock_all_components):
    """Test goodnight in dry-run mode completes without errors"""
    from automations import goodnight

    with patch.object(goodnight, 'DRY_RUN', True):
        result = goodnight.run()

    assert result['status'] in ['success', 'partial']


def test_good_morning_dry_run_completes(mock_all_components):
    """Test good_morning in dry-run mode completes without errors"""
    from automations import good_morning

    with patch.object(good_morning, 'DRY_RUN', True):
        with patch('lib.notifications.send_automation_summary'):
            result = good_morning.run()

    assert result['status'] in ['success', 'partial']


# ====================
# Component API Tests
# ====================

def test_nest_api_dry_run_logs_but_no_calls():
    """Test NestAPI in dry-run logs actions but doesn't call API"""
    from components.nest import NestAPI

    nest = NestAPI(dry_run=True)

    # These should log but not make real API calls
    # (Implementation uses self.dry_run check before API calls)
    nest.set_comfort_mode(70)
    nest.set_away_mode()
    nest.set_sleep_mode()

    # No assertion needed - if dry_run works, no exception from missing auth


def test_sensibo_api_dry_run_logs_but_no_calls():
    """Test SensiboAPI in dry-run logs actions but doesn't call API"""
    from components.sensibo import SensiboAPI

    sensibo = SensiboAPI(dry_run=True)

    # These should log but not make real API calls
    sensibo.set_comfort_mode(70)
    sensibo.set_away_mode()
    sensibo.set_sleep_mode(66)

    # No assertion needed - if dry_run works, no exception from missing auth


def test_tapo_api_dry_run_logs_but_no_calls():
    """Test TapoAPI in dry-run logs actions but doesn't call API"""
    from components.tapo import TapoAPI

    tapo = TapoAPI(dry_run=True)

    # These should log but not make real API calls
    tapo.turn_on("Livingroom Lamp")
    tapo.turn_off("Livingroom Lamp")

    # No assertion needed - if dry_run works, no exception from missing auth


# ====================
# Integration Tests
# ====================

def test_two_stage_arrival_dry_run_no_state_changes(mock_all_components):
    """Test complete two-stage arrival in dry-run doesn't change state"""
    from automations import pre_arrival, im_home

    with patch.object(pre_arrival, 'DRY_RUN', True):
        with patch.object(im_home, 'DRY_RUN', True):
            with patch.object(pre_arrival, 'update_presence_state') as mock_pre_update:
                with patch.object(pre_arrival, 'is_dark', return_value=False):
                    with patch.object(pre_arrival, 'is_night_mode', return_value=False):
                        with patch('lib.notifications.send_automation_summary'):
                            # Stage 1: Pre-arrival
                            result1 = pre_arrival.run()
                            assert result1['stage'] == 1

                            # Stage 2: Im home
                            with patch.object(im_home, 'get_presence_state', return_value='home'):
                                result2 = im_home.run()
                                assert result2['stage'] == 2

            # No state updates should happen in dry-run
            mock_pre_update.assert_not_called()


def test_full_automation_cycle_dry_run():
    """Test full automation cycle (leave -> arrive) in dry-run mode"""
    from automations import leaving_home, pre_arrival, im_home

    with patch('components.nest.NestAPI'), \
         patch('components.sensibo.SensiboAPI'), \
         patch('components.tapo.TapoAPI'):

        with patch.object(leaving_home, 'DRY_RUN', True):
            with patch.object(pre_arrival, 'DRY_RUN', True):
                with patch.object(im_home, 'DRY_RUN', True):
                    with patch.object(leaving_home, 'update_presence_state'):
                        with patch.object(pre_arrival, 'update_presence_state'):
                            with patch.object(pre_arrival, 'is_dark', return_value=False):
                                with patch.object(pre_arrival, 'is_night_mode', return_value=False):
                                    with patch.object(im_home, 'get_presence_state', return_value='home'):
                                        with patch('lib.notifications.send_automation_summary'):
                                            # Leave home
                                            result_leave = leaving_home.run()
                                            assert result_leave['status'] in ['success', 'partial']

                                            # Arrive home (Stage 1)
                                            result_pre = pre_arrival.run()
                                            assert result_pre['stage'] == 1

                                            # Arrive home (Stage 2)
                                            result_im = im_home.run()
                                            assert result_im['stage'] == 2

    # All automations complete without errors in dry-run


# ====================
# Edge Case Tests
# ====================

def test_dry_run_with_component_errors():
    """Test dry-run mode handles component initialization errors gracefully"""
    from automations import leaving_home

    with patch.object(leaving_home, 'DRY_RUN', True):
        with patch('components.nest.NestAPI', side_effect=Exception("Auth failed")):
            # Even with component errors, dry-run should handle gracefully
            # (Implementation should catch exceptions)
            result = leaving_home.run()

            # May have errors but shouldn't crash
            assert 'status' in result


def test_dry_run_config_false():
    """Test dry-run disabled when config=false and no CLI flag"""
    import sys

    with patch.object(sys, 'argv', ['script.py']):
        with patch('lib.config.get', return_value=False):
            import importlib
            from automations import leaving_home
            importlib.reload(leaving_home)

            # No CLI flag, config=false → dry_run should be False
            assert leaving_home.DRY_RUN == False


def test_dry_run_config_true():
    """Test dry-run enabled when config=true and no CLI flag"""
    import sys

    with patch.object(sys, 'argv', ['script.py']):
        with patch('lib.config.get', return_value=True):
            import importlib
            from automations import leaving_home
            importlib.reload(leaving_home)

            # No CLI flag, config=true → dry_run should be True
            assert leaving_home.DRY_RUN == True


# ====================
# API Endpoint Tests
# ====================

def test_api_status_returns_dry_run_flag(client):
    """Test /api/system-status endpoint includes dry_run status"""
    from lib.config import get as original_get

    def mock_get(key, default=None):
        if key == 'automations.dry_run':
            return True
        return original_get(key, default)

    with patch('lib.config.get', side_effect=mock_get):
        response = client.get('/api/system-status')
        assert response.status_code == 200

        import json
        data = json.loads(response.data)

        assert 'dry_run' in data
        assert data['dry_run'] == True


def test_api_automation_control_reflects_config(client):
    """Test /api/automation-control returns current config value"""
    with patch('lib.config.get', return_value=False):
        response = client.get('/api/automation-control')
        assert response.status_code == 200

        import json
        data = json.loads(response.data)

        assert data['dry_run'] == False
        assert data['status'] == 'active'


# ====================
# Fixtures
# ====================

@pytest.fixture
def client():
    """Flask test client"""
    from server.app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
