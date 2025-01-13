from __future__ import annotations

from homeassistant.const import CONF_MAC
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo

from ..const import DOMAIN
from .const import BATTERY_MODEL, INVERTER_MODEL, NAME
from .entity import RctPowerEntity


def get_inverter_device_info(entity: RctPowerEntity) -> DeviceInfo:
    inverter_sn = str(entity.get_valid_api_response_value_by_name("inverter_sn", None))
    connections = (
        {(CONNECTION_NETWORK_MAC, mac)}
        if (mac := entity.coordinators[0].config_entry.data.get(CONF_MAC)) is not None
        else None
    )

    return DeviceInfo(
        identifiers={
            (DOMAIN, f"STORAGE_{inverter_sn}"),
        },
        name=str(
            entity.get_valid_api_response_value_by_name("android_description", ""),
        ),
        connections=connections,
        sw_version=str(entity.get_valid_api_response_value_by_name("svnversion", "")),
        model=INVERTER_MODEL,
        manufacturer=NAME,
    )


def get_battery_device_info(entity: RctPowerEntity) -> DeviceInfo:
    bms_sn = str(entity.get_valid_api_response_value_by_name("battery.bms_sn", None))
    inverter_sn = str(entity.get_valid_api_response_value_by_name("inverter_sn", None))

    return DeviceInfo(
        identifiers={
            (DOMAIN, f"BATTERY_{bms_sn}"),
        },
        name=f"Battery at {entity.get_valid_api_response_value_by_name('android_description', '')}",
        sw_version=str(
            entity.get_valid_api_response_value_by_name(
                "battery.bms_software_version", ""
            )
        ),
        model=BATTERY_MODEL,
        manufacturer=NAME,
        via_device=(DOMAIN, f"STORAGE_{inverter_sn}"),
    )
