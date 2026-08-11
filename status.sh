#!/usr/bin/env bash
# Check status of 24/7 background services and print the public URL

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}=== SILENT CO-DRIVER SERVICE STATUS ===${NC}"

# Check backend
if tmux has-session -t f1-backend 2>/dev/null; then
    echo -e "Backend:  ${GREEN}[RUNNING]${NC}"
else
    echo -e "Backend:  ${RED}[STOPPED]${NC}"
fi

# Check tunnel
if tmux has-session -t f1-tunnel 2>/dev/null; then
    echo -e "Tunnel:   ${GREEN}[RUNNING]${NC}"
else
    echo -e "Tunnel:   ${RED}[STOPPED]${NC}"
fi

# Print URL
if [ -f "$REPO_DIR/tunnel.log" ]; then
    TUNNEL_URL=$(grep -o 'https://[-a-zA-Z0-9.]*\.trycloudflare\.com' "$REPO_DIR/tunnel.log" | head -n 1 || true)
    if [ -n "$TUNNEL_URL" ]; then
        echo ""
        echo -e "${CYAN}Public URL:${NC} ${GREEN}${TUNNEL_URL}${NC}"
    fi
fi
echo -e "${CYAN}=======================================${NC}"
