"""
Custom integration to integrate RCT Power with Home Assistant.

For more details about this integration, please refer to
https://github.com/cdce8p/home-assistant-rct-power-integration
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.typing import UNDEFINED
from homeassistant.util.hass_dict import HassEntryKey

from .config_flow import async_get_mac_address_from_host
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
from .lib.const import BATTERY_MODEL, INVERTER_MODEL, EntityUpdatePriority
from .lib.entities import all_entity_descriptions
from .lib.entity import resolve_object_infos
from .models import RctConfEntryData, RctConfEntryOptions

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

    new_data = config_entry.data.copy()
    if config_entry.version < 2:
        if config_entry.minor_version < 2:
            # TODO: modify Config Entry data with changes in version 1.2
            new_data[CONF_MAC] = await async_get_mac_address_from_host(
                hass, config_entry.data[CONF_HOSTNAME]
            )

        new_data[CONF_HOST] = config_entry.data[CONF_HOSTNAME]
        new_data.pop(CONF_HOSTNAME, None)

        device_registry = dr.async_get(hass)
        device_entries = dr.async_entries_for_config_entry(
            device_registry, config_entry.entry_id
        )
        client = RctPowerApiClient(
            hostname=new_data[CONF_HOST],
            port=new_data[CONF_PORT],
        )
        inverter_sn = await client.get_serial_number()
        bms_sn = await client.get_battery_bms_serial_number()
        for dev_entry in device_entries:
            if any(ids[-1] == "None" for ids in dev_entry.identifiers):
                device_registry.async_remove_device(dev_entry.id)
                continue
            if dev_entry.model == INVERTER_MODEL:
                connections = (
                    {(CONNECTION_NETWORK_MAC, mac)}
                    if (mac := new_data[CONF_MAC]) is not None
                    else UNDEFINED
                )
                device_registry.async_update_device(
                    dev_entry.id,
                    new_identifiers={(DOMAIN, f"STORAGE_{inverter_sn}")},
                    new_connections=connections,
                )
            elif dev_entry.model == BATTERY_MODEL:
                device_registry.async_get_device
                device_registry.async_update_device(
                    dev_entry.id,
                    new_identifiers={(DOMAIN, f"BATTERY_{bms_sn}")},
                )

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
    data = cast(RctConfEntryData, entry.data)
    options = cast(RctConfEntryOptions, entry.options)

    client = RctPowerApiClient(
        hostname=data[CONF_HOST],
        port=data[CONF_PORT],
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
        client=client,
        name_suffix="frequent",
        object_ids=frequently_updated_object_ids,
        update_interval=options.get(
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
        client=client,
        name_suffix="infrequent",
        object_ids=infrequently_updated_object_ids,
        update_interval=options.get(
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
        client=client,
        name_suffix="static",
        object_ids=static_object_ids,
        update_interval=options.get(
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

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: RctConfigEntry) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: RctConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
