# Sena-Sign — Developer Documentation (Radxa)

Technical reference for the Radxa build. For the Raspberry Pi Zero W setup, see `docs/SETUP_PI_ZERO_W.md`.

---

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Radxa Board                       │
│                                                     │
│  ┌─────────────┐    ┌──────────────────────────┐   │
│  │   hostapd   │    │     Flask App (port 5000) │   │
│  │  wlan0      │    │     app.py                │   │
│  │  192.168.42.1    │                           │   │
│  └──────┬──────┘    └──────────────┬────────────┘   │
│         │                          │                │
│  ┌──────▼──────┐    ┌──────────────▼────────────┐   │
│  │   dnsmasq   │    │  Captive Portal (port 80) │   │
│  │  DHCP + DNS │    │  captive_app (in-process) │   │
│  │  spoof      │    │                           │   │
│  └─────────────┘    └───────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │           inventory.json (database)          │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
              ↕ Wi-Fi (Sena-Sign-Local)
         Phone browser → http://192.168.42.1:5000
```

---

## File Locations

| File | Path | Purpose |
|------|------|---------|
| Flask app | `/root/sena_sign/app.py` | Main backend |
| Database | `/root/sena_sign/inventory.json` | All item data |
| POS interface | `/root/sena_sign/templates/index.html` | Sales UI |
| Admin panel | `/root/sena_sign/templates/admin.html` | Management UI |
| Wi-Fi config | `/etc/hostapd/hostapd.conf` | Hotspot settings |
| DHCP/DNS config | `/etc/dnsmasq.conf` | Network config |
| Systemd service | `/etc/systemd/system/sena-sign.service` | Auto-start |

---

## System Config Files

### `/etc/hostapd/hostapd.conf`
```
interface=wlan0
driver=nl80211
ssid=Sena-Sign-Local
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=YourPasswordHere
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

### `/etc/dnsmasq.conf`
```
interface=wlan0
listen-address=192.168.42.1
bind-dynamic
dhcp-range=192.168.42.10,192.168.42.100,255.255.255.0,24h
dhcp-option=3,192.168.42.1
dhcp-option=6,192.168.42.1
address=/connectivitycheck.gstatic.com/192.168.42.1
address=/connectivitycheck.android.com/192.168.42.1
address=/clients3.google.com/192.168.42.1
address=/captive.apple.com/192.168.42.1
address=/www.msftconnecttest.com/192.168.42.1
```

**Why the address= lines exist:** Android and iOS run a connectivity check when joining any Wi-Fi network. They query specific domains (e.g. `connectivitycheck.gstatic.com`) expecting an HTTP 204 response. Without spoofing, the board can't answer these queries and the phone marks the Wi-Fi as "no internet," causing it to block local traffic. The `address=` lines redirect those DNS queries to the board's own IP, where the captive portal server answers them correctly.

### `/etc/systemd/system/sena-sign.service`
```ini
[Unit]
Description=Sena-Sign POS System
After=network.target

[Service]
WorkingDirectory=/root/sena_sign
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
```

---

## Flask Application — Route Reference

### Main App (port 5000)

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Renders `index.html` with full inventory |
| GET | `/admin` | Renders `admin.html` with full inventory |
| POST | `/record_sale/<item_id>` | Decrements stock by 1, increments sold by 1 |
| POST | `/undo_sale/<item_id>` | Reverses a sale (increments stock, decrements sold) |
| POST | `/add_item` | Adds a new item to the database |
| POST | `/edit_details/<item_id>` | Edits name, price, quantity, or sold count |
| POST | `/delete_item/<item_id>` | Permanently removes an item |
| GET | `/export_csv` | Streams a CSV sales report as a file download |
| POST | `/upload_patch` | Accepts `app.py`, `index.html`, or `admin.html` uploads and hot-patches the running system |
| GET | `/generate_204` | Android connectivity spoof (returns HTTP 204) |
| GET | `/gen_204` | Android connectivity spoof fallback |
| GET | `/hotspot-detect.html` | iOS connectivity spoof |
| GET | `/ncsi.txt` | Windows/Samsung connectivity spoof |

### Captive Portal App (port 80)

A second Werkzeug server runs inside the same process on a background thread, bound to port 80. It answers all connectivity check requests. This is necessary because Android's connectivity checker specifically hits port 80, not port 5000.

| Route | Returns |
|-------|---------|
| `/generate_204` | HTTP 204 |
| `/gen_204` | HTTP 204 |
| `/hotspot-detect.html` | HTTP 200 with success HTML |
| `/ncsi.txt` | HTTP 200 with "Microsoft NCSI" |
| `/<anything else>` | HTTP 204 (catch-all) |

**Port 80 binding:** Port 80 requires elevated privileges. Grant the capability to Python without running as root:
```bash
sudo setcap 'cap_net_bind_service=+ep' $(readlink -f $(which python3))
```

---

## Database Schema

`inventory.json` is a flat JSON object. Each key is an item ID, and the value is an item record.

```json
{
    "item_01": {
        "name": "Keychain A",
        "price": 5.00,
        "quantity": 14,
        "sold": 3
    },
    "item_02": {
        "name": "Print B",
        "price": 12.00,
        "quantity": 8,
        "sold": 1
    }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Display name shown on the UI |
| `price` | float | Price per unit in dollars |
| `quantity` | int | Current remaining stock |
| `sold` | int | Total units sold this session |

**ID generation:** New items get auto-incremented IDs (`item_01`, `item_02`, etc.) by scanning existing keys for the highest numeric suffix.

**Persistence:** The file is read on every request and written on every mutation. There is no in-memory caching. This is intentional — it ensures data survives a sudden power loss (common at conventions when someone kicks a power bank).

---

## Live Patch System

The `/upload_patch` route allows hot-patching the running system from the admin UI without SSH access.

**Accepted files:**
- `app.py` → saved to `/root/sena_sign/app.py`, triggers restart via `os._exit(0)`
- `index.html` → saved to `/root/sena_sign/templates/index.html`, no restart needed
- `admin.html` → saved to `/root/sena_sign/templates/admin.html`, no restart needed

**Restart behaviour:** When `app.py` is patched, a background thread waits 1 second (to allow the HTTP response to be sent), then calls `os._exit(0)`. The systemd service detects the exit and restarts the process with the new code. The browser polls `/admin` every second until the server responds, then redirects automatically.

**Security:** Any filename not in the allowlist returns HTTP 403. Only exact filenames are accepted — no path traversal possible.

---

## Phone Compatibility Notes

### iPhone (iOS)
iOS is generally cooperative about running Wi-Fi and cellular simultaneously. The issue is DNS — with automatic DNS, iOS may attempt to resolve real domains through the board's Wi-Fi interface, where they fail because the board has no upstream DNS.

**Fix:** Set DNS manually to `8.8.8.8` and `1.1.1.1` on the `Sena-Sign-Local` network profile. This forces all DNS queries through cellular, which correctly routes app traffic over cellular while local `192.168.42.x` traffic stays on Wi-Fi.

Additionally set a manual static IP with no router/gateway to prevent iOS from trying to route internet traffic through the board.

### Android (12+)
Android 12+ enforces strict connectivity validation. If a Wi-Fi network fails the connectivity check, Android routes all traffic (including `192.168.42.x`) through cellular, making the board unreachable.

The DNS spoof + port 80 captive portal correctly intercepts and answers the connectivity check. However, Samsung One UI 8 / Android 16 performs a dual-path connectivity check — it simultaneously checks over both Wi-Fi and cellular, and if the cellular check succeeds, it disregards the Wi-Fi check result and marks the network as "no internet" regardless.

**Current status:** No network-side workaround found for this Samsung behaviour. The POS app is accessible if the user taps "Always connect" on the popup, but internet browsing is disabled while connected. This is an OS-level limitation.

---

## Useful Commands

```bash
# Check app status and recent logs
sudo systemctl status sena-sign

# Follow live logs
sudo journalctl -u sena-sign -f

# Restart the app manually
sudo systemctl restart sena-sign

# Check Wi-Fi hotspot status
sudo systemctl status hostapd

# Check DHCP/DNS status and see connected devices
sudo systemctl status dnsmasq

# View the raw database
cat /root/sena_sign/inventory.json

# Test connectivity check endpoint (from the board itself)
curl http://192.168.42.1:80/generate_204 -v
curl http://192.168.42.1:5000/generate_204 -v
```

---

## Known Issues & Limitations

| Issue | Status | Notes |
|-------|--------|-------|
| Android 12+ dual-path connectivity check | ⚠️ Unresolved | Samsung One UI 8 bypasses spoof via cellular |
| Single Wi-Fi chip (Pi Zero W only) | ℹ️ By design | Can't connect to upstream Wi-Fi and broadcast hotspot simultaneously |
| No authentication on admin panel | ℹ️ By design | Local network only, no public internet exposure |
| JSON write on every mutation | ℹ️ By design | Ensures data survives power loss; performance fine at this scale |
| `os._exit(0)` for restart | ℹ️ By design | Hard exit needed because Flask dev server doesn't support graceful reload |
