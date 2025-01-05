from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.typing import StateType
from homeassistant.util.dt import as_local

from .api import ApiResponseValue
from .const import BatteryStatusFlag
from .const import FREQUENCY_STATE_DECIMAL_DIGITS
from .const import NUMERIC_STATE_DECIMAL_DIGITS


def get_first_api_response_value_as_state(
    entity: SensorEntity,
    values: list[ApiResponseValue | None],
) -> StateType:
    if len(values) <= 0:
        return None

    return get_api_response_value_as_state(entity=entity, value=values[0])


def get_api_response_value_as_state(
    entity: SensorEntity,
    value: ApiResponseValue | None,
) -> StateType:
    if isinstance(value, bytes):
        return value.hex()

    if isinstance(value, tuple):
        return None

    if isinstance(value, (int, float)) and entity.native_unit_of_measurement == "%":
        return round(value * 100, NUMERIC_STATE_DECIMAL_DIGITS)

    if isinstance(value, (int, float)) and entity.native_unit_of_measurement == "Hz":
        return round(value, FREQUENCY_STATE_DECIMAL_DIGITS)

    if isinstance(value, (int, float)):
        return round(value, NUMERIC_STATE_DECIMAL_DIGITS)

    return value


def get_first_api_response_value_as_absolute_state(
    entity: SensorEntity,
    values: list[ApiResponseValue | None],
) -> StateType:
    value = get_first_api_response_value_as_state(entity=entity, values=values)

    if isinstance(value, (int, float)):
        return abs(value)

    return value


def sum_api_response_values_as_state(
    entity: SensorEntity,
    values: list[ApiResponseValue | None],
) -> float:
    return sum(
        (
            float(state_value)
            for value in values
            if isinstance(
                state_value := get_api_response_value_as_state(entity, value),
                (int, float),
            )
        ),
        0.0,
    )


#
# Battery status
#
class BatteryStatus(StrEnum):
    NORMAL = "normal"
    CHARGING = "charging"
    DISCHARGING = "discharging"
    CALIBRATING = "calibrating"
    BALANCING = "balancing"
    OTHER = "other"


available_battery_status: list[str] = list(BatteryStatus._value2member_map_)


def get_api_response_value_as_battery_status(
    entity: SensorEntity,
    value: ApiResponseValue | None,
) -> BatteryStatus | None:
    if not isinstance(value, int):
        return None

    match BatteryStatusFlag(value):
        case BatteryStatusFlag.calibrating:
            return BatteryStatus.CALIBRATING
        case BatteryStatusFlag.charging:
            return BatteryStatus.CHARGING
        case BatteryStatusFlag.discharging:
            return BatteryStatus.DISCHARGING
        case BatteryStatusFlag.balancing:
            return BatteryStatus.BALANCING
        case BatteryStatusFlag.normal:
            return BatteryStatus.NORMAL
        case _:
            return BatteryStatus.OTHER


def get_first_api_response_value_as_battery_status(
    entity: SensorEntity,
    values: list[ApiResponseValue | None],
) -> BatteryStatus | None:
    match values:
        case [firstValue, *_] if firstValue is not None:
            return get_api_response_value_as_battery_status(entity, firstValue)
        case _:
            return None


#
# Bitfield
#
def get_api_response_values_as_bitfield(
    entity: SensorEntity,
    values: list[ApiResponseValue | None],
) -> str:
    return "".join(f"{value:b}" for value in values if isinstance(value, int))


#
# Timestamp
#
def get_first_api_response_value_as_timestamp(
    entity: SensorEntity,
    values: list[ApiResponseValue | None],
) -> datetime | None:
    if len(values) <= 0:
        return None

    return get_api_response_value_as_timestamp(entity=entity, value=values[0])


def get_api_response_value_as_timestamp(
    entity: SensorEntity,
    value: ApiResponseValue | None,
) -> datetime | None:
    if isinstance(value, int):
        return as_local(datetime.fromtimestamp(value))

    return None
