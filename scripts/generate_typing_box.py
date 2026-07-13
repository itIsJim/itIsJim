#!/usr/bin/env python3
"""Generate the dotted typing-box SVGs for the profile README.

A message is drawn as a dot-matrix (same dotted feel as the braille art),
revealed character by character like someone typing, inside a dotted box,
with a blinking cursor. Emits light + dark variants plus dotted link
buttons, meant to be wired together with <picture> tags in the README.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from generate_pixel_art import GLYPHS, glyph_w  # noqa: E402

CELL = 7          # px per font cell
DOT_R = 2.4       # dot radius
PAD = 4           # box padding, in cells
TYPE_DELAY = 0.09 # seconds per typed character

THEMES = {
    # ink, accent (for the name), frame
    "light": ("#24292f", "#0969da", "#d0d7de"),
    "dark":  ("#e6edf3", "#58a6ff", "#30363d"),
}

STYLE = """
  .ch { opacity: 0; animation: appear .01s steps(1) forwards; }
  .cursor { opacity: 0; animation: caret 1.06s steps(1) infinite; }
  @keyframes appear { to { opacity: 1; } }
  @keyframes caret { 0%, 49% { opacity: 1; } 50%, 100% { opacity: 0; } }
  @media (prefers-reduced-motion: reduce) {
    .ch { animation: none; opacity: 1; }
    .cursor { animation: none; opacity: 1; }
  }
"""


def dots_for_glyph(ch, ox, oy, color, scale=1):
    """Circles for one glyph; ox/oy in cells."""
    out = []
    for gy, row in enumerate(GLYPHS[ch]):
        for gx, cell in enumerate(row):
            if cell == "#":
                cx = (ox + gx * scale + 0.5) * CELL
                cy = (oy + gy * scale + 0.5) * CELL
                out.append(f'<circle cx="{cx:g}" cy="{cy:g}" '
                           f'r="{DOT_R * scale:g}" fill="{color}"/>')
    return out


def text_cells(s):
    return sum(glyph_w(ch) + 1 for ch in s) - 1


def typing_box(message, accent_word, theme, out):
    """message typed out character by character in a normal (system
    monospace) font inside a plain outlined box; accent_word (if found)
    gets the accent color."""
    ink, accent, frame = THEMES[theme]
    fs = 26                    # font size
    adv = fs * 0.62            # per-character advance
    pad_x, pad_y = 30, 24
    W = round(len(message) * adv + adv * 1.6 + 2 * pad_x)
    H = fs + 2 * pad_y
    baseline = pad_y + fs * 0.78
    font = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

    el = [f'<rect x="1.5" y="1.5" width="{W - 3}" height="{H - 3}" rx="10" '
          f'fill="none" stroke="{frame}" stroke-width="2"/>']

    a0 = message.find(accent_word) if accent_word else -1
    a1 = a0 + len(accent_word) - 1 if a0 >= 0 else -2

    delay = 0.4
    for i, ch in enumerate(message):
        if ch != " ":
            color = accent if a0 <= i <= a1 else ink
            x = pad_x + i * adv
            c = ch.replace("&", "&amp;").replace("<", "&lt;")
            el.append(f'<text x="{x:.1f}" y="{baseline:.1f}" class="ch" '
                      f'style="animation-delay:{delay:.2f}s" fill="{color}" '
                      f'font-family="{font}" font-size="{fs}">{c}</text>')
        delay += TYPE_DELAY

    # blinking block cursor after the text
    cx = pad_x + len(message) * adv + 3
    el.append(f'<rect x="{cx:.1f}" y="{baseline - fs * 0.75:.1f}" '
              f'width="{adv * 0.8:.1f}" height="{fs * 0.92:.1f}" fill="{ink}" '
              f'class="cursor" style="animation-delay:{delay:.2f}s"/>')

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}" role="img" aria-label="{message}">'
           f"<style>{STYLE}</style>" + "".join(el) + "</svg>")
    with open(out, "w") as f:
        f.write(svg)
    print(f"wrote {out} ({W}x{H})")


def button(label, theme, out):
    ink, _, _ = THEMES[theme]
    tw = text_cells(label)
    W, H = (tw + 2) * CELL, 7 * CELL
    el = []
    x = 1
    for ch in label:
        el += dots_for_glyph(ch, x, 1, ink)
        x += glyph_w(ch) + 1
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}" role="img" aria-label="{label}">'
           + "".join(el) + "</svg>")
    with open(out, "w") as f:
        f.write(svg)
    print(f"wrote {out} ({W}x{H})")


if __name__ == "__main__":
    os.makedirs("assets", exist_ok=True)
    for theme in THEMES:
        typing_box("Hello, it is Jim. Welcome!", "Jim", theme,
                   f"assets/typing-box-{theme}.svg")
        for label in ("WEBSITE", "LINKEDIN", "EMAIL"):
            button(label, theme, f"assets/btn-{label.lower()}-{theme}.svg")
