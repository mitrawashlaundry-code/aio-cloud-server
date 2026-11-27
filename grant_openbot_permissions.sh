#!/usr/bin/env bash
set -e

# 1. Tambahkan openbot ke grup docker
usermod -aG docker openbot

# 2. Buat konfigurasi sudoers NOPASSWD untuk openbot
cat << 'EOF' > /etc/sudoers.d/openbot
openbot ALL=(ALL) NOPASSWD: ALL
EOF
chmod 0440 /etc/sudoers.d/openbot

# 3. Validasi sintaks sudoers
visudo -c -f /etc/sudoers.d/openbot

# 4. Berikan akses baca/tulis ke direktori /opt/app-data
chmod -R 775 /opt/app-data
chown -R root:docker /opt/app-data

echo "--- TEST WHOAMI SUDO ---"
sudo -u openbot sudo -n whoami

echo "--- TEST DOCKER ---"
sudo -u openbot docker ps --format "table {{.Names}}\t{{.Status}}"

echo "--- RESTART OPENBOT SERVICE ---"
systemctl restart openbot

echo "STATUS_SUCCESS"
