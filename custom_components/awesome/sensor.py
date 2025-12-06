import logging
from datetime import datetime, timedelta
import pytz
import aiohttp
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.event import (
    async_track_time_interval,
    async_track_point_in_utc_time
)
from bs4 import BeautifulSoup
import json

_LOGGER = logging.getLogger(__name__)

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the Garfield URL sensor."""
    _LOGGER.debug("Setting up Garfield URL sensor platform.")
    add_entities([GarfieldComicSensor(hass)])

class GarfieldComicSensor(SensorEntity):
    """Home Assistant sensor to provide the daily Garfield comic URL."""

    _attr_name = "Garfield Comic URL"
    _attr_native_value = None
    _attr_icon = "mdi:comic-strip"

    def __init__(self, hass: HomeAssistant):
        self._hass = hass
        self._remove_listener = None

    @property
    def native_value(self):
        """Return the state of the sensor (the URL)."""
        return self._attr_native_value

    @property
    def should_poll(self):
        """Disable default polling; we use scheduled updates."""
        return False

    async def async_added_to_hass(self):
        """Register state update callback and perform initial update."""
        _LOGGER.debug("Garfield URL sensor added to Home Assistant.")
        # Initial update
        await self.async_update()

        # Schedule update at midnight local time
        await self.schedule_midnight_update()

    async def async_will_remove_from_hass(self):
        """Unregister scheduled callbacks."""
        _LOGGER.debug("Garfield URL sensor will be removed from Home Assistant.")
        if self._remove_listener:
            self._remove_listener()
            _LOGGER.info("Garfield URL update listener successfully removed.")

    async def schedule_midnight_update(self):
        """Schedule the sensor to update at midnight local time."""
        tz = pytz.timezone("Europe/Amsterdam")  # e.g., "America/New_York"
        now = datetime.now(tz)
        midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
        midnight = tz.localize(midnight)

        _LOGGER.warning(f"Scheduling next Garfield update at {midnight.isoformat()}")
        self._remove_listener = async_track_point_in_utc_time(
            self._hass,
            self.midnight_callback,
            midnight.astimezone(pytz.utc)
        )

    async def midnight_callback(self, now):
        """Callback to run at midnight to update the sensor."""
        await self.async_update()
        # Schedule next midnight update
        await self.schedule_midnight_update()

    async def async_update(self) -> None:
        """Generate the daily Garfield comic URL."""
        try:
            today = datetime.now()
            yyyy = today.strftime("%Y")  # e.g., 2025
            yy = today.strftime("%y")    # e.g., 25
            mm = today.strftime("%m")    # e.g., 12
            dd = today.strftime("%d")    # e.g., 06

            url = f"http://picayune.uclick.com/comics/ga/{yyyy}/ga{yy}{mm}{dd}.gif"

            _LOGGER.warning(f"Generated Garfield comic URL: {url}")

            self._attr_native_value = url

        except Exception as err:
            _LOGGER.error(f"Unexpected error generating Garfield URL: {err}")
            self._attr_native_value = "error_generating"

        self.schedule_update_ha_state()
