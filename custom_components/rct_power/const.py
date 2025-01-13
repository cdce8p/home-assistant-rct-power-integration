from __future__ import annotations

import logging
from enum import IntEnum, StrEnum
from typing import Final

from homeassistant.const import Platform

LOGGER = logging.getLogger(__package__)

CONF_HOSTNAME: Final = "hostname"
CONF_ENTITY_PREFIX: Final = "entity_prefix"

DEFAULT_PORT: Final = 8899
DEFAULT_ENTITY_PREFIX: Final = "RCT Power Storage"

DOMAIN: Final = "rct_power"
PLATFORMS: Final = [Platform.SENSOR]


class ConfScanInterval(StrEnum):
    FREQUENT = "frequent_scan_interval"
    INFREQUENT = "infrequent_scan_interval"
    STATIC = "static_scan_interval"


class ScanIntervalDefault(IntEnum):
    FREQUENT = 30
    INFREQUENT = 60 * 3
    STATIC = 60 * 60
