from __future__ import annotations

from homeassistant.const import ATTR_CONNECTIONS, CONF_MAC
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo

from ..const import BATTERY_MODEL, DOMAIN, INVERTER_MODEL, NAME
from .entity import RctPowerEntity


def get_inverter_device_info(entity: RctPowerEntity) -> DeviceInfo:
    inverter_sn = str(entity.get_valid_api_response_value_by_name("inverter_sn", None))
    connections: set[tuple[str, str]] | None = (
        {(CONNECTION_NETWORK_MAC, mac)}
        if (mac := entity.coordinators[0].config_entry.data.get(CONF_MAC)) is not None
        else None
    )

    info = DeviceInfo(
        identifiers={(DOMAIN, f"STORAGE_{inverter_sn}")},
        name=str(
            entity.get_valid_api_response_value_by_name("android_description", ""),
        ),
        sw_version=str(entity.get_valid_api_response_value_by_name("svnversion", "")),
        serial_number=inverter_sn,
        model=INVERTER_MODEL,
        manufacturer=NAME,
    )
    if connections is not None:
        info[ATTR_CONNECTIONS] = connections
    return info


def get_battery_device_info(entity: RctPowerEntity) -> DeviceInfo:
    bms_sn = str(entity.get_valid_api_response_value_by_name("battery.bms_sn", None))
    inverter_sn = str(entity.get_valid_api_response_value_by_name("inverter_sn", None))

    return DeviceInfo(
        identifiers={(DOMAIN, f"BATTERY_{bms_sn}")},
        name=f"Battery at {entity.get_valid_api_response_value_by_name('android_description', '')}",  # type: ignore[str-bytes-safe]
        sw_version=str(
            entity.get_valid_api_response_value_by_name(
                "battery.bms_software_version", ""
            )
        ),
        serial_number=bms_sn,
        model=BATTERY_MODEL,
        manufacturer=NAME,
        via_device=(DOMAIN, f"STORAGE_{inverter_sn}"),
    )
