#!/usr/bin/env bash
set -euo pipefail

echo "=== [1/6] Mengaktifkan TCP BBR ==="
cat << 'EOF' | sudo tee /etc/sysctl.d/99-bbr.conf
net.core.default_qdisc=fq
net.ipv4.tcp_congestion_control=bbr
net.ipv4.ip_forward=1
net.ipv6.conf.all.forwarding=1
EOF
sudo sysctl --system

echo "=== [2/6] Memperbarui sistem dan menginstall dependensi dasar ==="
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg lsb-release unzip tar jq openssl ufw

echo "=== [3/6] Menginstall Docker Engine & Docker Compose Plugin ==="
if ! command -v docker &> /dev/null; then
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo systemctl enable --now docker
    sudo usermod -aG docker "$USER" || true
fi

echo "=== [4/6] Membuat struktur direktori /opt/app-data/ ==="
sudo mkdir -p /opt/app-data/portainer
sudo mkdir -p /opt/app-data/adguard/work /opt/app-data/adguard/conf
sudo mkdir -p /opt/app-data/rustdesk
sudo mkdir -p /opt/app-data/openbot
sudo mkdir -p /opt/app-data/anythingllm
sudo mkdir -p /opt/app-data/metube/downloads
sudo mkdir -p /opt/app-data/filebrowser/data
sudo mkdir -p /opt/app-data/filebrowser/database
sudo mkdir -p /opt/app-data/sing-box

sudo touch /opt/app-data/filebrowser/database/filebrowser.db
sudo chmod -R 777 /opt/app-data/filebrowser
sudo chmod -R 777 /opt/app-data/metube/downloads

echo "=== [5/6] Menginstall & Menyiapkan sing-box (VLESS Reality) ==="
SINGBOX_VER=$(curl -s https://api.github.com/repos/SagerNet/sing-box/releases/latest | jq -r .tag_name | tr -d 'v')
if [ -z "$SINGBOX_VER" ] || [ "$SINGBOX_VER" == "null" ]; then
    SINGBOX_VER="1.11.2"
fi

if [ ! -f /usr/local/bin/sing-box ]; then
    curl -Lo /tmp/sing-box.tar.gz "https://github.com/SagerNet/sing-box/releases/download/v${SINGBOX_VER}/sing-box-${SINGBOX_VER}-linux-amd64.tar.gz"
    tar -zxvf /tmp/sing-box.tar.gz -C /tmp/
    sudo mv /tmp/sing-box-${SINGBOX_VER}-linux-amd64/sing-box /usr/local/bin/sing-box
    sudo chmod +x /usr/local/bin/sing-box
    rm -rf /tmp/sing-box*
fi

# Generate Keypair Reality & UUID
KEYPAIR=$(sing-box generate reality-keypair)
PRIVATE_KEY=$(echo "$KEYPAIR" | grep -i "PrivateKey:" | awk '{print $2}')
PUBLIC_KEY=$(echo "$KEYPAIR" | grep -i "PublicKey:" | awk '{print $2}')
UUID=$(sing-box generate uuid)
SHORT_ID=$(openssl rand -hex 8)

cat << EOF | sudo tee /opt/app-data/sing-box/config.json
{
  "log": {
    "level": "info",
    "timestamp": true
  },
  "inbounds": [
    {
      "type": "vless",
      "tag": "vless-in",
      "listen": "::",
      "listen_port": 443,
      "users": [
        {
          "uuid": "${UUID}",
          "flow": "xtls-rprx-vision"
        }
      ],
      "tls": {
        "enabled": true,
        "server_name": "gateway.icloud.com",
        "reality": {
          "enabled": true,
          "handshake": {
            "server": "gateway.icloud.com",
            "server_port": 443
          },
          "private_key": "${PRIVATE_KEY}",
          "short_id": [
            "${SHORT_ID}"
          ]
        }
      }
    }
  ],
  "outbounds": [
    {
      "type": "direct",
      "tag": "direct"
    }
  ]
}
EOF

cat << 'EOF' | sudo tee /etc/systemd/system/sing-box.service
[Unit]
Description=sing-box service
Documentation=https://sing-box.sagernet.org
After=network.target nss-lookup.target

[Service]
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE CAP_NET_RAW
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE CAP_NET_RAW
ExecStart=/usr/local/bin/sing-box run -c /opt/app-data/sing-box/config.json
Restart=on-failure
RestartSec=5s
LimitNOFILE=infinity

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now sing-box

echo "=== [6/6] Menyiapkan docker-compose.yml 7 Aplikasi ==="
cat << 'EOF' | sudo tee /opt/app-data/docker-compose.yml
services:
  # 1. Portainer CE (Port 9000)
  portainer:
    image: portainer/portainer-ce:latest
    container_name: portainer
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    ports:
      - "9000:9000"
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /opt/app-data/portainer:/data

  # 2. AdGuard Home (Port 3000 Web UI)
  adguardhome:
    image: adguard/adguardhome:latest
    container_name: adguardhome
    restart: unless-stopped
    ports:
      - "3000:3000/tcp"
    volumes:
      - /opt/app-data/adguard/work:/opt/adguardhome/work
      - /opt/app-data/adguard/conf:/opt/adguardhome/conf

  # 3. RustDesk Server (hbbs & hbbr)
  rustdesk-hbbs:
    image: rustdesk/rustdesk-server:latest
    container_name: rustdesk-hbbs
    command: hbbs -r 0.0.0.0:21117
    restart: unless-stopped
    ports:
      - "21115:21115"
      - "21116:21116"
      - "21116:21116/udp"
      - "21118:21118"
    volumes:
      - /opt/app-data/rustdesk:/root
    depends_on:
      - rustdesk-hbbr

  rustdesk-hbbr:
    image: rustdesk/rustdesk-server:latest
    container_name: rustdesk-hbbr
    command: hbbr
    restart: unless-stopped
    ports:
      - "21117:21117"
      - "21119:21119"
    volumes:
      - /opt/app-data/rustdesk:/root

  # 4. OpenBot (Agent Engine)
  openbot:
    image: alpine:latest
    container_name: openbot
    restart: unless-stopped
    command: sh -c "echo 'OpenBot workspace ready' > /data/README.txt && tail -f /dev/null"
    volumes:
      - /opt/app-data/openbot:/data

  # 5. AnythingLLM (Port 3001)
  anythingllm:
    image: mintplexlabs/anything-llm:latest
    container_name: anythingllm
    restart: unless-stopped
    ports:
      - "3001:3001"
    environment:
      - STORAGE_DIR=/app/server/storage
    volumes:
      - /opt/app-data/anythingllm:/app/server/storage

  # 6. MeTube (Port 8081)
  metube:
    image: ghcr.io/alexta69/metube:latest
    container_name: metube
    restart: unless-stopped
    ports:
      - "8081:8081"
    volumes:
      - /opt/app-data/metube/downloads:/downloads

  # 7. FileBrowser (Port 8080)
  filebrowser:
    image: filebrowser/filebrowser:latest
    container_name: filebrowser
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      - /opt/app-data/filebrowser/data:/srv
      - /opt/app-data/filebrowser/database/filebrowser.db:/database/filebrowser.db
EOF

cd /opt/app-data
sudo docker compose pull
sudo docker compose up -d

echo "=== Output Parameter Penting ==="
echo "UUID=${UUID}"
echo "PUBLIC_KEY=${PUBLIC_KEY}"
echo "SHORT_ID=${SHORT_ID}"
echo "BBR_STATUS=$(sysctl net.ipv4.tcp_congestion_control)"
echo "SETUP_DONE"
