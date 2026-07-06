#!/usr/bin/env bash
# render_cover.sh — helpers around the headless cover render.
# The actual screenshot happens via the Playwright MCP browser tools (resize -> navigate ->
# take_screenshot); this script handles the shell side: serving the folder and collecting the PNG.
#
# Usage:
#   render_cover.sh serve <dir> [port]     start a localhost server for the cover folder
#   render_cover.sh collect <dest.png>     copy the newest Playwright screenshot to <dest.png>
#   render_cover.sh stop [port]            stop the server (default port 8731)
set -euo pipefail

cmd="${1:-}"; shift || true
port_default=8731

case "$cmd" in
  serve)
    dir="${1:?usage: render_cover.sh serve <dir> [port]}"
    port="${2:-$port_default}"
    ( cd "$dir" && python3 -m http.server "$port" >/dev/null 2>&1 & )
    sleep 1
    code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port/" || true)
    echo "serving $dir on http://localhost:$port (status $code)"
    ;;
  collect)
    dest="${1:?usage: render_cover.sh collect <dest.png>}"
    # Playwright MCP writes screenshots into a .playwright-mcp dir under its cwd.
    src=$(find . "$HOME" -maxdepth 4 -path '*/.playwright-mcp/*.png' -newerct '-10 minutes' 2>/dev/null \
          | xargs -I{} stat -f '%m {}' {} 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2- || true)
    if [ -z "${src:-}" ]; then
      # GNU stat fallback (linux)
      src=$(find . "$HOME" -maxdepth 4 -path '*/.playwright-mcp/*.png' -newermt '-10 minutes' 2>/dev/null \
            | xargs -I{} stat -c '%Y {}' {} 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2- || true)
    fi
    [ -n "${src:-}" ] || { echo "no recent screenshot found under a .playwright-mcp dir" >&2; exit 1; }
    mkdir -p "$(dirname "$dest")"
    cp "$src" "$dest"
    echo "collected $src -> $dest ($(wc -c < "$dest" | tr -d ' ') bytes)"
    ;;
  stop)
    port="${1:-$port_default}"
    pkill -f "http.server $port" 2>/dev/null || true
    echo "stopped server on port $port (if it was running)"
    ;;
  *)
    grep '^#' "$0" | head -8; exit 1;;
esac
