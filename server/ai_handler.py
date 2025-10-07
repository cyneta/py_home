#!/usr/bin/env python
"""
AI Command Handler for Natural Language Home Automation

Processes natural language commands via Claude AI and executes appropriate
automations or device controls.

Usage:
    From Flask: ai_handler.process_command("turn off all lights")
    Standalone: python server/ai_handler.py "set temperature to 72"
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


def get_claude_api_key() -> Optional[str]:
    """Get Claude API key from environment"""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        from lib.config import config
        api_key = config.get('anthropic', {}).get('api_key')
    return api_key


def get_system_context() -> str:
    """Get system context about available devices and automations"""
    from lib.config import config

    # Build context about available devices
    context = """You are a home automation assistant. You have access to these devices and automations:

AUTOMATIONS (predefined routines):
- leaving_home: Set house to away mode (Nest to 62°F, turn off all Tapo outlets)
- goodnight: Sleep mode (Nest to 68°F, turn off Sensibo AC, turn off all outlets)
- im_home: Welcome home (Nest to 72°F)
- good_morning: Morning routine (Nest to 70°F, get weather)
- temp_coordination: Coordinate Nest and Sensibo to avoid conflicts

DEVICES:
Nest Thermostat:
- Current temp, humidity, mode
- Commands: set_temperature(temp_f), set_mode(mode)

Sensibo AC (bedroom):
- Commands: turn_on(mode, temp_f), turn_off(), set_temperature(temp_f)

Tapo Smart Outlets:
"""

    # Add Tapo outlet list
    tapo_outlets = config.get('tapo', {}).get('outlets', [])
    for outlet in tapo_outlets:
        context += f"  - {outlet['name']} ({outlet['ip']})\n"

    context += """
Commands: turn_on(outlet_name), turn_off(outlet_name), turn_on_all(), turn_off_all()

YOUR TASK:
Parse the user's natural language command and return a JSON response with the action to take.

RESPONSE FORMAT:
{
    "type": "automation|device|query|error",
    "action": "specific_action",
    "params": {...},
    "reasoning": "why you chose this action"
}

EXAMPLES:

User: "I'm leaving"
Response: {"type": "automation", "action": "leaving_home", "params": {}, "reasoning": "User is departing, trigger leaving home routine"}

User: "Set temperature to 72"
Response: {"type": "device", "action": "nest.set_temperature", "params": {"temp_f": 72}, "reasoning": "User wants to adjust thermostat"}

User: "Turn off bedroom lamp"
Response: {"type": "device", "action": "tapo.turn_off", "params": {"outlet_name": "Bedroom Right Lamp"}, "reasoning": "User wants to turn off specific outlet"}

User: "Make it warmer"
Response: {"type": "device", "action": "nest.increase_temperature", "params": {"delta": 2}, "reasoning": "User wants temperature increased, default +2°F"}

User: "What's the temperature?"
Response: {"type": "query", "action": "nest.get_status", "params": {}, "reasoning": "User requesting current temperature"}

User: "Turn everything off"
Response: {"type": "device", "action": "tapo.turn_off_all", "params": {}, "reasoning": "User wants all outlets off"}

User: "Good night"
Response: {"type": "automation", "action": "goodnight", "params": {}, "reasoning": "User going to bed, trigger goodnight routine"}

IMPORTANT:
- Be conservative - if unclear, ask for clarification in error message
- Use exact outlet names from the list above
- Temperature should be in Fahrenheit
- Prefer automations over individual commands when appropriate
"""

    return context


def parse_with_claude(command: str) -> Dict[str, Any]:
    """
    Parse natural language command using Claude API

    Args:
        command: Natural language command from user

    Returns:
        Dict with type, action, params, reasoning
    """
    try:
        import anthropic
    except ImportError:
        return {
            "type": "error",
            "action": "missing_dependency",
            "params": {},
            "reasoning": "anthropic package not installed. Run: pip install anthropic"
        }

    api_key = get_claude_api_key()
    if not api_key:
        return {
            "type": "error",
            "action": "missing_api_key",
            "params": {},
            "reasoning": "ANTHROPIC_API_KEY not set in environment or config"
        }

    try:
        client = anthropic.Anthropic(api_key=api_key)

        system_context = get_system_context()

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_context,
            messages=[
                {
                    "role": "user",
                    "content": f"Parse this command: {command}"
                }
            ]
        )

        # Extract JSON from response
        response_text = response.content[0].text.strip()

        # Try to parse JSON (handle if Claude wrapped in markdown)
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        parsed = json.loads(response_text)

        # Validate response structure
        required_keys = ["type", "action", "params", "reasoning"]
        if not all(key in parsed for key in required_keys):
            raise ValueError(f"Response missing required keys: {required_keys}")

        return parsed

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response as JSON: {e}")
        logger.error(f"Response was: {response_text}")
        return {
            "type": "error",
            "action": "parse_error",
            "params": {},
            "reasoning": f"AI response was not valid JSON: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return {
            "type": "error",
            "action": "api_error",
            "params": {},
            "reasoning": f"Failed to process command: {str(e)}"
        }


def execute_action(parsed_command: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    """
    Execute the parsed command action

    Args:
        parsed_command: Output from parse_with_claude()
        dry_run: If True, don't actually execute, just return what would happen

    Returns:
        Dict with status, result, message
    """
    command_type = parsed_command.get("type")
    action = parsed_command.get("action")
    params = parsed_command.get("params", {})
    reasoning = parsed_command.get("reasoning", "")

    result = {
        "status": "success",
        "command_type": command_type,
        "action": action,
        "reasoning": reasoning,
        "executed": not dry_run
    }

    try:
        # Handle errors
        if command_type == "error":
            result["status"] = "error"
            result["message"] = reasoning
            return result

        # Handle queries
        if command_type == "query":
            if action == "nest.get_status":
                from components.nest import get_status
                status = get_status()
                result["data"] = {
                    "temperature": status['current_temp_f'],
                    "humidity": status['current_humidity'],
                    "mode": status['mode'],
                    "hvac_status": status['hvac_status']
                }
                result["message"] = f"Current temp: {status['current_temp_f']}°F, {status['mode']} mode, HVAC: {status['hvac_status']}"
            else:
                result["status"] = "error"
                result["message"] = f"Unknown query action: {action}"
            return result

        # Handle automations
        if command_type == "automation":
            if dry_run:
                result["message"] = f"Would trigger automation: {action}"
                return result

            automation_map = {
                "leaving_home": "automations.leaving_home",
                "goodnight": "automations.goodnight",
                "im_home": "automations.im_home",
                "good_morning": "automations.good_morning",
                "temp_coordination": "automations.temp_coordination"
            }

            if action in automation_map:
                module_name = automation_map[action]
                module = __import__(module_name, fromlist=['run'])
                automation_result = module.run()
                result["data"] = automation_result
                result["message"] = f"Triggered {action} automation"
            else:
                result["status"] = "error"
                result["message"] = f"Unknown automation: {action}"

            return result

        # Handle device commands
        if command_type == "device":
            if dry_run:
                result["message"] = f"Would execute: {action} with params {params}"
                return result

            # Nest commands
            if action.startswith("nest."):
                from components.nest import NestAPI, get_status
                nest = NestAPI()

                if action == "nest.set_temperature":
                    temp_f = params.get("temp_f")
                    mode = params.get("mode")
                    nest.set_temperature(temp_f, mode=mode)
                    result["message"] = f"Set Nest to {temp_f}°F"

                elif action == "nest.increase_temperature":
                    delta = params.get("delta", 2)
                    current_status = get_status()
                    current_temp = current_status.get('heat_setpoint_f') or current_status.get('cool_setpoint_f') or 70
                    new_temp = current_temp + delta
                    nest.set_temperature(new_temp)
                    result["message"] = f"Increased temperature by {delta}°F to {new_temp}°F"

                elif action == "nest.decrease_temperature":
                    delta = params.get("delta", 2)
                    current_status = get_status()
                    current_temp = current_status.get('heat_setpoint_f') or current_status.get('cool_setpoint_f') or 70
                    new_temp = current_temp - delta
                    nest.set_temperature(new_temp)
                    result["message"] = f"Decreased temperature by {delta}°F to {new_temp}°F"

                elif action == "nest.set_mode":
                    mode = params.get("mode")
                    nest.set_mode(mode)
                    result["message"] = f"Set Nest mode to {mode}"

                else:
                    result["status"] = "error"
                    result["message"] = f"Unknown Nest action: {action}"

            # Sensibo commands
            elif action.startswith("sensibo."):
                from components.sensibo import SensiboAPI
                sensibo = SensiboAPI()

                if action == "sensibo.turn_on":
                    mode = params.get("mode", "cool")
                    temp_f = params.get("temp_f", 72)
                    sensibo.turn_on(mode=mode, target_temp_f=temp_f)
                    result["message"] = f"Turned on AC: {mode} mode at {temp_f}°F"

                elif action == "sensibo.turn_off":
                    sensibo.turn_off()
                    result["message"] = "Turned off AC"

                elif action == "sensibo.set_temperature":
                    temp_f = params.get("temp_f")
                    sensibo.set_temperature(temp_f)
                    result["message"] = f"Set AC to {temp_f}°F"

                else:
                    result["status"] = "error"
                    result["message"] = f"Unknown Sensibo action: {action}"

            # Tapo commands
            elif action.startswith("tapo."):
                from components.tapo import TapoAPI
                tapo = TapoAPI()

                if action == "tapo.turn_on":
                    outlet_name = params.get("outlet_name")
                    tapo.turn_on(outlet_name)
                    result["message"] = f"Turned on {outlet_name}"

                elif action == "tapo.turn_off":
                    outlet_name = params.get("outlet_name")
                    tapo.turn_off(outlet_name)
                    result["message"] = f"Turned off {outlet_name}"

                elif action == "tapo.turn_on_all":
                    tapo.turn_on_all()
                    result["message"] = "Turned on all outlets"

                elif action == "tapo.turn_off_all":
                    tapo.turn_off_all()
                    result["message"] = "Turned off all outlets"

                else:
                    result["status"] = "error"
                    result["message"] = f"Unknown Tapo action: {action}"

            else:
                result["status"] = "error"
                result["message"] = f"Unknown device type in action: {action}"

            return result

        # Unknown type
        result["status"] = "error"
        result["message"] = f"Unknown command type: {command_type}"
        return result

    except Exception as e:
        logger.error(f"Error executing action: {e}")
        import traceback
        traceback.print_exc()
        result["status"] = "error"
        result["message"] = f"Execution failed: {str(e)}"
        return result


def process_command(command: str, dry_run: bool = False) -> Dict[str, Any]:
    """
    Main entry point: parse and execute natural language command

    Args:
        command: Natural language command from user
        dry_run: If True, don't actually execute commands

    Returns:
        Dict with status, message, and result data
    """
    logger.info(f"Processing command: {command} (dry_run={dry_run})")

    # Parse with AI
    parsed = parse_with_claude(command)
    logger.info(f"Parsed as: {parsed}")

    # Execute action
    result = execute_action(parsed, dry_run=dry_run)
    logger.info(f"Result: {result}")

    return result


def main():
    """CLI for testing AI command handler"""
    import argparse

    parser = argparse.ArgumentParser(description='AI Command Handler for Home Automation')
    parser.add_argument('command', nargs='+', help='Natural language command')
    parser.add_argument('--dry-run', action='store_true', help='Parse only, don\'t execute')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    command = ' '.join(args.command)

    result = process_command(command, dry_run=args.dry_run)

    print("\n" + "="*60)
    print("AI COMMAND RESULT")
    print("="*60)
    print(json.dumps(result, indent=2))
    print("="*60 + "\n")

    if result['status'] == 'error':
        sys.exit(1)


if __name__ == '__main__':
    main()
