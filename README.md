# AIO Cloud Server Control Center (GCP Singapore Master)

All-in-One Cloud Server Management Dashboard, Service Stack, dan OpenBot AI Engine untuk Google Cloud Platform (GCP).

## 🚀 Fitur Utama
- **Web Control Center**: Real-time server monitor (CPU, RAM, Disk, Uptime) & Remote Power Control (Reboot/Shutdown VM GCP).
- **Service App Manager**: Kontrol start/stop/restart satu-klik untuk 7 container aplikasi.
- **OpenBot AI Multi-Agent Studio**: Terintegrasi langsung dengan Gemini Flash & OpenBot Hosted Engine.
- **Web Console Terminal**: Akses interactive shell browser berbasis `ttyd` untuk laptop & tablet tanpa perlu software SSH.
- **Remote Desktop Server**: XFCE4 GUI + xRDP (Port 3389) & RustDesk Relay pribadi.
- **One-Click Backup**: Ekspor instan seluruh data `/opt/app-data/` ke file `.tar.gz`.

---

## 📦 Stack Aplikasi Terpasang
1. **Portainer CE** (Port `9000`) - Docker Container Manager visual.
2. **AdGuard Home** (Port `3000`) - Anti-iklan & DNS Privacy terpusat.
3. **MeTube** (Port `8081`) - Video Downloader (YouTube/TikTok) kecepatan 1 Gbps.
4. **FileBrowser** (Port `8080`) - Private Cloud Drive di web.
5. **AnythingLLM** (Port `3001`) - RAG Document AI Question & Answering.
6. **RustDesk Server** (`21115-21119/tcp`, `21116/udp`) - Remote Desktop Relay pribadi.
7. **sing-box (VLESS Reality)** (Port `443`) - Proxy anti-blokir VLESS + XTLS Vision + Reality + Kernel BBR.
8. **OpenBot Hosted Server** - Engine agen AI tersinkronisasi ke aplikasi laptop & tablet (`openbot.run`).

---

## 🛠️ Arsitektur & Struktur Folder
```text
/opt/app-data/
├── aio-dashboard.service    # Systemd daemon untuk Web Dashboard
├── dashboard_server.py      # Python HTTP Server & API Control
├── docker-compose.yml       # Definisi 7 container aplikasi
├── auth.json                # Kredensial login dashboard
├── portainer/               # Data volume Portainer
├── adguard/                 # Data DNS & filter rules AdGuard
├── rustdesk/                # Public key & database RustDesk
├── anythingllm/             # Vector storage AnythingLLM
├── filebrowser/             # Database & folder root FileBrowser
├── metube/downloads/        # Folder output hasil download MeTube
├── openbot/                 # Konfigurasi OpenBot & Gemini API
└── sing-box/                # Config VLESS Reality TLS
```

---

## 🔑 Kredensial Default
- **Dashboard Web**: `http://<IP_SERVER>/` (User: `admin` | Pass: `admin123`)
- **Web Terminal**: `http://<IP_SERVER>:7681/` (User: `admin` | Pass: `admin123`)
- **Remote Desktop (xRDP)**: Port `3389` (User: `eardisis` | Pass: `admin123`)
- **FileBrowser**: Port `8080` (User: `admin` | Pass: `admin`)
