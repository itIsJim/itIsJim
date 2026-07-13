# Setup

This repo is the GitHub profile README for **itIsJim** — shown at
github.com/itIsJim because the repo is named after the account.

- `README.md` — hello line + Website / LinkedIn / Email buttons
- `assets/btn-*.svg` — dotted link buttons (light + dark, picked via `<picture>`)
- `scripts/generate_typing_box.py` — regenerates the buttons (and can make an
  animated typing-box banner if wanted)
- `scripts/pixelate.py` — photo → pixel art / ASCII / braille converter used
  for the art on [itisjim.github.io](https://itisjim.github.io); supports
  clickable links inside the art (`--link "URL|tooltip|@rows:cols"`)

Preview like GitHub renders it: `grip README.md` → http://localhost:6419
