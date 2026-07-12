# Setup

How to get this pixel-art profile live on GitHub.

## 1. Create the special profile repo

On GitHub, create a **public** repo named **exactly your username** (e.g.
`github.com/yourname/yourname`). GitHub shows its `README.md` on your profile
page.

## 2. Fill in your username

The README uses `YOURUSERNAME` as a placeholder in the stats-card and snake
URLs. Replace it:

```sh
sed -i '' 's/YOURUSERNAME/your-actual-username/g' README.md
```

## 3. Personalize

- **Banner name/subtitle** — regenerate the art:
  ```sh
  python3 scripts/generate_pixel_art.py --name JIM --subtitle "WELCOME TO MY PROFILE"
  ```
  (Only A-Z, spaces and `, . ' ! -` are supported by the pixel font.)
- **Pixelate a photo** (e.g. for a retro avatar) — requires Pillow:
  ```sh
  python3 scripts/pixelate.py photo.jpg -o assets/avatar.svg --width 48 --palette pico8
  ```
  See `python3 scripts/pixelate.py --help` for palettes, dithering and PNG output.
- **About Me / Tech Stack** — edit `README.md` directly.

## 4. Push

```sh
git add -A
git commit -m "pixel art profile"
git remote add origin git@github.com:yourname/yourname.git
git push -u origin main
```
