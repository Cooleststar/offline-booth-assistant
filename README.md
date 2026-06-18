# 🏷️ Sena-Sign — Offline Convention POS System

A lightweight, fully offline Point of Sale and inventory management system built for convention booths. No internet required. No subscriptions. No cloud. Just plug in a power bank and go.

Built as a personal gift for an artist who sells at conventions — designed to survive the chaos of convention hall Wi-Fi (or the complete lack of it).

---

## ✨ What It Does

- **Tracks inventory in real time** — tap a button, stock goes down by one
- **5-second undo** — mis-tapped? A popup lets you reverse it instantly
- **Admin panel** — add, edit, restock, or delete items without touching any code
- **Sales report export** — download a CSV spreadsheet at the end of the day with full revenue breakdown
- **Live patching** — upload a fixed `app.py` or template file from the admin panel and the system restarts itself in seconds, no terminal needed
- **Works on any phone** — the UI is mobile-first and runs in any browser

---

## 🧠 How It Works

Instead of relying on convention Wi-Fi (notoriously terrible), a small Linux board acts as its own private router. It broadcasts a Wi-Fi network (`Sena-Sign-Local`). When a phone connects to it, the board serves the POS web app directly to the phone's browser — no internet required at any point.

```
Power Bank → Linux Board → broadcasts Wi-Fi → Phone connects → opens POS in browser
```

Everything is self-contained. The board, the app, the database — it all lives on one SD card.

---

## 🛠️ Hardware

| Component | Used In This Build |
|-----------|-------------------|
| Linux Board | Radxa (migration to Raspberry Pi Zero W in progress) |
| Storage | MicroSD card |
| Power | USB power bank |
| Client Device | Any phone with a browser |

---

## 📂 File Structure

```
sena_sign/
├── app.py              # Flask backend — handles all routes and logic
├── inventory.json      # The database — all items, prices, stock, and sales
└── templates/
    ├── index.html      # Main POS interface (sales logging)
    └── admin.html      # Admin panel (inventory management)
```

**System config files (outside the project folder):**
| File | Purpose |
|------|---------|
| `/etc/hostapd/hostapd.conf` | Broadcasts the `Sena-Sign-Local` Wi-Fi network |
| `/etc/dnsmasq.conf` | Assigns IPs to connected devices, handles DNS |
| `/etc/systemd/system/sena-sign.service` | Starts the app automatically on boot |

---

## 🚀 Tech Stack

- **Python 3 / Flask** — backend web server
- **HTML / CSS / JavaScript** — frontend UI (no frameworks, vanilla only)
- **AJAX** — sales updates happen without page reloads
- **JSON** — lightweight flat-file database
- **hostapd** — Wi-Fi hotspot broadcasting
- **dnsmasq** — DHCP server + DNS spoofing for connectivity checks
- **systemd** — auto-start service on boot

---

## 📱 Phone Compatibility

| Platform | Status | Notes |
|----------|--------|-------|
| iPhone (iOS) | ✅ Full support | Requires one-time manual IP + DNS setup |
| Android | ⚠️ Partial | POS works, but internet browsing disabled while connected — Android 12+ OS limitation |

### iPhone one-time setup
Go to **Settings → Wi-Fi → Sena-Sign-Local → Configure IP → Manual**

| Field | Value |
|-------|-------|
| IP Address | `192.168.42.50` |
| Subnet Mask | `255.255.255.0` |
| Router | *(leave blank)* |

Then **Configure DNS → Manual**: `8.8.8.8` and `1.1.1.1`

This lets the phone use the POS app over Wi-Fi while keeping cellular data available for everything else.

---

## 🗺️ Roadmap

- [x] Core POS with undo
- [x] Admin panel
- [x] CSV export
- [x] Live patching via browser upload
- [x] Connectivity check spoofing (iOS + Android)
- [ ] Migrate to Raspberry Pi Zero W (will be added to another branch)
- [ ] Multi-device support (two phones at once)
- [ ] End-of-day sales summary screen using waveshare

---

## 🤝 Use This For Your Own Booth

This project is intentionally simple and self-contained. If you sell at conventions and want a free offline POS system, feel free to fork it. The setup guide for the Radxa and Raspberry Pi Zero W are included in the `/docs` folder.

---

## 👤 Author

Built by Cooleststar for [Sena](https://www.instagram.com/senananacos?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==) — an incredible cosplayer that is amazing at her work.
