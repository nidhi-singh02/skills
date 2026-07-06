#!/usr/bin/env bash
# fetch_logo.sh — grab a usable brand mark from a product site, best-first.
#
# Usage: fetch_logo.sh <domain-or-url> [out-basename]
#   e.g. fetch_logo.sh ollama.com ollama_logo
#
# Tries, in order: /safari-pinned-tab.svg (mono silhouette, easy to recolour),
# /apple-touch-icon.png, /android-chrome-512x512.png, /favicon.png. Falls back to
# listing every .svg/.png referenced on the homepage so you can pick one manually.
set -euo pipefail

raw="${1:?usage: fetch_logo.sh <domain-or-url> [out-basename]}"
out="${2:-logo}"
host="${raw#*://}"; host="${host%%/*}"
base="https://$host"

try() { # url ext
  local url="$1" ext="$2" f="$out.$2"
  local code; code=$(curl -s -L --connect-timeout 5 --max-time 20 -o "$f" -w "%{http_code}" "$url" || echo 000)
  if [ "$code" = "200" ] && [ -s "$f" ] && [ "$(wc -c < "$f")" -gt 500 ] \
     && ! grep -qi "<html" "$f" 2>/dev/null; then
    echo "saved $f  ($(wc -c < "$f" | tr -d ' ') bytes)  <- $url"
    exit 0
  fi
  rm -f "$f"
}

# stage 1: conventional root paths
try "$base/safari-pinned-tab.svg"      svg
try "$base/apple-touch-icon.png"       png
try "$base/android-chrome-512x512.png" png
try "$base/favicon.png"                png

# stage 2: scrape the homepage and auto-try candidates by priority
name="${host%%.*}"
cands=$(curl -s -L --connect-timeout 5 --max-time 20 "$base" | grep -oiE '(src|href)="[^"]*\.(svg|png)"' \
        | sed -E 's/^(src|href)="//; s/"$//' | sort -u || true)
for pat in apple-touch-icon android-chrome-512 android-chrome "$name" -logo logo pinned; do
  hit=$(printf '%s\n' "$cands" | grep -i -- "$pat" | head -1 || true)
  [ -n "$hit" ] || continue
  case "$hit" in
    http*) url="$hit";;
    //*)   url="https:$hit";;          # protocol-relative //cdn.example/logo.png
    /*)    url="$base$hit";;
    *)     url="$base/$hit";;
  esac
  ext="${url##*.}"
  try "$url" "$ext"
done

echo "no usable mark found at $base; homepage candidates were:" >&2
printf '%s\n' "$cands" | head -20 >&2
exit 1
