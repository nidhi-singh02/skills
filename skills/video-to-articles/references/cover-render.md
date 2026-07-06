# Cover: render, imagery, fonts

## Render the cover (headless)

Pick a template (usually `cover-text-template.html`; `cover-template.html` only for an A→B→C
system), copy it to a working dir as `cover.html` along with `departure.woff2` and any imagery.
`file://` is blocked in the Playwright MCP browser, so serve over localhost. The
`scripts/render_cover.sh` helper wraps the serve/collect/stop shell steps
(`render_cover.sh serve <dir>`, then after the screenshot `render_cover.sh collect <dest.png>`,
then `render_cover.sh stop`); the manual equivalent is:

```bash
cd <cover-working-dir>
python3 -m http.server 8731 --bind 127.0.0.1 >/dev/null 2>&1 &   # loopback-only (or: render_cover.sh serve .)
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8731/cover.html   # expect 200
```

Then with the Playwright browser tools:
1. `browser_resize` → width 1600, height 900 (Medium featured: 1600×840).
2. `browser_navigate` → `http://localhost:8731/cover.html`.
3. `browser_take_screenshot` → `fullPage: true`.
4. **Read the screenshot and actually look at it.** Iterate on the HTML, re-navigate, re-screenshot
   until it's clean. Then copy the PNG to `blog/assets/<platform>_cover.png` (e.g. `x_cover.png`,
   `medium_cover.png`), so a multi-platform run doesn't overwrite one cover with another.
5. Kill the server (`pkill -f "http.server 8731"`) and clean up the `.playwright-mcp/` dir.

Tip: the screenshot saves into a `.playwright-mcp/` dir under the browser's cwd. `find` it, `cp` out.

## Verify the cover
- Shrink to ~540px wide and view → headline + accent legible at feed/thumbnail size?
- Centre-crop to 1.91:1 (link-card crop) and view → nothing important lost, only empty margin.
  (On macOS, run each check on a FRESH copy of the full-size PNG since `sips` edits in place:
  `cp cover.png small.png && sips -Z 540 small.png` for legibility, and
  `cp cover.png crop.png && sips -c 838 1600 crop.png` for the crop; any image tool works elsewhere.)

## Sourcing cover imagery
Most covers need NO imagery. Choose by video type:
- **Type-only** (essays, opinion, and most topics): no imagery. Use `cover-text-template.html`.
- **A hero photo or the video's own best frame** (cooking, travel, product demo, lifestyle): one
  clean image behind or beside the headline. A real frame beats any icon. Use the commented
  `HERO PHOTO` block in `cover-text-template.html` (a full-bleed `<img>` + scrim under the type).
- **Brand logos** (dev / product / tool topics, or an A→B→C system diagram): run
  `scripts/fetch_logo.sh <domain-or-url> [out-basename]`: it tries the conventional root paths
  best-first (`/safari-pinned-tab.svg` mono silhouette → `/apple-touch-icon.png` /
  `/android-chrome-512*.png` full colour) then falls back to scraping the homepage for candidates.
  If it finds nothing, try the GitHub repo or a header screenshot as a last resort.
  Recolour a black logo to white **only on a dark cover**:
  `filter:brightness(0) invert(1)` (see `.invert` in the template). A logo that is itself a coloured
  circle works as a node as-is; a detailed dark illustration needs a LIGHT disc behind it (`.disc.light`).

## Choosing a display font
`assets/departure.woff2` is **Departure Mono**, a pixel font by Helena Zhang & Tobias Fried (MIT),
bundled and set as the default `--display`. It suits dev/technical topics. For other topics, swap
`--display` in the template to something that fits the subject: a warm serif for essays/lifestyle, a
clean geometric sans for product/SaaS. You normally never need to refetch the font; canonical copies
live at https://departuremono.com.
