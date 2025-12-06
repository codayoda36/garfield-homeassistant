import logging
from datetime import datetime, timedelta
import pytz
import aiohttp
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.event import async_track_time_interval
from bs4 import BeautifulSoup
import json

_LOGGER = logging.getLogger(__name__)

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    _LOGGER.debug("Setting up Garfield URL sensor platform.")
    # More concise way to add a single entity
    add_entities([ExampleSensor(hass)]) # Pass a list containing your sensor instance directly

class ExampleSensor(SensorEntity):
    """Representation of a Sensor."""

    _attr_name = "Garfield Comic URL"
    _attr_native_value = None
    _attr_icon = "mdi:comic-strip"

    def __init__(self, hass: HomeAssistant):
        self._hass = hass
        self._remove_interval_listener = None

    @property
    def native_value(self):
        """Return the state of the sensor (the URL)."""
        return self._attr_native_value

    async def async_added_to_hass(self):
        """Register state update callback and perform initial update."""
        _LOGGER.debug("Garfield URL sensor added to Home Assistant.")

        await self.async_update()

        self._remove_interval_listener = async_track_time_interval(
            self.hass,
            self.async_update,
            timedelta(hours=24)
        )
        _LOGGER.info("Scheduled Garfield URL update every 24 hours using HA's interval tracker.")

    async def async_will_remove_from_hass(self):
        """Unregister state update callback."""
        _LOGGER.debug("Garfield URL sensor will be removed from Home Assistant.")
        if self._remove_interval_listener:
            self._remove_interval_listener()
            _LOGGER.info("Garfield URL update listener successfully removed.")
    
    async def async_update(self) -> None:
        try:
            today = datetime.now()

            yyyy = today.strftime("%Y")  # e.g. 2025
            yy   = today.strftime("%y")  # e.g. 25
            mm   = today.strftime("%m")  # e.g. 12
            dd   = today.strftime("%d")  # e.g. 06

            # Build the URL
            url = f"http://picayune.uclick.com/comics/ga/{yyyy}/ga{yy}{mm}{dd}.gif"

            _LOGGER.warning(f"Generated Garfield comic URL: {url}")

            # Set sensor value
            self._attr_native_value = url

        except Exception as err:
            _LOGGER.error(f"Unexpected error generating Garfield URL: {err}")
            self._attr_native_value = "error_generating"

        # Update HA state
        self.schedule_update_ha_state()

