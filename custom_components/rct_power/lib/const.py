"""Constants for RCT Power."""

from __future__ import annotations

from enum import KEEP, Enum, IntFlag, auto
from typing import Final

from homeassistant.const import Platform

NAME: Final = "RCT Power"
DOMAIN: Final = "rct_power"
VERSION: Final = "0.14.1"

ISSUE_URL = "https://github.com/cdce8p/home-assistant-rct-power-integration/issues"

# Inverter
INVERTER_MODEL: Final = "RCT Power Storage"

# Battery
BATTERY_MODEL: Final = "RCT Power Battery"

# Icons
ICON = "mdi:solar-power"

# Platforms
PLATFORMS = [Platform.SENSOR]

# Configuration and options
CONF_ENABLED: Final = "enabled"
CONF_HOSTNAME: Final = "hostname"
CONF_PORT: Final = "port"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Defaults
STARTUP_MESSAGE: Final = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""

NUMERIC_STATE_DECIMAL_DIGITS: Final = 1
FREQUENCY_STATE_DECIMAL_DIGITS: Final = 3


class EntityUpdatePriority(Enum):
    FREQUENT = auto()
    INFREQUENT = auto()
    STATIC = auto()


class BatteryStatusFlag(IntFlag, boundary=KEEP):
    normal = 0
    charging = 2**3
    discharging = 2**10
    balancing = 2**11

    calibrating = charging | discharging
