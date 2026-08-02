"""Integration setup tests."""

# ruff: noqa: RUF001

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.translation import async_get_translations
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.stout_plus.api import StoutPlusApi
from custom_components.stout_plus.const import DOMAIN

MAIN = {
    "Err_str": "<p>Работает без ошибок</p>",
    "Err_Lst": "",
    "Err_Rel_Lst": "",
    "PowerLevels_str": "6",
    "FullPwr_str": "9.0",
    "settedDHWmode": "0",
    "settedTemperatureOfDHW": "",
    "temperatureOfDHW": "",
    "DHWLevel": "2",
    "exManagStatus": "0",
    "setMode": "4",
    "ModeStat": "<p>Текущий режим: Антизамерзание</p>",
    "SetTempCarrier": "30.0",
    "ActValTempCarrier": "24.7",
    "SetDepNumber": "2",
    "TempOutAir": "29.1",
    "setTempRoomMode": "24.3",
    "TempInRoom": "27.3",
}

OTHER = {
    "PowerLevels_str": "6",
    "FullPwr_str": "9.0",
    "CurrPwr_str": "0.0",
    "exManagStatus": "0",
    "amountActiveLevelsAtNight": "4",
    "amountActiveLevelsPerDay": "4",
    "nightTime": "23:00",
    "dayTime": "07:00",
    "OutAirSensor": "<p>Уличный датчик: Подключен</p>",
    "InAirSensor": "<p>Комнатный датчик: Подключен</p>",
    "DomHotWatSensor": "<p>Датчик температуры ГВС: Отключен</p>",
    "exManagMode": "0",
    "Antil_trn": "0",
    "Antil_temp": "0",
    "Antil_wday_str": "0",
    "set_time_legionella": "3",
    "Antil_stat_str": "<p>Статус работы в данный момент: Не активен</p>",
    "SetMaxTempCarrier": "40.0",
    "srcMQTT": "0",
    "PumpLag": "128",
    "PmpStat": "0",
    "Alg": "4",
    "gist": "0.4",
    "warn": "0",
    "ActPress": "<p>Текущее давление: 1.75</p>",
    "RTCStatus": "<p>Внутренние часы (RTC): Работают</p>",
}

ADDITIONAL = {
    "boilerControllerSoft": "<p>Контроллера котла: 00.01.006</p>",
    "boilerRemoteSoft": "<p>Пульта управления: 02.04.001</p>",
    "minDHWTemp": "<p>Минимальная, °C: 40.0</p>",
    "maxDHWTemp": "<p>Максимальная, °C: 75.0</p>",
    "MinPress": "<p>Минимальное, бар: 1.15</p>",
    "MaxPress": "<p>Максимальное, бар: 2.60</p>",
    "MaxWarmCarrier": "<p>Максимальная, °C: 40.0</p>",
    "MinWarmCarrier": "<p>Минимальная, °C: 8.0</p>",
    "MinTempInRoom": "<p>Минимальная, °C: 0.0</p>",
    "MaxTempInRoom": "<p>Максимальная, °C: 35.0</p>",
    "OverHeatSensor": "<p>Датчик температуры теплоносителя: Подключен</p>",
    "PressureSensor": "<p>Датчик давления: Подключен</p>",
    "Sens0": "Состояние: Подключен",
    "SensMode0": "<p>Режим: Комнатный</p>",
    "SensTemp0": "<p>Температура: 27.3</p>",
    "Sens1": "Состояние: Отключен",
    "SensMode1": "<p>Режим: Комнатный</p>",
    "SensTemp1": "<p>Температура: </p>",
    "Sens2": "Состояние: Подключен",
    "SensMode2": "<p>Режим: Уличный</p>",
    "SensTemp2": "<p>Температура: 29.1</p>",
    "Sens3": "Состояние: Подключен",
    "SensMode3": "<p>Режим: Не задан</p>",
    "SensTemp3": "<p>Температура: 0.0</p>",
}


async def test_setup_all_platforms(hass, enable_custom_integrations) -> None:
    """Set up every entity platform from a real boiler response sample."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Stout Plus",
        data={"host": "192.0.2.1"},
        unique_id="stoutplus_test",
    )
    entry.add_to_hass(hass)

    responses = {
        "main_params": MAIN,
        "other_params": OTHER,
        "additional_params": ADDITIONAL,
    }

    async def fake_get(_api: StoutPlusApi, endpoint: str) -> dict:
        return responses[endpoint]

    with (
        patch.object(StoutPlusApi, "async_get", fake_get),
        patch.object(
            StoutPlusApi, "async_post_text", new_callable=AsyncMock
        ) as post_text,
        patch.object(
            StoutPlusApi, "async_post_form", new_callable=AsyncMock
        ) as post_form,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        registry = er.async_get(hass)
        entities = er.async_entries_for_config_entry(registry, entry.entry_id)
        assert len(entities) == 57

        pressure = hass.states.get("sensor.stout_plus_boiler_pressure")
        power = hass.states.get("sensor.stout_plus_boiler_power_consumption")
        assert pressure is not None and pressure.state == "1.75"
        assert power is not None and power.state == "0.0"

        entries_by_unique_id = {entity.unique_id: entity for entity in entities}
        by_unique_id = {
            unique_id: entity.entity_id
            for unique_id, entity in entries_by_unique_id.items()
        }

        assert (
            entries_by_unique_id[
                f"{DOMAIN}_{entry.entry_id}_operating_mode"
            ].entity_category
            is None
        )
        assert (
            entries_by_unique_id[f"{DOMAIN}_{entry.entry_id}_power_day"].entity_category
            is EntityCategory.CONFIG
        )
        assert (
            entries_by_unique_id[
                f"{DOMAIN}_{entry.entry_id}_controller_firmware"
            ].entity_category
            is EntityCategory.DIAGNOSTIC
        )

        await hass.services.async_call(
            "climate",
            "set_temperature",
            {
                "entity_id": by_unique_id[f"{DOMAIN}_{entry.entry_id}_boiler_climate"],
                "temperature": 31.0,
            },
            blocking=True,
        )
        await hass.services.async_call(
            "select",
            "select_option",
            {
                "entity_id": by_unique_id[f"{DOMAIN}_{entry.entry_id}_operating_mode"],
                "option": "heating",
            },
            blocking=True,
        )
        await hass.services.async_call(
            "select",
            "select_option",
            {
                "entity_id": by_unique_id[f"{DOMAIN}_{entry.entry_id}_power_day"],
                "option": "6.0",
            },
            blocking=True,
        )
        await hass.services.async_call(
            "switch",
            "turn_off",
            {
                "entity_id": by_unique_id[f"{DOMAIN}_{entry.entry_id}_dhw"],
            },
            blocking=True,
        )
        await hass.services.async_call(
            "number",
            "set_value",
            {
                "entity_id": by_unique_id[
                    f"{DOMAIN}_{entry.entry_id}_temperature_hysteresis_setting"
                ],
                "value": 0.5,
            },
            blocking=True,
        )
        await hass.services.async_call(
            "time",
            "set_value",
            {
                "entity_id": by_unique_id[f"{DOMAIN}_{entry.entry_id}_night_time"],
                "time": "23:00:00",
            },
            blocking=True,
        )

        post_text.assert_any_await("change_crrtrg", "[31.0]")
        post_text.assert_any_await("switch_mode", "[0]")
        post_text.assert_any_await("switch_dhw", "[0]")
        post_text.assert_any_await("change_gist", "[0.5]")
        post_form.assert_any_await(
            "apply_power_day", {"amountActiveLevelsPerDay": "6.0"}
        )
        post_form.assert_any_await("apply_power_day", {"nightTime": "23:00"})

        translations = await async_get_translations(
            hass, "ru", "entity", integrations={DOMAIN}
        )
        assert (
            translations[f"component.{DOMAIN}.entity.sensor.pressure.name"]
            == "Давление"
        )
        assert (
            translations[
                f"component.{DOMAIN}.entity.select.operating_mode.state.antifreeze"
            ]
            == "Антизамерзание"
        )
