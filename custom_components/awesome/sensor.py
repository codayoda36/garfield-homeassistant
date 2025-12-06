import logging
from datetime import datetime, timedelta, time
import pytz
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.event import async_track_point_in_utc_time

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
        # Schedule update at midnight Amsterdam time
        await self.schedule_daily_update(hour=0, minute=0)

    async def async_will_remove_from_hass(self):
        """Unregister scheduled callbacks."""
        _LOGGER.debug("Garfield URL sensor will be removed from Home Assistant.")
        if self._remove_listener:
            self._remove_listener()
            _LOGGER.info("Garfield URL update listener successfully removed.")

    async def schedule_daily_update(self, hour=0, minute=0):
        """Schedule the sensor to update at a specific time (Amsterdam time)."""
        tz = pytz.timezone("Europe/Amsterdam")
        now = datetime.now(tz)
        # Next scheduled time
        scheduled_time = datetime.combine(now.date(), time(hour=hour, minute=minute))
        scheduled_time = tz.localize(scheduled_time)
        if scheduled_time <= now:
            scheduled_time += timedelta(days=1)

        _LOGGER.info(f"Scheduling next Garfield update at {scheduled_time.isoformat()}")
        self._remove_listener = async_track_point_in_utc_time(
            self._hass,
            self.daily_callback,
            scheduled_time.astimezone(pytz.utc)
        )

    async def daily_callback(self, now):
        """Callback to run at scheduled time to update the sensor."""
        await self.async_update()
        # Schedule next day
        await self.schedule_daily_update(hour=0, minute=0)

    async def async_update(self) -> None:
        """Generate the daily Garfield comic URL."""
        try:
            # Always use yesterday's date
            tz = pytz.timezone("Europe/Amsterdam")
            today = datetime.now(tz).date()
            yesterday = today - timedelta(days=1)

            yyyy = yesterday.strftime("%Y")  # e.g., 2025
            yy = yesterday.strftime("%y")    # e.g., 25
            mm = yesterday.strftime("%m")    # e.g., 12
            dd = yesterday.strftime("%d")    # e.g., 05

            # Sunday uses .jpg, others .gif
            weekday = yesterday.weekday()  # Monday=0 ... Sunday=6
            extension = ".jpg" if weekday == 6 else ".gif"

            url = f"http://picayune.uclick.com/comics/ga/{yyyy}/ga{yy}{mm}{dd}{extension}"

            _LOGGER.info(f"Generated Garfield comic URL for {yesterday}: {url}")

            self._attr_native_value = url

        except Exception as err:
            _LOGGER.error(f"Unexpected error generating Garfield URL: {err}")
            self._attr_native_value = "error_generating"

        # Update HA state
        self.schedule_update_ha_state()
