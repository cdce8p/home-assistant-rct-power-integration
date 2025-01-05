"""
Custom integration to integrate RCT Power with Home Assistant.

For more details about this integration, please refer to
https://github.com/weltenwort/home-assistant-rct-power-integration
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.core_config import Config
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.util.hass_dict import HassEntryKey

from .lib.api import RctPowerApiClient
from .lib.const import DOMAIN
from .lib.const import PLATFORMS
from .lib.const import STARTUP_MESSAGE
from .lib.entities import all_entity_descriptions
from .lib.entity import EntityUpdatePriority
from .lib.entity import resolve_object_infos
from .lib.entry import RctPowerConfigEntryData
from .lib.entry import RctPowerConfigEntryOptions
from .lib.update_coordinator import RctPowerDataUpdateCoordinator

SCAN_INTERVAL = timedelta(seconds=30)
RCT_DATA_KEY: HassEntryKey[RctData] = HassEntryKey(DOMAIN)
type RctConfigEntry = ConfigEntry[RctData]

_LOGGER: logging.Logger = logging.getLogger(__package__)


@dataclass
class RctData:
    update_coordinators: dict[EntityUpdatePriority, RctPowerDataUpdateCoordinator]


async def async_setup(hass: HomeAssistant, config: Config) -> bool:
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: RctConfigEntry) -> bool:
    """Set up this integration using UI."""
    if not (data := hass.data.setdefault(DOMAIN, {})):
        _LOGGER.info(STARTUP_MESSAGE)
        data["startup_message"] = True

    config_entry_data = RctPowerConfigEntryData.from_config_entry(entry)
    config_entry_options = RctPowerConfigEntryOptions.from_config_entry(entry)

    client = RctPowerApiClient(
        hostname=config_entry_data.hostname, port=config_entry_data.port
    )

    frequently_updated_object_ids = list(
        {
            object_info.object_id
            for entity_description in all_entity_descriptions
            if entity_description.update_priority == EntityUpdatePriority.FREQUENT
            for object_info in resolve_object_infos(entity_description)
        }
    )
    frequent_update_coordinator = RctPowerDataUpdateCoordinator(
        hass=hass,
        logger=_LOGGER,
        name=f"{DOMAIN} {entry.unique_id} frequent",
        update_interval=timedelta(seconds=config_entry_options.frequent_scan_interval),
        object_ids=frequently_updated_object_ids,
        client=client,
    )

    infrequently_updated_object_ids = list(
        {
            object_info.object_id
            for entity_description in all_entity_descriptions
            if entity_description.update_priority == EntityUpdatePriority.INFREQUENT
            for object_info in resolve_object_infos(entity_description)
        }
    )
    infrequent_update_coordinator = RctPowerDataUpdateCoordinator(
        hass=hass,
        logger=_LOGGER,
        name=f"{DOMAIN} {entry.unique_id} infrequent",
        update_interval=timedelta(
            seconds=config_entry_options.infrequent_scan_interval
        ),
        object_ids=infrequently_updated_object_ids,
        client=client,
    )

    static_object_ids = list(
        {
            object_info.object_id
            for entity_description in all_entity_descriptions
            if entity_description.update_priority == EntityUpdatePriority.STATIC
            for object_info in resolve_object_infos(entity_description)
        }
    )
    static_update_coordinator = RctPowerDataUpdateCoordinator(
        hass=hass,
        logger=_LOGGER,
        name=f"{DOMAIN} {entry.unique_id} static",
        update_interval=timedelta(seconds=config_entry_options.static_scan_interval),
        object_ids=static_object_ids,
        client=client,
    )

    await frequent_update_coordinator.async_refresh()
    await infrequent_update_coordinator.async_refresh()
    await static_update_coordinator.async_refresh()

    if not (
        frequent_update_coordinator.last_update_success
        and infrequent_update_coordinator.last_update_success
        and static_update_coordinator.last_update_success
    ):
        raise ConfigEntryNotReady

    entry.runtime_data = RctData(
        {
            EntityUpdatePriority.FREQUENT: frequent_update_coordinator,
            EntityUpdatePriority.INFREQUENT: infrequent_update_coordinator,
            EntityUpdatePriority.STATIC: static_update_coordinator,
        }
    )

    remove_update_listener = entry.add_update_listener(async_reload_entry)
    entry.async_on_unload(remove_update_listener)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: RctConfigEntry) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: RctConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
