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
        """
        Fetches the GoComics Garfield page, extracts the daily comic image URL
        from the JSON-LD script, and updates the sensor state.
        """
        _LOGGER.warning("Attempting to fetch new Garfield URL.")
        url = 'https://www.gocomics.com/garfield'
        fetched_comic_image_url = None

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as response:
                    response.raise_for_status()
                    html_content = await response.text()

            soup = BeautifulSoup(html_content, 'html.parser')

            today = datetime.now()
            formatted_date = today.strftime('%B %d, %Y').replace(' 0', ' ')

            json_ld_scripts = soup.find_all('script', type='application/ld+json')

            for script in json_ld_scripts:
                try:
                    json_data = json.loads(script.string)

                    if (json_data.get('@type') == 'ImageObject' and
                        'Garfield' in json_data.get('name', '') and
                        formatted_date in json_data.get('name', '') and
                        (json_data.get('contentUrl') or json_data.get('url'))):

                        fetched_comic_image_url = json_data.get('contentUrl') or json_data.get('url')
                        _LOGGER.info(f"Successfully fetched Daily Garfield Comic URL: {fetched_comic_image_url}")
                        break

                except json.JSONDecodeError:
                    _LOGGER.debug("Skipping malformed JSON-LD script.")
                    continue
                except (AttributeError, TypeError):
                    _LOGGER.debug("Skipping JSON-LD script with invalid or no content.")
                    continue

            if fetched_comic_image_url:
                self._attr_native_value = fetched_comic_image_url
            else:
                _LOGGER.warning(f"Could not find the daily Garfield comic URL for {formatted_date}.")
                if self._attr_native_value is None:
                    self._attr_native_value = "unknown"

        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error fetching data from GoComics: {err}")
            self._attr_native_value = "error_fetching"
        except Exception as err:
            _LOGGER.error(f"An unexpected error occurred while parsing comic data: {err}")
            self._attr_native_value = "error_parsing"

        self.schedule_update_ha_state()