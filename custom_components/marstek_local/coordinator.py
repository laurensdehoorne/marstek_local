import asyncio
import json
import logging
import socket
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UDP_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class MarstekUDPClient:
    """JSON-RPC over UDP client for Marstek devices."""

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._req_id = 0
        self._lock = asyncio.Lock()
        self.src: str = ""
        # Stored passive-mode settings; updated whenever a passive command is sent
        self._passive_power: int = 0
        self._passive_duration: int = 0

    def _next_id(self) -> int:
        self._req_id = (self._req_id + 1) % 65535
        return self._req_id

    def _sync_exchange(self, payload: bytes) -> dict[str, Any]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(UDP_TIMEOUT)
        try:
            sock.sendto(payload, (self._host, self._port))
            data, _ = sock.recvfrom(4096)
            return json.loads(data.decode())
        finally:
            sock.close()

    async def async_send(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            payload = json.dumps(
                {"id": self._next_id(), "method": method, "params": params}
            ).encode()
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, self._sync_exchange, payload)
            if "src" in response:
                self.src = response["src"]
            if "error" in response:
                code = response["error"]["code"]
                msg = response["error"].get("message", "")
                raise RuntimeError(f"Device error {code}: {msg}")
            return response.get("result", {})

    @property
    def device_model(self) -> str:
        """Parse model from device src string, e.g. 'VenusE-abc123' -> 'VenusE'."""
        if "-" in self.src:
            return self.src.split("-")[0]
        return self.src or "Marstek"

    @property
    def device_mac(self) -> str:
        if "-" in self.src:
            return self.src.split("-", 1)[1]
        return ""

    async def get_es_status(self) -> dict[str, Any]:
        return await self.async_send("ES.GetStatus", {"id": 0})

    async def get_es_mode(self) -> dict[str, Any]:
        return await self.async_send("ES.GetMode", {"id": 0})

    async def get_bat_status(self) -> dict[str, Any]:
        return await self.async_send("Bat.GetStatus", {"id": 0})

    async def get_pv_status(self) -> dict[str, Any]:
        return await self.async_send("PV.GetStatus", {"id": 0})

    async def set_mode(self, mode: str) -> bool:
        """Switch operating mode. Passive mode uses last stored passive settings."""
        mode_cfgs: dict[str, dict[str, Any]] = {
            "Auto": {"auto_cfg": {"enable": 1}},
            "AI": {"ai_cfg": {"enable": 1}},
            "Manual": {
                "manual_cfg": {
                    "time_num": 0,
                    "start_time": "00:00",
                    "end_time": "23:59",
                    "week_set": 127,
                    "power": 0,
                    "enable": 1,
                }
            },
            "Passive": {
                "passive_cfg": {
                    "power": self._passive_power,
                    "cd_time": self._passive_duration,
                }
            },
            "UPS": {"ups_cfg": {"enable": 1}},
        }
        cfg = {"mode": mode, **mode_cfgs.get(mode, {})}
        result = await self.async_send("ES.SetMode", {"id": 0, "config": cfg})
        return bool(result.get("set_result", False))

    async def set_passive(self, power: int, cd_time: int | None = None) -> bool:
        """Activate Passive mode with given power [W] and optional countdown [s].

        Positive power = charge, negative power = discharge (sign convention
        matches the battery's on-grid perspective; verify with your hardware).
        cd_time=0 means no countdown (runs until changed).
        """
        if cd_time is not None:
            self._passive_duration = cd_time
        self._passive_power = power
        result = await self.async_send(
            "ES.SetMode",
            {
                "id": 0,
                "config": {
                    "mode": "Passive",
                    "passive_cfg": {
                        "power": self._passive_power,
                        "cd_time": self._passive_duration,
                    },
                },
            },
        )
        return bool(result.get("set_result", False))

    async def set_dod(self, value: int) -> bool:
        result = await self.async_send("DOD.SET", {"value": int(value)})
        return bool(result.get("set_result", False))

    async def set_led(self, state: bool) -> bool:
        result = await self.async_send("Led.Ctrl", {"state": 1 if state else 0})
        return bool(result.get("set_result", False))


class MarstekCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the Marstek device and merges all component data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: MarstekUDPClient,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            es_status, es_mode, bat_status = await asyncio.gather(
                self.client.get_es_status(),
                self.client.get_es_mode(),
                self.client.get_bat_status(),
                return_exceptions=True,
            )

            data: dict[str, Any] = {}

            if isinstance(es_status, dict):
                data.update(es_status)
            else:
                _LOGGER.debug("ES.GetStatus failed: %s", es_status)

            if isinstance(es_mode, dict):
                data["mode_data"] = es_mode
            else:
                _LOGGER.debug("ES.GetMode failed: %s", es_mode)

            if isinstance(bat_status, dict):
                data["bat_data"] = bat_status
            else:
                _LOGGER.debug("Bat.GetStatus failed: %s", bat_status)

            # Venus D/A only — ignore silently on Venus C/E
            try:
                data["pv_data"] = await self.client.get_pv_status()
            except Exception:
                pass

            if not data:
                raise UpdateFailed("No data received from Marstek device")

            return data

        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Communication error: {err}") from err
