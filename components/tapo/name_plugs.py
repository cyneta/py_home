#!/usr/bin/env python
"""
Interactive script to name Tapo plugs by cycling them on/off for identification

Usage:
    python name_plugs.py           # Name all plugs
    python name_plugs.py 2         # Name only plug #2
    python name_plugs.py 1 3 4     # Name plugs 1, 3, and 4 (skip 2)

Instructions:
- Press ESC to pause/resume cycling
- Type name (can include spaces) and press ENTER when you've found the plug
- Press ENTER alone to skip/keep current name
"""

import sys
import time
import asyncio
import argparse
from kasa import Device, DeviceConfig, Credentials, DeviceConnectionParameters
from kasa import DeviceEncryptionType, DeviceFamily

# For keyboard input
if sys.platform == 'win32':
    import msvcrt
else:
    import termios
    import tty

# Tapo credentials
USERNAME = "matt@wheelers.us"
PASSWORD = "h4fsqSbNjfdm"

async def connect_device(ip):
    """Connect to a Tapo plug"""
    config = DeviceConfig(
        host=ip,
        credentials=Credentials(USERNAME, PASSWORD),
        connection_type=DeviceConnectionParameters(
            device_family=DeviceFamily.SmartTapoPlug,
            encryption_type=DeviceEncryptionType.Klap
        )
    )
    return await Device.connect(config=config)

async def cycle_plug_with_pause(ip, pause_event, stop_event):
    """Cycle a plug on/off, respecting pause and stop events"""
    dev = await connect_device(ip)

    print('Cycling ON/OFF... (Press ESC to pause/resume, then type name and ENTER)')
    print()

    cycle_count = 0
    try:
        while not stop_event.is_set():
            # Check if paused
            if pause_event.is_set():
                await asyncio.sleep(0.1)
                continue

            await dev.turn_on()
            cycle_count += 1
            print(f'\r  Cycle {cycle_count}: ON ', end='', flush=True)

            for _ in range(10):  # 1 second in 0.1s chunks for responsiveness
                if stop_event.is_set() or pause_event.is_set():
                    break
                await asyncio.sleep(0.1)

            if stop_event.is_set():
                break

            await dev.turn_off()
            print(f'\r  Cycle {cycle_count}: OFF', end='', flush=True)

            for _ in range(10):  # 1 second in 0.1s chunks
                if stop_event.is_set() or pause_event.is_set():
                    break
                await asyncio.sleep(0.1)

    finally:
        # Leave it ON
        await dev.turn_on()
        await dev.protocol.close()
        print('\n  Left ON\n')

async def set_plug_name(ip, name):
    """Set the alias for a plug"""
    dev = await connect_device(ip)
    await dev.set_alias(name)
    print(f'✓ Named "{name}"')
    await dev.protocol.close()

def check_keyboard_input():
    """Check for keyboard input (non-blocking)"""
    if sys.platform == 'win32':
        if msvcrt.kbhit():
            return msvcrt.getch().decode('utf-8', errors='ignore')
    return None

async def get_name_with_pause_control(pause_event, stop_event):
    """Get name from user while allowing ESC to pause cycling"""
    buffer = []
    print('Enter name (ESC pauses cycling): ', end='', flush=True)

    while True:
        # Check for keyboard input
        await asyncio.sleep(0.05)  # Small delay for responsiveness

        if sys.platform == 'win32':
            if msvcrt.kbhit():
                char = msvcrt.getch()

                if char == b'\r':  # Enter
                    print()  # New line
                    stop_event.set()
                    return ''.join(buffer).strip()

                elif char == b'\x1b':  # ESC
                    if pause_event.is_set():
                        pause_event.clear()
                        print(' [RESUMED] ', end='', flush=True)
                    else:
                        pause_event.set()
                        print(' [PAUSED] ', end='', flush=True)

                elif char == b'\x08':  # Backspace
                    if buffer:
                        buffer.pop()
                        print('\b \b', end='', flush=True)

                elif 32 <= ord(char) <= 126:  # Printable characters
                    char_str = char.decode('utf-8', errors='ignore')
                    buffer.append(char_str)
                    print(char_str, end='', flush=True)

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Name Tapo plugs by cycling them on/off',
        epilog='Examples:\n'
               '  %(prog)s           # Name all plugs\n'
               '  %(prog)s 2         # Name only plug #2\n'
               '  %(prog)s 1 3 4     # Name plugs 1, 3, and 4',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('plugs', nargs='*', type=int, metavar='N',
                        help='Plug numbers to name (1-4). If omitted, all plugs will be processed.')

    args = parser.parse_args()

    # Load plugs from config
    from lib.config import config
    outlets = config['tapo']['outlets']
    all_plugs = [(outlet['ip'], outlet['name']) for outlet in outlets]

    # Determine which plugs to process
    if args.plugs:
        # Validate plug numbers
        for plug_num in args.plugs:
            if plug_num < 1 or plug_num > len(all_plugs):
                print(f'Error: Plug number must be between 1 and {len(all_plugs)}')
                return

        # Filter to only requested plugs
        plug_indices = [p - 1 for p in args.plugs]  # Convert to 0-based
        plugs_to_process = [(i, all_plugs[i][0], all_plugs[i][1])
                            for i in plug_indices]
    else:
        # Process all plugs
        plugs_to_process = [(i, ip, name) for i, (ip, name) in enumerate(all_plugs)]

    print('='*60)
    print('TAPO PLUG NAMING TOOL')
    print('='*60)
    print()
    print('Instructions:')
    print('  - Plug will cycle ON/OFF automatically')
    print('  - Press ESC to pause/resume cycling')
    print('  - Type the name (can include spaces) and press ENTER')
    print('  - Press ENTER without typing to skip/keep current name')
    print()

    for idx, ip, current_name in plugs_to_process:
        i = idx + 1  # Convert back to 1-based for display
        print(f'===== PLUG #{i}/4 =====')
        print(f'IP: {ip}')
        if current_name:
            print(f'Current name: "{current_name}"')
        print()

        # Events for controlling cycling
        pause_event = asyncio.Event()
        stop_event = asyncio.Event()

        # Start cycling in background
        cycle_task = asyncio.create_task(
            cycle_plug_with_pause(ip, pause_event, stop_event)
        )

        # Get name with pause control
        name = await get_name_with_pause_control(pause_event, stop_event)

        # Wait for cycle task to finish
        await cycle_task

        if name:
            await set_plug_name(ip, name)
        else:
            print('Skipped (no name entered)')

        print()

if __name__ == '__main__':
    if sys.platform != 'win32':
        print('Warning: This script is optimized for Windows. Linux/Mac support may be limited.')
        print()

    asyncio.run(main())
