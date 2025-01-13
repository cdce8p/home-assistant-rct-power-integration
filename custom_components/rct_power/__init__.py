"""
Custom integration to integrate RCT Power with Home Assistant.

For more details about this integration, please refer to
https://github.com/cdce8p/home-assistant-rct-power-integration
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.util.hass_dict import HassEntryKey

from custom_components.rct_power.config_flow import async_get_mac_address_from_host

from .const import (
    CONF_HOSTNAME,
    DOMAIN,
    LOGGER,
    PLATFORMS,
    ConfScanInterval,
    ScanIntervalDefault,
)
from .coordinator import RctPowerDataUpdateCoordinator
from .lib.api import RctPowerApiClient
from .lib.entities import all_entity_descriptions
from .lib.entity import EntityUpdatePriority, resolve_object_infos

RCT_DATA_KEY: HassEntryKey[RctData] = HassEntryKey(DOMAIN)
type RctConfigEntry = ConfigEntry[RctData]


@dataclass
class RctData:
    update_coordinators: dict[EntityUpdatePriority, RctPowerDataUpdateCoordinator]


async def async_migrate_entry(
    hass: HomeAssistant, config_entry: RctConfigEntry
) -> bool:
    """Migrate old entry."""
    LOGGER.info(
        "Migrating configuration from version %s.%s",
        config_entry.version,
        config_entry.minor_version,
    )

    if config_entry.version > 2:
        # This means the user has downgraded from a future version
        return False

    if config_entry.version == 1:

        new_data = {**config_entry.data}
        if config_entry.minor_version < 2:
            # TODO: modify Config Entry data with changes in version 1.2
            new_data[CONF_MAC] = await async_get_mac_address_from_host(
                hass, config_entry.data[CONF_HOSTNAME]
            )

        new_data[CONF_HOST] = config_entry.data[CONF_HOSTNAME]
        new_data.pop(CONF_HOSTNAME, None)

        hass.config_entries.async_update_entry(
            config_entry, data=new_data, version=2, minor_version=0
        )

    LOGGER.info(
        "Migration to configuration version %s.%s successful",
        config_entry.version,
        config_entry.minor_version,
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: RctConfigEntry) -> bool:
    """Set up this integration using UI."""
    client = RctPowerApiClient(
        hostname=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
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
        entry=entry,
        name_suffix="frequent",
        client=client,
        object_ids=frequently_updated_object_ids,
        update_interval=entry.options.get(
            ConfScanInterval.FREQUENT, ScanIntervalDefault.FREQUENT
        ),
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
        entry=entry,
        name_suffix="infrequent",
        client=client,
        object_ids=infrequently_updated_object_ids,
        update_interval=entry.options.get(
            ConfScanInterval.INFREQUENT, ScanIntervalDefault.INFREQUENT
        ),
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
        entry=entry,
        name_suffix="static",
        client=client,
        object_ids=static_object_ids,
        update_interval=entry.options.get(
            ConfScanInterval.STATIC, ScanIntervalDefault.STATIC
        ),
    )
    await frequent_update_coordinator.async_config_entry_first_refresh()
    await infrequent_update_coordinator.async_config_entry_first_refresh()
    await static_update_coordinator.async_config_entry_first_refresh()

    entry.runtime_data = RctData(
        {
            EntityUpdatePriority.FREQUENT: frequent_update_coordinator,
            EntityUpdatePriority.INFREQUENT: infrequent_update_coordinator,
            EntityUpdatePriority.STATIC: static_update_coordinator,
        }
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: RctConfigEntry) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: RctConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
