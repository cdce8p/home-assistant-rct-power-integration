"""Constants for RCT Power."""

from __future__ import annotations

from enum import KEEP, Enum, IntFlag, auto
from typing import Final

NAME: Final = "RCT Power"

# Inverter
INVERTER_MODEL: Final = "RCT Power Storage"

# Battery
BATTERY_MODEL: Final = "RCT Power Battery"

# Icons
ICON = "mdi:solar-power"


# Defaults
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
