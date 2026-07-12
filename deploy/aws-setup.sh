#!/usr/bin/env bash
# =============================================================================
# aws-setup.sh — EC2 Bootstrap Script for My-Blog
# =============================================================================
# Run this ONCE on a fresh Ubuntu 24.04 LTS EC2 instance after SSH-ing in.
# Usage:
#   chmod +x aws-setup.sh && sudo ./aws-setup.sh
# =============================================================================

set -euo pipefail

REPO_URL="https://github.com/YOUR_GITHUB_USERNAME/My-Blog.git"  # <-- UPDATE THIS
APP_DIR="/opt/myblog"
APP_USER="ubuntu"

echo "=============================================="
echo " My-Blog AWS EC2 Bootstrap"
echo "=============================================="

# ── 1. System Update ──────────────────────────────
echo "[1/6] Updating system packages..."
apt-get update -y && apt-get upgrade -y

# ── 2. Install Docker ─────────────────────────────
echo "[2/6] Installing Docker & Plugins..."
apt-get install -y ca-certificates curl gnupg git

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Allow ubuntu user to run docker without sudo
usermod -aG docker "$APP_USER"

echo "  Docker: $(docker --version)"
echo "  Compose Plugin: $(docker compose version)"

# ── 3. Clone Repository ───────────────────────────
echo "[3/6] Cloning repository to ${APP_DIR}..."
if [ -d "$APP_DIR" ]; then
    echo "  Directory exists — pulling latest..."
    git -C "$APP_DIR" pull || true
else
    # Allow failure if repo not configured yet
    git clone "$REPO_URL" "$APP_DIR" || echo "  Warning: Clone failed. Please clone manually to ${APP_DIR} later."
fi

# Ensure correct permissions
if [ -d "$APP_DIR" ]; then
    chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
fi

# ── 4. Configure Firewall (UFW) ───────────────────
echo "[4/6] Configuring UFW firewall..."
apt-get install -y ufw
ufw --force enable
ufw allow ssh
ufw allow 80/tcp
ufw status

# ── 5. Setup empty logs directory ─────────────────
echo "[5/6] Creating application directories..."
mkdir -p "${APP_DIR}/logs" || true
if [ -d "$APP_DIR" ]; then
    chown -R "$APP_USER":"$APP_USER" "${APP_DIR}/logs"
fi

# ── 6. Done ───────────────────────────────────────
echo ""
echo "[6/6] Bootstrap complete!"
echo ""
echo "Next steps:"
echo "  1. cd ${APP_DIR}"
echo "  2. cp .env.production.example .env.production"
echo "  3. edit .env.production       # fill in SECRET_KEY and AWS_REGION etc."
echo "  4. docker compose -f docker-compose.prod.yml up -d --build"
echo "  5. Visit http://\$(curl -s ifconfig.me)"
echo ""
echo "  To view logs:    docker compose -f docker-compose.prod.yml logs -f"
echo "  To stop:         docker compose -f docker-compose.prod.yml down"
