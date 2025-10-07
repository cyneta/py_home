"""
TP-Link Tapo Smart Outlet API client for py_home

Controls Tapo P125M outlets using the official tapo Python library.

Setup:
1. Install: pip install tapo
2. Add Tapo account credentials to config/.env
3. Configure outlet IPs in config/config.yaml

Requires Python 3.9+
"""

import asyncio
import logging
from tapo import ApiClient

logger = logging.getLogger(__name__)


class TapoAPI:
    """
    TP-Link Tapo outlet API client

    Supports P100, P105, P110, P115, P125M outlets
    """

    def __init__(self):
        from utils.config import config

        self.username = config['tapo']['username']
        self.password = config['tapo']['password']
        self.outlets = config['tapo']['outlets']

        if not self.username or not self.password:
            raise ValueError(
                "Tapo credentials not configured. "
                "Add TAPO_USERNAME and TAPO_PASSWORD to config/.env"
            )

        if not self.outlets:
            raise ValueError(
                "No Tapo outlets configured in config/config.yaml"
            )

    async def _get_device(self, ip):
        """Get device client for specific outlet"""
        client = ApiClient(self.username, self.password)
        return await client.p110(ip)  # P110 API works for P125M too

    def _run_async(self, coro):
        """Helper to run async function in sync context"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(coro)

    def get_outlet_by_name(self, name):
        """Find outlet config by name"""
        for outlet in self.outlets:
            if outlet['name'].lower() == name.lower():
                return outlet
        raise ValueError(f"Outlet not found: {name}")

    def turn_on(self, outlet_name=None, ip=None):
        """
        Turn on outlet

        Args:
            outlet_name: Name from config (e.g., "Coffee Maker")
            ip: IP address (alternative to name)

        Example:
            >>> tapo.turn_on("Coffee Maker")
            >>> tapo.turn_on(ip="192.168.1.100")
        """
        if outlet_name:
            outlet = self.get_outlet_by_name(outlet_name)
            ip = outlet['ip']

        if not ip:
            raise ValueError("Must specify outlet_name or ip")

        async def _turn_on():
            device = await self._get_device(ip)
            await device.on()

        self._run_async(_turn_on())
        logger.info(f"Tapo outlet turned ON: {outlet_name or ip}")

    def turn_off(self, outlet_name=None, ip=None):
        """
        Turn off outlet

        Args:
            outlet_name: Name from config
            ip: IP address (alternative)

        Example:
            >>> tapo.turn_off("Coffee Maker")
        """
        if outlet_name:
            outlet = self.get_outlet_by_name(outlet_name)
            ip = outlet['ip']

        if not ip:
            raise ValueError("Must specify outlet_name or ip")

        async def _turn_off():
            device = await self._get_device(ip)
            await device.off()

        self._run_async(_turn_off())
        logger.info(f"Tapo outlet turned OFF: {outlet_name or ip}")

    def turn_on_all(self):
        """Turn on all configured outlets"""
        for outlet in self.outlets:
            try:
                self.turn_on(ip=outlet['ip'])
                logger.info(f"Turned ON: {outlet['name']}")
            except Exception as e:
                logger.error(f"Failed to turn on {outlet['name']}: {e}")

    def turn_off_all(self):
        """Turn off all configured outlets"""
        for outlet in self.outlets:
            try:
                self.turn_off(ip=outlet['ip'])
                logger.info(f"Turned OFF: {outlet['name']}")
            except Exception as e:
                logger.error(f"Failed to turn off {outlet['name']}: {e}")

    def get_status(self, outlet_name=None, ip=None):
        """
        Get outlet status

        Args:
            outlet_name: Name from config
            ip: IP address (alternative)

        Returns:
            dict: {
                'on': bool,
                'device_info': dict,
                'energy': dict (if supported)
            }
        """
        if outlet_name:
            outlet = self.get_outlet_by_name(outlet_name)
            ip = outlet['ip']

        if not ip:
            raise ValueError("Must specify outlet_name or ip")

        async def _get_status():
            device = await self._get_device(ip)
            info = await device.get_device_info()

            result = {
                'on': info.device_on,
                'device_info': {
                    'type': info.type,
                    'model': info.model,
                    'hardware_version': info.hw_ver,
                    'firmware_version': info.fw_ver,
                    'mac': info.mac,
                    'rssi': info.rssi
                }
            }

            # Try to get energy usage (P110/P125M support this)
            try:
                energy = await device.get_energy_usage()
                result['energy'] = {
                    'current_power_w': energy.current_power / 1000,  # mW to W
                    'today_energy_wh': energy.today_energy,
                    'month_energy_wh': energy.month_energy
                }
            except Exception:
                result['energy'] = None

            return result

        status = self._run_async(_get_status())
        logger.info(
            f"Tapo status ({outlet_name or ip}): "
            f"{'ON' if status['on'] else 'OFF'}"
        )
        return status

    def list_all_status(self):
        """Get status of all configured outlets"""
        results = []
        for outlet in self.outlets:
            try:
                status = self.get_status(ip=outlet['ip'])
                status['name'] = outlet['name']
                results.append(status)
            except Exception as e:
                logger.error(f"Failed to get status for {outlet['name']}: {e}")
                results.append({
                    'name': outlet['name'],
                    'error': str(e)
                })
        return results


# Singleton instance
_tapo = None

def get_tapo():
    """Get or create Tapo API instance"""
    global _tapo
    if _tapo is None:
        _tapo = TapoAPI()
    return _tapo


# Convenience functions
def turn_on(outlet_name):
    """Turn on outlet by name"""
    return get_tapo().turn_on(outlet_name)


def turn_off(outlet_name):
    """Turn off outlet by name"""
    return get_tapo().turn_off(outlet_name)


def turn_on_all():
    """Turn on all outlets"""
    return get_tapo().turn_on_all()


def turn_off_all():
    """Turn off all outlets"""
    return get_tapo().turn_off_all()


def get_status(outlet_name):
    """Get outlet status"""
    return get_tapo().get_status(outlet_name)


__all__ = [
    'TapoAPI', 'get_tapo', 'turn_on', 'turn_off',
    'turn_on_all', 'turn_off_all', 'get_status'
]
