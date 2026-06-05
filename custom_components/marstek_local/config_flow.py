from __future__ import annotations

import asyncio
import socket
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
)

from .const import (
    CONF_SCAN_INTERVAL,
    CONF_UDP_PORT,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    UDP_TIMEOUT,
)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): TextSelector(),
        vol.Optional(CONF_UDP_PORT, default=DEFAULT_PORT): NumberSelector(
            NumberSelectorConfig(min=1, max=65535, mode=NumberSelectorMode.BOX)
        ),
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): NumberSelector(
            NumberSelectorConfig(min=10, max=300, mode=NumberSelectorMode.BOX)
        ),
    }
)


def _test_connection(host: str, port: int) -> str:
    """Try ES.GetMode and return the src string, or raise on failure."""
    import json

    payload = json.dumps(
        {"id": 1, "method": "ES.GetMode", "params": {"id": 0}}
    ).encode()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(UDP_TIMEOUT)
    try:
        sock.sendto(payload, (host, port))
        data, _ = sock.recvfrom(4096)
        response = json.loads(data.decode())
        return response.get("src", "Marstek")
    finally:
        sock.close()


class MarstekLocalConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = int(user_input.get(CONF_UDP_PORT, DEFAULT_PORT))

            try:
                loop = asyncio.get_running_loop()
                src = await loop.run_in_executor(None, _test_connection, host, port)
            except TimeoutError:
                errors["base"] = "cannot_connect"
            except OSError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            else:
                model = src.split("-")[0] if "-" in src else "Marstek"
                await self.async_set_unique_id(src)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=model,
                    data={
                        CONF_HOST: host,
                        CONF_UDP_PORT: port,
                        CONF_SCAN_INTERVAL: int(
                            user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                        ),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )
