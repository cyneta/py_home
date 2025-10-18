#!/usr/bin/env python
"""
Tests for AI Command Handler

Tests the natural language command processing system using mocked Claude API.
"""

import os
import sys
import json
from unittest.mock import Mock, patch, MagicMock

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

# Check if anthropic is available
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


def test_parse_automation_command():
    """Test parsing 'I'm leaving' command"""
    print(f"\n{YELLOW}Testing automation command parsing...{RESET}")

    if not ANTHROPIC_AVAILABLE:
        print(f"{YELLOW}⊘{RESET} Skipping (anthropic module not installed)")
        return True

    try:
        from server.ai_handler import parse_with_claude

        # Mock Claude API response
        mock_response = {
            "type": "automation",
            "action": "leaving_home",
            "params": {},
            "reasoning": "User is departing"
        }

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_message = Mock()
            mock_content = Mock()
            mock_content.text = json.dumps(mock_response)
            mock_message.content = [mock_content]
            mock_client.messages.create.return_value = mock_message
            mock_anthropic.return_value = mock_client

            with patch('server.ai_handler.get_claude_api_key', return_value='test-key'):
                result = parse_with_claude("I'm leaving")

        assert result['type'] == 'automation', f"Expected automation, got {result['type']}"
        assert result['action'] == 'leaving_home', f"Expected leaving_home, got {result['action']}"

        print(f"{GREEN}✓{RESET} Automation command parsing test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Automation command parsing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parse_device_command():
    """Test parsing 'set temperature to 72' command"""
    print(f"\n{YELLOW}Testing device command parsing...{RESET}")

    if not ANTHROPIC_AVAILABLE:
        print(f"{YELLOW}⊘{RESET} Skipping (anthropic module not installed)")
        return True

    try:
        from server.ai_handler import parse_with_claude

        # Mock Claude API response
        mock_response = {
            "type": "device",
            "action": "nest.set_temperature",
            "params": {"temp_f": 72},
            "reasoning": "User wants to adjust thermostat"
        }

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_message = Mock()
            mock_content = Mock()
            mock_content.text = json.dumps(mock_response)
            mock_message.content = [mock_content]
            mock_client.messages.create.return_value = mock_message
            mock_anthropic.return_value = mock_client

            with patch('server.ai_handler.get_claude_api_key', return_value='test-key'):
                result = parse_with_claude("set temperature to 72")

        assert result['type'] == 'device', f"Expected device, got {result['type']}"
        assert result['action'] == 'nest.set_temperature', f"Expected nest.set_temperature, got {result['action']}"
        assert result['params']['temp_f'] == 72, f"Expected temp 72, got {result['params']}"

        print(f"{GREEN}✓{RESET} Device command parsing test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Device command parsing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parse_query_command():
    """Test parsing 'what's the temperature?' command"""
    print(f"\n{YELLOW}Testing query command parsing...{RESET}")

    if not ANTHROPIC_AVAILABLE:
        print(f"{YELLOW}⊘{RESET} Skipping (anthropic module not installed)")
        return True

    try:
        from server.ai_handler import parse_with_claude

        # Mock Claude API response
        mock_response = {
            "type": "query",
            "action": "nest.get_status",
            "params": {},
            "reasoning": "User requesting current temperature"
        }

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_message = Mock()
            mock_content = Mock()
            mock_content.text = json.dumps(mock_response)
            mock_message.content = [mock_content]
            mock_client.messages.create.return_value = mock_message
            mock_anthropic.return_value = mock_client

            with patch('server.ai_handler.get_claude_api_key', return_value='test-key'):
                result = parse_with_claude("what's the temperature?")

        assert result['type'] == 'query', f"Expected query, got {result['type']}"
        assert result['action'] == 'nest.get_status', f"Expected nest.get_status, got {result['action']}"

        print(f"{GREEN}✓{RESET} Query command parsing test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Query command parsing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parse_with_markdown_response():
    """Test parsing Claude response wrapped in markdown code blocks"""
    print(f"\n{YELLOW}Testing markdown-wrapped response parsing...{RESET}")

    if not ANTHROPIC_AVAILABLE:
        print(f"{YELLOW}⊘{RESET} Skipping (anthropic module not installed)")
        return True

    try:
        from server.ai_handler import parse_with_claude

        # Mock Claude API response with markdown
        mock_response = {
            "type": "device",
            "action": "tapo.turn_off",
            "params": {"outlet_name": "Master Heater"},
            "reasoning": "User wants to turn off heater"
        }

        markdown_wrapped = f"```json\n{json.dumps(mock_response)}\n```"

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_message = Mock()
            mock_content = Mock()
            mock_content.text = markdown_wrapped
            mock_message.content = [mock_content]
            mock_client.messages.create.return_value = mock_message
            mock_anthropic.return_value = mock_client

            with patch('server.ai_handler.get_claude_api_key', return_value='test-key'):
                result = parse_with_claude("turn off the heater")

        assert result['type'] == 'device', "Failed to parse markdown-wrapped response"
        assert result['params']['outlet_name'] == 'Heater'

        print(f"{GREEN}✓{RESET} Markdown-wrapped response parsing test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Markdown response parsing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_missing_api_key():
    """Test behavior when API key is missing"""
    print(f"\n{YELLOW}Testing missing API key handling...{RESET}")

    try:
        from server.ai_handler import parse_with_claude

        with patch('server.ai_handler.get_claude_api_key', return_value=None):
            result = parse_with_claude("turn on the lights")

        assert result['type'] == 'error', f"Expected error type, got {result['type']}"
        # Accept either missing_api_key or missing_dependency
        assert result['action'] in ['missing_api_key', 'missing_dependency'], f"Expected missing_api_key or missing_dependency, got {result['action']}"

        print(f"{GREEN}✓{RESET} Missing API key handling test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Missing API key test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_execute_automation_dry_run():
    """Test executing automation in dry-run mode"""
    print(f"\n{YELLOW}Testing automation execution (dry-run)...{RESET}")

    try:
        from server.ai_handler import execute_action

        parsed_command = {
            "type": "automation",
            "action": "leaving_home",
            "params": {},
            "reasoning": "User is leaving"
        }

        result = execute_action(parsed_command, dry_run=True)

        assert result['status'] == 'success', f"Expected success, got {result['status']}"
        assert result['executed'] == False, "Dry-run should not execute"
        assert 'leaving_home' in result['message'].lower()

        print(f"{GREEN}✓{RESET} Automation dry-run execution test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Automation dry-run test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_execute_device_command_dry_run():
    """Test executing device command in dry-run mode"""
    print(f"\n{YELLOW}Testing device command execution (dry-run)...{RESET}")

    try:
        from server.ai_handler import execute_action

        parsed_command = {
            "type": "device",
            "action": "nest.set_temperature",
            "params": {"temp_f": 72},
            "reasoning": "User wants 72 degrees"
        }

        result = execute_action(parsed_command, dry_run=True)

        assert result['status'] == 'success', f"Expected success, got {result['status']}"
        assert result['executed'] == False, "Dry-run should not execute"
        assert '72' in result['message']

        print(f"{GREEN}✓{RESET} Device command dry-run execution test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Device command dry-run test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_execute_query():
    """Test executing query command"""
    print(f"\n{YELLOW}Testing query execution...{RESET}")

    try:
        from server.ai_handler import execute_action

        parsed_command = {
            "type": "query",
            "action": "nest.get_status",
            "params": {},
            "reasoning": "User wants temperature"
        }

        # Mock get_status to avoid API call
        with patch('components.nest.get_status') as mock_get_status:
            mock_get_status.return_value = {
                'current_temp_f': 70.5,
                'current_humidity': 45,
                'mode': 'HEAT',
                'hvac_status': 'OFF'
            }

            result = execute_action(parsed_command, dry_run=False)

        assert result['status'] == 'success', f"Expected success, got {result['status']}"
        assert 'data' in result, "Expected data in result"
        assert result['data']['temperature'] == 70.5

        print(f"{GREEN}✓{RESET} Query execution test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Query execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_execute_error_command():
    """Test executing error command"""
    print(f"\n{YELLOW}Testing error command handling...{RESET}")

    try:
        from server.ai_handler import execute_action

        parsed_command = {
            "type": "error",
            "action": "parse_error",
            "params": {},
            "reasoning": "Could not understand command"
        }

        result = execute_action(parsed_command, dry_run=False)

        assert result['status'] == 'error', f"Expected error status, got {result['status']}"
        assert 'message' in result

        print(f"{GREEN}✓{RESET} Error command handling test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Error command test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_execute_unknown_automation():
    """Test executing unknown automation"""
    print(f"\n{YELLOW}Testing unknown automation handling...{RESET}")

    try:
        from server.ai_handler import execute_action

        parsed_command = {
            "type": "automation",
            "action": "nonexistent_automation",
            "params": {},
            "reasoning": "Test"
        }

        result = execute_action(parsed_command, dry_run=False)

        assert result['status'] == 'error', f"Expected error status, got {result['status']}"
        assert 'unknown' in result['message'].lower()

        print(f"{GREEN}✓{RESET} Unknown automation handling test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Unknown automation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_nest_increase_temperature():
    """Test nest.increase_temperature command"""
    print(f"\n{YELLOW}Testing temperature increase command...{RESET}")

    try:
        from server.ai_handler import execute_action

        parsed_command = {
            "type": "device",
            "action": "nest.increase_temperature",
            "params": {"delta": 2},
            "reasoning": "User wants it warmer"
        }

        # Mock Nest API
        with patch('components.nest.get_status') as mock_get_status:
            with patch('components.nest.NestAPI') as mock_nest_api:
                mock_get_status.return_value = {'heat_setpoint_f': 70}
                mock_nest_instance = Mock()
                mock_nest_api.return_value = mock_nest_instance

                result = execute_action(parsed_command, dry_run=False)

        assert result['status'] == 'success', f"Expected success, got {result['status']}"
        assert '72' in result['message'], "Should show increased temp (70 + 2 = 72)"

        print(f"{GREEN}✓{RESET} Temperature increase command test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Temperature increase test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tapo_turn_off():
    """Test tapo.turn_off command"""
    print(f"\n{YELLOW}Testing Tapo turn off command...{RESET}")

    try:
        from server.ai_handler import execute_action

        parsed_command = {
            "type": "device",
            "action": "tapo.turn_off",
            "params": {"outlet_name": "Master Heater"},
            "reasoning": "Turn off heater"
        }

        # Mock Tapo API
        with patch('components.tapo.TapoAPI') as mock_tapo_api:
            mock_tapo_instance = Mock()
            mock_tapo_api.return_value = mock_tapo_instance

            result = execute_action(parsed_command, dry_run=False)

        assert result['status'] == 'success', f"Expected success, got {result['status']}"
        assert 'heater' in result['message'].lower()
        mock_tapo_instance.turn_off.assert_called_once_with("Master Heater")

        print(f"{GREEN}✓{RESET} Tapo turn off command test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Tapo turn off test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_process_command_end_to_end():
    """Test full process_command workflow (dry-run)"""
    print(f"\n{YELLOW}Testing end-to-end command processing...{RESET}")

    if not ANTHROPIC_AVAILABLE:
        print(f"{YELLOW}⊘{RESET} Skipping (anthropic module not installed)")
        return True

    try:
        from server.ai_handler import process_command

        # Mock Claude API
        mock_response = {
            "type": "automation",
            "action": "goodnight",
            "params": {},
            "reasoning": "User going to bed"
        }

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_message = Mock()
            mock_content = Mock()
            mock_content.text = json.dumps(mock_response)
            mock_message.content = [mock_content]
            mock_client.messages.create.return_value = mock_message
            mock_anthropic.return_value = mock_client

            with patch('server.ai_handler.get_claude_api_key', return_value='test-key'):
                result = process_command("goodnight", dry_run=True)

        assert result['status'] == 'success', f"Expected success, got {result['status']}"
        assert result['command_type'] == 'automation'
        assert result['action'] == 'goodnight'
        assert result['executed'] == False  # dry-run

        print(f"{GREEN}✓{RESET} End-to-end command processing test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_system_context():
    """Test system context generation"""
    print(f"\n{YELLOW}Testing system context generation...{RESET}")

    try:
        from server.ai_handler import get_system_context

        context = get_system_context()

        # Verify context includes key information
        assert 'AUTOMATIONS' in context
        assert 'leaving_home' in context
        assert 'goodnight' in context
        assert 'Nest Thermostat' in context
        assert 'Sensibo' in context
        assert 'Tapo' in context

        print(f"{GREEN}✓{RESET} System context generation test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} System context test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all AI handler tests"""
    print(f"\n{GREEN}╔{'═'*58}╗{RESET}")
    print(f"{GREEN}║{' '*16}AI HANDLER TEST SUITE{' '*19}║{RESET}")
    print(f"{GREEN}╚{'═'*58}╝{RESET}\n")
    print(f"{YELLOW}Testing AI command processing with mocked Claude API{RESET}")

    tests = [
        ("Parse automation command", test_parse_automation_command),
        ("Parse device command", test_parse_device_command),
        ("Parse query command", test_parse_query_command),
        ("Parse markdown response", test_parse_with_markdown_response),
        ("Missing API key", test_missing_api_key),
        ("Execute automation (dry-run)", test_execute_automation_dry_run),
        ("Execute device command (dry-run)", test_execute_device_command_dry_run),
        ("Execute query", test_execute_query),
        ("Execute error command", test_execute_error_command),
        ("Unknown automation", test_execute_unknown_automation),
        ("Nest increase temperature", test_nest_increase_temperature),
        ("Tapo turn off", test_tapo_turn_off),
        ("End-to-end processing", test_process_command_end_to_end),
        ("System context generation", test_get_system_context)
    ]

    results = []

    print(f"\n{YELLOW}Running AI Handler Tests:{RESET}")
    print("="*60)

    for name, test_func in tests:
        result = test_func()
        results.append((name, result))

    # Summary
    print("\n" + "="*60)
    print(f"{GREEN}TEST SUMMARY{RESET}")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)

    print(f"Total: {len(results)} tests")
    print(f"{GREEN}Passed: {passed}{RESET}")
    print(f"{RED}Failed: {failed}{RESET}")

    if failed > 0:
        print(f"\n{RED}Failed Tests:{RESET}")
        for name, result in results:
            if not result:
                print(f"  • {name}")

    print()

    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
