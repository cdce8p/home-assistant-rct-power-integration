from __future__ import annotations

import logging
from enum import Enum
from typing import Final

from homeassistant.const import Platform

LOGGER = logging.getLogger(__package__)

# Configuration, options, defaults
CONF_ENTITY_PREFIX: Final = "entity_prefix"
CONF_HOSTNAME: Final = "hostname"

DEFAULT_ENTITY_PREFIX: Final = "RCT Power Storage"
DEFAULT_PORT: Final = 8899

DOMAIN: Final = "rct_power"
PLATFORMS: Final = [Platform.SENSOR]


class ScanInterval(Enum):
    FREQUENT = ("frequent_scan_interval", 30)
    INFREQUENT = ("infrequent_scan_interval", 60 * 3)
    STATIC = ("static_scan_interval", 60 * 60)

    @property
    def key(self) -> str:
        return self.value[0]

    @property
    def default(self) -> int:
        """Default scan interval in seconds."""
        return self.value[1]
