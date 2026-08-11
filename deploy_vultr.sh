#!/usr/bin/env bash
# ==============================================================================
# 🏎️ SILENT CO-DRIVER — VULTR CLOUD DEPLOYMENT & CLOUDFLARE TUNNEL SCRIPT
# Automated setup for Ubuntu 22.04 / 24.04 LTS instances
# ==============================================================================

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "======================================================================"
echo "🏎️  SILENT CO-DRIVER — VULTR CLOUD DEPLOYMENT INITIALIZER"
echo "======================================================================"
echo -e "${NC}"

# 1. Update system packages
echo -e "${CYAN}>> [1/5] Updating system packages and installing prerequisites...${NC}"
apt-get update -y
apt-get install -y python3-pip python3-venv git curl tmux build-essential

# 2. Setup Python Virtual Environment
echo -e "${CYAN}>> [2/5] Setting up Python virtual environment...${NC}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 3. Upgrade pip and install requirements
echo -e "${CYAN}>> [3/5] Installing project dependencies from requirements.txt...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# 4. Install Cloudflare Tunnel CLI (cloudflared)
echo -e "${CYAN}>> [4/5] Installing Cloudflare Tunnel (cloudflared)...${NC}"
if ! command -v cloudflared &> /dev/null; then
    curl -L --output /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    dpkg -i /tmp/cloudflared.deb || apt-get install -f -y
    rm -f /tmp/cloudflared.deb
    echo -e "${GREEN}✓ Cloudflare CLI installed successfully.${NC}"
else
    echo -e "${GREEN}✓ Cloudflare CLI is already installed.${NC}"
fi

# 5. Start Backend Server in persistent tmux session
echo -e "${CYAN}>> [5/5] Launching FastAPI Backend & Cloudflare Tunnel...${NC}"
tmux kill-session -t f1-backend 2>/dev/null || true
tmux new-session -d -s f1-backend "cd '$REPO_DIR' && source venv/bin/activate && uvicorn backend.app:app --host 0.0.0.0 --port 8000"

sleep 3

# Verify backend health locally
if curl -s http://127.0.0.1:8000/api/health > /dev/null; then
    echo -e "${GREEN}✓ Backend is running and healthy on http://127.0.0.1:8000${NC}"
else
    echo -e "${RED}⚠️ Backend starting up, connecting tunnel...${NC}"
fi

echo ""
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}🚀 STARTING PUBLIC CLOUDFLARE HTTPS TUNNEL${NC}"
echo -e "${GREEN}Look below for your public URL (e.g. https://xxxx.trycloudflare.com):${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""

# Launch Cloudflare Tunnel (will output the live HTTPS URL directly)
cloudflared tunnel --url http://localhost:8000
