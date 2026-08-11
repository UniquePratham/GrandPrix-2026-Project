#!/usr/bin/env bash
# ==============================================================================
# 🏎️ SILENT CO-DRIVER — VULTR CLOUD DEPLOYMENT & PERSISTENT TUNNEL SCRIPT
# Runs 24/7 in background even after closing SSH connection
# ==============================================================================

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}"
echo "======================================================================"
echo "🏎️  SILENT CO-DRIVER — 24/7 BACKGROUND CLOUD DEPLOYMENT"
echo "======================================================================"
echo -e "${NC}"

# 1. Update system packages
echo -e "${CYAN}>> [1/5] Updating packages and tools...${NC}"
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

# 3. Install project dependencies
echo -e "${CYAN}>> [3/5] Installing project dependencies from requirements.txt...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# 4. Install Cloudflare Tunnel CLI (cloudflared)
echo -e "${CYAN}>> [4/5] Checking Cloudflare Tunnel (cloudflared)...${NC}"
if ! command -v cloudflared &> /dev/null; then
    curl -L --output /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    dpkg -i /tmp/cloudflared.deb || apt-get install -f -y
    rm -f /tmp/cloudflared.deb
    echo -e "${GREEN}✓ Cloudflare CLI installed.${NC}"
else
    echo -e "${GREEN}✓ Cloudflare CLI is already installed.${NC}"
fi

# 5. Start Backend in persistent detached tmux session
echo -e "${CYAN}>> [5/5] Launching Persistent Background Services...${NC}"

# Kill previous sessions if any
tmux kill-session -t f1-backend 2>/dev/null || true
tmux kill-session -t f1-tunnel 2>/dev/null || true

# Start FastAPI backend
tmux new-session -d -s f1-backend "cd '$REPO_DIR' && source venv/bin/activate && uvicorn backend.app:app --host 0.0.0.0 --port 8000"
echo -e "${GREEN}✓ FastAPI backend started in background session [f1-backend].${NC}"

sleep 3

# Start Cloudflare Tunnel in background session and log output
rm -f "$REPO_DIR/tunnel.log"
tmux new-session -d -s f1-tunnel "cloudflared tunnel --url http://localhost:8000 2>&1 | tee '$REPO_DIR/tunnel.log'"
echo -e "${GREEN}✓ Cloudflare tunnel started in background session [f1-tunnel].${NC}"

# Wait for tunnel URL to generate
echo -e "${YELLOW}>> Generating your public HTTPS URL (waiting 6 seconds)...${NC}"
sleep 6

TUNNEL_URL=""
for i in {1..10}; do
    if [ -f "$REPO_DIR/tunnel.log" ]; then
        TUNNEL_URL=$(grep -o 'https://[-a-zA-Z0-9.]*\.trycloudflare\.com' "$REPO_DIR/tunnel.log" | head -n 1 || true)
        if [ -n "$TUNNEL_URL" ]; then
            break
        fi
    fi
    sleep 2
done

echo ""
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}🎉 DEPLOYMENT SUCCESSFUL — RUNNING 24/7 IN BACKGROUND!${NC}"
echo -e "${GREEN}======================================================================${NC}"
if [ -n "$TUNNEL_URL" ]; then
    echo -e "${CYAN}🌐 YOUR PUBLIC CLOUDFLARE URL:${NC}"
    echo -e "${GREEN}${TUNNEL_URL}${NC}"
else
    echo -e "${YELLOW}Tunnel is initializing. Check URL anytime with: ./status.sh${NC}"
fi
echo -e "${GREEN}======================================================================${NC}"
echo -e "${YELLOW}ℹ️  YOU CAN SAFELY CLOSE THIS SSH WINDOW NOW.${NC}"
echo -e "   The server and tunnel will stay permanently active in background."
echo ""
echo -e "   Useful commands on VM:"
echo -e "   - Check URL & Status:  ${CYAN}./status.sh${NC}"
echo -e "   - Stop all services:   ${CYAN}./stop.sh${NC}"
echo -e "${GREEN}======================================================================${NC}"
