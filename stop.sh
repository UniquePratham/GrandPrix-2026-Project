#!/usr/bin/env bash
# Stop all background services (FastAPI backend and Cloudflare tunnel)

echo "🛑 Stopping Silent Co-Driver background services..."
tmux kill-session -t f1-backend 2>/dev/null && echo "✓ Backend stopped." || echo "- Backend was not running."
tmux kill-session -t f1-tunnel 2>/dev/null && echo "✓ Cloudflare tunnel stopped." || echo "- Tunnel was not running."
echo "✅ All services stopped."
