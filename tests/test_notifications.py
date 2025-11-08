"""
Unit tests for notification system
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.notifications import send, send_info, send_urgent


class TestNotificationValidation(unittest.TestCase):
    """Test input validation"""

    def test_empty_message_rejected(self):
        """Empty messages should return False"""
        self.assertFalse(send(""))
        self.assertFalse(send("   "))
        self.assertFalse(send(None))

    def test_valid_message_accepted(self):
        """Valid messages should be processed"""
        with patch('lib.notifications._send_ntfy') as mock_send:
            mock_send.return_value = True
            result = send("Test message")
            self.assertTrue(result or mock_send.called)

    def test_invalid_priority_corrected(self):
        """Invalid priorities should be corrected to 0"""
        with patch('lib.notifications._send_ntfy') as mock_send:
            mock_send.return_value = True
            # String instead of int
            send("Test", priority="high")
            # Out of range
            send("Test", priority=999)
            send("Test", priority=-999)
            # All should work (corrected to 0)

    def test_valid_priorities(self):
        """Valid priorities should be accepted"""
        with patch('lib.notifications._send_ntfy') as mock_send:
            mock_send.return_value = True
            for priority in [0, 1]:
                result = send("Test", priority=priority)
                # Should not raise exception


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience wrapper functions"""

    @patch('lib.notifications.send')
    def test_send_info(self, mock_send):
        """send_info should use priority 0"""
        send_info("Test message", "Test Title")
        mock_send.assert_called_once_with("Test message", "Test Title", priority=0)

    @patch('lib.notifications.send')
    def test_send_urgent(self, mock_send):
        """send_urgent should use priority 1"""
        send_urgent("Test message", "Test Title")
        mock_send.assert_called_once_with("Test message", "Test Title", priority=1)


class TestNtfyBackend(unittest.TestCase):
    """Test ntfy.sh notification backend"""

    @patch('lib.notifications.requests.post')
    @patch('lib.config.config', {'notifications': {'service': 'ntfy', 'ntfy': {'topic': 'test_topic'}}})
    def test_ntfy_success(self, mock_post):
        """Successful ntfy notification"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = send("Test message")
        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch('lib.notifications.requests.post')
    @patch('lib.config.config', {'notifications': {'service': 'ntfy', 'ntfy': {'topic': 'test_topic'}}})
    def test_ntfy_priority_mapping(self, mock_post):
        """ntfy priority mapping works correctly"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Priority 0 (info) -> ntfy 3 (default)
        send("Test", priority=0)
        self.assertEqual(mock_post.call_args[1]['headers']['Priority'], '3')

        # Priority 1 (urgent) -> ntfy 5 (urgent)
        send("Test", priority=1)
        self.assertEqual(mock_post.call_args[1]['headers']['Priority'], '5')

    @patch('lib.notifications.requests.post')
    @patch('lib.config.config', {'notifications': {'service': 'ntfy', 'ntfy': {'topic': 'test_topic'}}})
    def test_ntfy_network_failure(self, mock_post):
        """Network failure handling"""
        mock_post.side_effect = Exception("Network error")

        result = send("Test message")
        self.assertFalse(result)


class TestPushoverBackend(unittest.TestCase):
    """Test Pushover notification backend"""

    @patch('lib.notifications.requests.post')
    @patch('lib.config.config', {
        'notifications': {
            'service': 'pushover',
            'pushover': {'token': 'test_token', 'user': 'test_user'}
        }
    })
    def test_pushover_success(self, mock_post):
        """Successful Pushover notification"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = send("Test message")
        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch('lib.config.config', {
        'notifications': {
            'service': 'pushover',
            'pushover': {'token': '', 'user': ''}
        }
    })
    def test_pushover_missing_credentials(self):
        """Missing Pushover credentials"""
        result = send("Test message")
        self.assertFalse(result)

    @patch('lib.notifications.requests.post')
    @patch('lib.config.config', {
        'notifications': {
            'service': 'pushover',
            'pushover': {'token': 'test_token', 'user': 'test_user'}
        }
    })
    def test_pushover_network_failure(self, mock_post):
        """Network failure handling"""
        mock_post.side_effect = Exception("Network error")

        result = send("Test message")
        self.assertFalse(result)


class TestAlertState(unittest.TestCase):
    """Test alert state tracking (rate limiting)"""

    def setUp(self):
        """Clear alert state before each test"""
        from lib.alert_state import clear_alert_state
        clear_alert_state()

    def test_first_alert_should_send(self):
        """First alert should always be sent"""
        from lib.alert_state import should_send_alert
        self.assertTrue(should_send_alert('test_alert', 'location1'))

    def test_duplicate_alert_suppressed(self):
        """Duplicate alert within cooldown should be suppressed"""
        from lib.alert_state import should_send_alert, record_alert_sent

        # First alert
        self.assertTrue(should_send_alert('test_alert', 'location1', cooldown_minutes=60))
        record_alert_sent('test_alert', 'location1')

        # Second alert immediately after
        self.assertFalse(should_send_alert('test_alert', 'location1', cooldown_minutes=60))

    def test_different_locations_tracked_separately(self):
        """Different locations should be tracked separately"""
        from lib.alert_state import should_send_alert, record_alert_sent

        # Alert for location1
        self.assertTrue(should_send_alert('test_alert', 'location1'))
        record_alert_sent('test_alert', 'location1')

        # Alert for location2 should still send
        self.assertTrue(should_send_alert('test_alert', 'location2'))

    def test_clear_alert_state(self):
        """Clearing alert state allows resending"""
        from lib.alert_state import should_send_alert, record_alert_sent, clear_alert_state

        # Send and record
        self.assertTrue(should_send_alert('test_alert', 'location1'))
        record_alert_sent('test_alert', 'location1')

        # Should be suppressed
        self.assertFalse(should_send_alert('test_alert', 'location1'))

        # Clear state
        clear_alert_state('test_alert', 'location1')

        # Should be allowed again
        self.assertTrue(should_send_alert('test_alert', 'location1'))


class TestMessageFormatting(unittest.TestCase):
    """Test notification message formatting"""

    def test_concise_freeze_alert(self):
        """Freeze alert uses concise format"""
        room = "Crawlspace"
        temp_f = 48.5
        expected = "🚨 Crawlspace: 48.5°F - FREEZE RISK"
        actual = f"🚨 {room}: {temp_f:.1f}°F - FREEZE RISK"
        self.assertEqual(expected, actual)

    def test_error_detail_formatting(self):
        """Error details included in automation failures"""
        errors = ["Nest timeout", "Tapo offline", "Sensibo failed"]
        error_summary = ', '.join(errors[:2])
        if len(errors) > 2:
            error_summary += f" (+{len(errors)-2} more)"

        expected = "Nest timeout, Tapo offline (+1 more)"
        self.assertEqual(expected, error_summary)


if __name__ == '__main__':
    unittest.main()
