from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MarstekCoordinator


class MarstekEntity(CoordinatorEntity[MarstekCoordinator]):
    """Base entity for Marstek Local integration."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MarstekCoordinator, unique_suffix: str) -> None:
        super().__init__(coordinator)
        client = coordinator.client
        device_id = client.src or "marstek"
        self._attr_unique_id = f"{device_id}_{unique_suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=client.device_model,
            manufacturer="Marstek",
            model=client.device_model,
        )
