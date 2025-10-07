"""
TP-Link Tapo Smart Outlet API client for py_home

Controls Tapo P125M outlets using python-kasa library.

Setup:
1. Install: pip install python-kasa
2. Add Tapo account credentials to config/.env
3. Configure outlet IPs in config/config.yaml

Requires Python 3.9+
"""

import asyncio
import logging
from kasa import Device, DeviceConfig, Credentials, DeviceConnectionParameters
from kasa import DeviceEncryptionType, DeviceFamily

logger = logging.getLogger(__name__)


class TapoAPI:
    """
    TP-Link Tapo outlet API client using python-kasa

    Supports P100, P105, P110, P115, P125M outlets
    """

    def __init__(self, dry_run=False):
        from lib.config import config

        self.username = config['tapo']['username']
        self.password = config['tapo']['password']
        self.outlets = config['tapo']['outlets']
        self.dry_run = dry_run

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
        config = DeviceConfig(
            host=ip,
            credentials=Credentials(self.username, self.password),
            connection_type=DeviceConnectionParameters(
                device_family=DeviceFamily.SmartTapoPlug,
                encryption_type=DeviceEncryptionType.Klap
            )
        )
        device = await Device.connect(config=config)
        return device

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
            outlet_name: Name from config (e.g., "Kitchen plug")
            ip: IP address (alternative to name)

        Example:
            >>> tapo.turn_on("Kitchen plug")
            >>> tapo.turn_on(ip="192.168.50.135")
        """
        if outlet_name:
            outlet = self.get_outlet_by_name(outlet_name)
            ip = outlet['ip']

        if not ip:
            raise ValueError("Must specify outlet_name or ip")

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would turn ON Tapo outlet: {outlet_name or ip}")
            return

        async def _turn_on():
            device = await self._get_device(ip)
            await device.turn_on()
            await device.protocol.close()

        self._run_async(_turn_on())
        logger.info(f"Tapo outlet turned ON: {outlet_name or ip}")

    def turn_off(self, outlet_name=None, ip=None):
        """
        Turn off outlet

        Args:
            outlet_name: Name from config
            ip: IP address (alternative)

        Example:
            >>> tapo.turn_off("Kitchen plug")
        """
        if outlet_name:
            outlet = self.get_outlet_by_name(outlet_name)
            ip = outlet['ip']

        if not ip:
            raise ValueError("Must specify outlet_name or ip")

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would turn OFF Tapo outlet: {outlet_name or ip}")
            return

        async def _turn_off():
            device = await self._get_device(ip)
            await device.turn_off()
            await device.protocol.close()

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

            result = {
                'on': device.is_on,
                'device_info': {
                    'model': device.model,
                    'alias': device.alias,
                    'hardware_version': device.hw_info.get('hw_ver', 'unknown'),
                    'firmware_version': device.hw_info.get('sw_ver', 'unknown'),
                    'mac': device.mac,
                    'rssi': device.rssi
                }
            }

            # Try to get energy usage (P110/P125M support this)
            try:
                if hasattr(device, 'emeter_realtime'):
                    emeter = await device.emeter_realtime
                    result['energy'] = {
                        'current_power_w': emeter.get('power', 0),
                        'total_wh': emeter.get('total', 0)
                    }
                else:
                    result['energy'] = None
            except Exception:
                result['energy'] = None

            # Close the HTTP session properly
            await device.protocol.close()
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
