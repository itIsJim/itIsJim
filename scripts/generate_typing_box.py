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
    """message typed out dot by dot; accent_word (if found) gets the
    accent color."""
    ink, accent, frame = THEMES[theme]
    tw = text_cells(message)
    w_cells = tw + 2 * PAD
    h_cells = 5 + 2 * PAD
    W, H = w_cells * CELL, h_cells * CELL

    el = []
    # dotted frame
    step = 2
    for x in range(0, w_cells + 1, step):
        el.append(f'<circle cx="{(x + .5) * CELL:g}" cy="{.5 * CELL:g}" r="{DOT_R}" fill="{frame}"/>')
        el.append(f'<circle cx="{(x + .5) * CELL:g}" cy="{(h_cells - .5) * CELL:g}" r="{DOT_R}" fill="{frame}"/>')
    for y in range(step, h_cells - 1, step):
        el.append(f'<circle cx="{.5 * CELL:g}" cy="{(y + .5) * CELL:g}" r="{DOT_R}" fill="{frame}"/>')
        el.append(f'<circle cx="{(w_cells - .5) * CELL:g}" cy="{(y + .5) * CELL:g}" r="{DOT_R}" fill="{frame}"/>')

    # find accent range (character indices of accent_word in message)
    a0 = message.find(accent_word) if accent_word else -1
    a1 = a0 + len(accent_word) - 1 if a0 >= 0 else -2

    x = PAD
    delay = 0.4
    for i, ch in enumerate(message):
        color = accent if a0 <= i <= a1 else ink
        dots = dots_for_glyph(ch, x, PAD, color)
        if dots:
            el.append(f'<g class="ch" style="animation-delay:{delay:.2f}s">'
                      + "".join(dots) + "</g>")
        delay += TYPE_DELAY
        x += glyph_w(ch) + 1

    # blinking cursor after the text, dotted block 2 cells wide
    cur = []
    for dy in range(5):
        for dx in range(2):
            cur.append(f'<circle cx="{(x + dx + 0.5) * CELL:g}" '
                       f'cy="{(PAD + dy + 0.5) * CELL:g}" r="{DOT_R}" fill="{ink}"/>')
    el.append(f'<g class="cursor" style="animation-delay:{delay:.2f}s">'
              + "".join(cur) + "</g>")

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
        typing_box("HELLO, IT IS JIM. WELCOME!", "JIM", theme,
                   f"assets/typing-box-{theme}.svg")
        for label in ("WEBSITE", "LINKEDIN", "EMAIL"):
            button(label, theme, f"assets/btn-{label.lower()}-{theme}.svg")
