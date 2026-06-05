# Marstek Local — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/laurensdehoorne/marstek_local.svg)](https://github.com/laurensdehoorne/marstek_local/releases)

Local polling integration for **Marstek Venus** home battery systems (Venus C, Venus E, Venus A, Venus D) using the official [Marstek Device Open API](https://static-eu.marstekcloud.com/ems/resource/agreement/MarstekDeviceOpenApi.pdf) (Rev 2.0).

No cloud dependency. All communication is JSON-RPC over UDP on your LAN.

---

## Prerequisites

1. Your Marstek device must be connected to your home network (Wi-Fi or Ethernet).
2. **Enable the Open API in the Marstek app**: Device settings → Open API → Enable, and note the UDP port (default: `30000`).
3. Recommended: assign the battery a static IP on your router.

> **Note:** Enabling the Open API may disable some built-in device features to prevent command conflicts. See the Marstek documentation for details.

---

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant.
2. Go to **Integrations** → three-dot menu → **Custom repositories**.
3. Add `https://github.com/laurensdehoorne/marstek_local` as an **Integration**.
4. Search for **Marstek Local** and click **Download**.
5. Restart Home Assistant.

### Manual

1. Download the latest release zip from [GitHub Releases](https://github.com/laurensdehoorne/marstek_local/releases).
2. Extract and copy the `marstek_local` folder into your HA `config/custom_components/` directory.
3. Restart Home Assistant.

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Marstek Local**.
3. Enter the battery's **IP address**, **UDP port** (default `30000`), and optional **scan interval** (default 30 s).

The integration will validate the connection and auto-detect the device model from the response.

---

## Entities

### Sensors

| Entity | Unit | Description |
|---|---|---|
| Battery SOC | % | State of charge |
| Battery Power | W | Charge (+) / discharge (−) power |
| Battery Capacity | Wh | Current total energy in battery |
| Battery Remaining Capacity | Wh | Remaining stored energy |
| Battery Temperature | °C | Cell temperature |
| Solar Power | W | Combined PV input power |
| Grid Power | W | On-grid exchange power |
| Off-grid Power | W | Off-grid output power |
| Total Solar Energy | kWh | Cumulative PV generation |
| Total Grid Export | kWh | Cumulative energy fed to grid |
| Total Grid Import | kWh | Cumulative energy drawn from grid |
| Total Load Energy | kWh | Cumulative load consumption |
| Operating Mode | — | Active mode (text) |
| CT Total Power | W | Total power from current transformer |
| Phase A/B/C Power | W | Per-phase grid power (CT required) |
| CT Cumulative Input/Output | kWh | CT energy totals |
| PV1–PV4 Power/Voltage/Current | W / V / A | Individual PV channels (Venus D/A, disabled by default) |

### Controls

| Entity | Type | Description |
|---|---|---|
| Operating Mode | Select | Switch between Auto / AI / Manual / Passive / UPS |
| Depth of Discharge | Number (30–88 %) | Minimum SOC before discharge stops |
| Panel LED | Switch | Turn the front LED on or off |

---

## Energy Dashboard

The integration exposes energy sensors with `state_class: total_increasing` and `device_class: energy`, so **Total Solar Energy**, **Total Grid Export**, **Total Grid Import**, and **Total Load Energy** are compatible with the HA Energy dashboard out of the box.

---

## Supported Devices

| Model | Tested |
|---|---|
| Venus C / Venus E | |
| Venus A / Venus D | |

Venus D/A models expose additional PV channel sensors (PV1–PV4). These are disabled by default and can be enabled per entity.

---

## Troubleshooting

- **Cannot connect**: Verify the Open API is enabled in the Marstek app, and the IP/port are correct.
- **Unavailable after a while**: The device may have changed IP. Set a static DHCP lease on your router.
- **Phase powers always 0**: The CT (current transformer) must be installed and connected. `ct_state` sensor shows `1` when connected.

---

## License

MIT
