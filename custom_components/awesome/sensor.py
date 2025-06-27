import asyncio
import logging
from datetime import datetime, timedelta
import pytz
import aiohttp
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from bs4 import BeautifulSoup
import json

_LOGGER = logging.getLogger(__name__)

async def async_track_time_interval(hass, interval, action):
    while True:
        await asyncio.sleep(interval)
        await action()

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:

    sensors = []
    sensors.append(ExampleSensor(hass))
    add_entities(sensors)

class ExampleSensor(SensorEntity):
    """Representation of a Sensor."""
    _common_attribute_names = [
        "url",
    ]

    def __init__(self, hass: HomeAssistant):
        #Setup config values
        self._hass = hass

    def initialize_attributes(self):
        for attr_name in self._common_attribute_names:
            setattr(self, f"_{attr_name}_attribute", None)

    @property
    def name(self):
        return "garfieldurl"

    @property
    def native_value(self):
        return self

    @property
    def extra_state_attributes(self):
        attributes = {}
        for attr_name in self._common_attribute_names:
            attributes[attr_name] = getattr(self, f"_{attr_name}_attribute")

        return attributes

    def set_attribute(self, attr_name, value):
        setattr(self, f"_{attr_name}_attribute", value)

    async def async_added_to_hass(self):
        """Register state update callback."""
        self.initialize_attributes()
        self._state_update_task = async_track_time_interval(self.hass, timedelta(hours=24), self.async_update)

    async def async_will_remove_from_hass(self):
        """Unregister state update callback."""
        self._state_update_task.cancel()

    async def async_update(self) -> None: # 'self' would be passed as the entity instance
        """
        Fetches the GoComics Garfield page, extracts the daily comic image URL
        from the JSON-LD script, and logs it.
        """
        url = 'https://www.gocomics.com/garfield'
    
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status() # Raise an exception for HTTP errors
                    html_content = await response.text()

            soup = BeautifulSoup(html_content, 'html.parser')
        
            # Get today's date in the format used in the JSON-LD name (e.g., "June 27, 2025")
            today = datetime.now()
            # Ensure consistent formatting with the website's schema.org data
            # Example: "June 27, 2025" - remove leading zero for day if present
            formatted_date = today.strftime('%B %d, %Y').replace(' 0', ' ')

            comic_image_url = None
            json_ld_scripts = soup.find_all('script', type='application/ld+json')

            for script in json_ld_scripts:
                try:
                    json_data = json.loads(script.string)

                    if (json_data.get('@type') == 'ImageObject' and
                        'Garfield' in json_data.get('name', '') and
                        formatted_date in json_data.get('name', '') and
                        (json_data.get('contentUrl') or json_data.get('url'))):
                    
                        comic_image_url = json_data.get('contentUrl') or json_data.get('url')
                        self.native_value(comic_image_url)
                        _LOGGER.info(f"Daily Garfield Comic URL: {comic_image_url}") # Log the URL
                        break # Found the URL, exit loop

                except json.JSONDecodeError:
                    _LOGGER.debug("Skipping malformed JSON-LD script.")
                    continue
                except AttributeError:
                    _LOGGER.debug("Skipping JSON-LD script with no content.")
                    continue
        
            if not comic_image_url:
                _LOGGER.warning(f"Could not find the daily Garfield comic URL for {formatted_date}.")

        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error fetching data from GoComics: {err}")
        except Exception as err:
            _LOGGER.error(f"An unexpected error occurred while parsing comic data: {err}")

