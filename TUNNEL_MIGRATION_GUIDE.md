# Panduan Cloudflare Tunnel & Migrasi Bebas Pusing (Zero Coupling)

Cloudflare Tunnel (`aio-sg-master`) adalah jembatan permanen antara domain **`ohana.biz.id`** dengan server aplikasi Anda.

Arsitektur ini didesain agar **tidak terikat dengan IP VM GCP saat ini**. Jika masa aktif VM GCP 3 bulan habis dan Anda berganti ke server baru (Oracle Cloud Always Free, VPS baru, atau PC lokal), Anda **tidak perlu mengubah DNS** di Cloudflare maupun di registrar domain.

---

## 📌 Identitas Tunnel
* **Tunnel Name:** `aio-sg-master`
* **Tunnel ID:** `0476994b-a44f-4715-9185-b4aaef427bff`
* **Account ID:** `39f490a8a9cbdca3eca947a33db61b29`
* **Tunnel Token:**
  ```text
  eyJhIjoiMzlmNDkwYThhOWNiZGNhM2VjYTk0N2EzM2RiNjFiMjkiLCJ0IjoiMDQ3Njk5NGItYTQ0Zi00NzE1LTkxODUtYjRhYWVmNDI3YmZmIiwicyI6InpjL1BrZjNKamtSTFRLTXJFVVZLYmt6QjUxdXFXNGphVHVaWk92QnhhR1RmN3BEZCtWRGxXa1E0U0p2cHlmQVp4dzdoSG1YSFArMmVlQUtERUFnOTh3PT0ifQ==
  ```

---

## 🌐 Pemetaan Subdomain Otomatis (Remote Ingress)

Semua subdomain di bawah ini sudah diarahkan ke Cloudflare Tunnel via CNAME:

| Subdomain | Target Service Internal | Keterangan |
| :--- | :--- | :--- |
| `dash.ohana.biz.id` | Cloudflare Pages (`sg-vm.pages.dev`) | Control Center & OpenBot AI Studio (Serverless) |
| `portainer.ohana.biz.id` | `http://127.0.0.1:9000` | Portainer Docker UI |
| `files.ohana.biz.id` | `http://127.0.0.1:8080` | FileBrowser Cloud Storage |
| `metube.ohana.biz.id` | `http://127.0.0.1:8081` | MeTube Downloader |
| `ai.ohana.biz.id` | `http://127.0.0.1:3001` | AnythingLLM AI |
| `adguard.ohana.biz.id` | `http://127.0.0.1:3000` | AdGuard Home DNS |
| `console.ohana.biz.id` | `http://127.0.0.1:7681` | Web Console Shell (ttyd) |
| `vpn.ohana.biz.id` | `34.1.202.11:443` | sing-box VLESS Reality (DNS-only) |
| `rustdesk.ohana.biz.id` | `34.1.202.11:21115-21119` | RustDesk Remote Desktop (DNS-only) |

---

## 🚀 Cara Migrasi Cepat saat VM 3 Bulan Habis

Bila nanti Anda membuat server baru di penyedia hosting mana pun:

1. **Pasang Stack Docker Anda:**
   Salin folder `/opt/app-data` (atau jalankan backup) dan jalankan `docker compose up -d`.
2. **Pasang Cloudflare Tunnel (1 Perintah):**
   Jalankan perintah ini di server baru:
   ```bash
   curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
   echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared noble main' | sudo tee /etc/apt/sources.list.d/cloudflared.list
   sudo apt-get update && sudo apt-get install -y cloudflared
   sudo cloudflared service install eyJhIjoiMzlmNDkwYThhOWNiZGNhM2VjYTk0N2EzM2RiNjFiMjkiLCJ0IjoiMDQ3Njk5NGItYTQ0Zi00NzE1LTkxODUtYjRhYWVmNDI3YmZmIiwicyI6InpjL1BrZjNKamtSTFRLTXJFVVZLYmt6QjUxdXFXNGphVHVaWk92QnhhR1RmN3BEZCtWRGxXa1E0U0p2cHlmQVp4dzdoSG1YSFArMmVlQUtERUFnOTh3PT0ifQ==
   ```
3. **Selesai!** 
   Seluruh traffic dari `ohana.biz.id` akan langsung tersambung ke server baru dalam hitungan detik tanpa perlu mengubah DNS record.
