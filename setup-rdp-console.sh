#!/usr/bin/env bash
set -euo pipefail

echo "=== [1/4] Menginstall ttyd (Web Terminal Console) ==="
if ! command -v ttyd &> /dev/null; then
    curl -Lo /usr/local/bin/ttyd https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64
    chmod +x /usr/local/bin/ttyd
fi

# Buat service ttyd untuk OpenBot Web Console di port 7681 dengan autentikasi
cat << 'EOF' > /etc/systemd/system/openbot-console.service
[Unit]
Description=OpenBot Web Terminal Console for Laptop & Tablet
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/app-data/openbot
ExecStart=/usr/local/bin/ttyd -p 7681 -c admin:admin123 -t fontSize=15 -t theme={'background':'#090d16'} bash
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now openbot-console

echo "=== [2/4] Menginstall Lingkungan Desktop XFCE4 & xRDP ==="
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y xfce4 xfce4-goodies xrdp dbus-x11

# Konfigurasi xRDP agar default menggunakan session XFCE
echo "xfce4-session" > /home/eardisis/.xsession
chown eardisis:eardisis /home/eardisis/.xsession
adduser xrdp ssl-cert || true

# Set password user eardisis untuk Remote Desktop
echo "eardisis:admin123" | chpasswd

systemctl enable --now xrdp

echo "=== [3/4] Konfigurasi Selesai ==="
systemctl restart xrdp
systemctl restart openbot-console
