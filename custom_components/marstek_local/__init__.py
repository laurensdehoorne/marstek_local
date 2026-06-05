from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_SCAN_INTERVAL, CONF_UDP_PORT, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL
from .coordinator import MarstekCoordinator, MarstekUDPClient

type MarstekConfigEntry = ConfigEntry[MarstekCoordinator]

PLATFORMS = [
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: MarstekConfigEntry) -> bool:
    client = MarstekUDPClient(
        host=entry.data[CONF_HOST],
        port=entry.data.get(CONF_UDP_PORT, DEFAULT_PORT),
    )
    coordinator = MarstekCoordinator(
        hass,
        client,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MarstekConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
