#!/usr/bin/env bash
# BanuDesk server setup for Ubuntu 22.04/24.04.
# Usage:  sudo ./setup.sh remote.bandirma.edu.tr      (or the server's public IP)
set -euo pipefail

HOST="${1:-}"
if [[ -z "$HOST" ]]; then
  echo "Usage: sudo $0 <public hostname or IP of this server>" >&2
  exit 1
fi
if [[ $EUID -ne 0 ]]; then
  echo "Run with sudo." >&2
  exit 1
fi
cd "$(dirname "$0")"

# 1. Docker
if ! command -v docker >/dev/null 2>&1; then
  echo "Installing Docker..."
  apt-get update -y
  apt-get install -y ca-certificates curl
  curl -fsSL https://get.docker.com | sh
fi

# 2. Settings file (kept if it already exists, so re-running is safe)
if [[ ! -f .env ]]; then
  JWT=$(head -c 32 /dev/urandom | base64 | tr -d '/+=' | head -c 40)
  printf 'SERVER_HOST=%s\nJWT_KEY=%s\n' "$HOST" "$JWT" > .env
  chmod 600 .env
else
  sed -i "s/^SERVER_HOST=.*/SERVER_HOST=$HOST/" .env
fi

# 3. Firewall (handles ufw and Oracle Cloud iptables)
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
  ufw allow 21114:21119/tcp
  ufw allow 21116/udp
fi

if command -v iptables >/dev/null 2>&1; then
  echo "Configuring iptables rules..."
  iptables -I INPUT 1 -p tcp -m multiport --dports 21114:21119 -j ACCEPT 2>/dev/null || true
  iptables -I INPUT 1 -p udp --dport 21116 -j ACCEPT 2>/dev/null || true
  if command -v netfilter-persistent >/dev/null 2>&1; then
    netfilter-persistent save 2>/dev/null || true
  fi
fi

# 4. Start
docker compose up -d
echo "Waiting for the key to be generated..."
for _ in $(seq 1 30); do
  [[ -s data/server/id_ed25519.pub ]] && break
  sleep 2
done
if [[ ! -s data/server/id_ed25519.pub ]]; then
  echo "Key not found. Check: docker logs banudesk-server" >&2
  exit 1
fi

echo
echo "================ BanuDesk server is running ================"
echo "Put these into GitHub > your fork > Settings > Secrets and variables > Actions:"
echo "  BANUDESK_ID_SERVER  = $HOST"
echo "  BANUDESK_KEY        = $(cat data/server/id_ed25519.pub)"
echo "  BANUDESK_API_SERVER = http://$HOST:21114"
echo
echo "Web admin: http://$HOST:21114/_admin/   (user: admin)"
echo "Admin password: look for it in   docker logs banudesk-server"
echo "Reset it with:  docker exec banudesk-server ./apimain reset-admin-pwd <new-password>  (path may differ by image version)"
echo "Back up ./data and .env. Losing data/server/id_ed25519 means rebuilding every client."
