#!/usr/bin/env python3
"""Generate the pixel-art SVGs used by the profile README.

Usage:
    python3 scripts/generate_pixel_art.py --name JIM

Outputs assets/header.svg, assets/divider.svg, assets/footer.svg.
Everything is drawn on a grid of 8x8 "pixels" so it stays crisp and blocky.
"""
import argparse
import os
import random

U = 8  # screen px per art pixel

# PICO-8 palette
C = {
    "black":  "#000000",
    "navy":   "#1d2b53",
    "plum":   "#7e2553",
    "green":  "#008751",
    "brown":  "#ab5236",
    "dgray":  "#5f574f",
    "lgray":  "#c2c3c7",
    "white":  "#fff1e8",
    "red":    "#ff004d",
    "orange": "#ffa300",
    "yellow": "#ffec27",
    "lime":   "#00e436",
    "blue":   "#29adff",
    "lav":    "#83769c",
    "pink":   "#ff77a8",
    "peach":  "#ffccaa",
}
SKY_TOP = "#0e0e22"
SKY_MID = "#1d2b53"
SKY_LOW = "#2a2350"
SILHOUETTE = "#0a0a1f"
BUILDING = "#151b3c"

# 5-row pixel font, variable width
GLYPHS = {
    "A": [".#.", "#.#", "###", "#.#", "#.#"],
    "B": ["##.", "#.#", "##.", "#.#", "##."],
    "C": ["###", "#..", "#..", "#..", "###"],
    "D": ["##.", "#.#", "#.#", "#.#", "##."],
    "E": ["###", "#..", "##.", "#..", "###"],
    "F": ["###", "#..", "##.", "#..", "#.."],
    "G": ["###", "#..", "#.#", "#.#", "###"],
    "H": ["#.#", "#.#", "###", "#.#", "#.#"],
    "I": ["###", ".#.", ".#.", ".#.", "###"],
    "J": ["..#", "..#", "..#", "#.#", "###"],
    "K": ["#.#", "##.", "#..", "##.", "#.#"],
    "L": ["#..", "#..", "#..", "#..", "###"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#"],
    "N": ["#..#", "##.#", "#.##", "#..#", "#..#"],
    "O": ["###", "#.#", "#.#", "#.#", "###"],
    "P": ["###", "#.#", "###", "#..", "#.."],
    "Q": ["###", "#.#", "#.#", "###", "..#"],
    "R": ["##.", "#.#", "##.", "#.#", "#.#"],
    "S": ["###", "#..", "###", "..#", "###"],
    "T": ["###", ".#.", ".#.", ".#.", ".#."],
    "U": ["#.#", "#.#", "#.#", "#.#", "###"],
    "V": ["#.#", "#.#", "#.#", "#.#", ".#."],
    "W": ["#...#", "#...#", "#.#.#", "#.#.#", ".#.#."],
    "X": ["#.#", "#.#", ".#.", "#.#", "#.#"],
    "Y": ["#.#", "#.#", ".#.", ".#.", ".#."],
    "Z": ["###", "..#", ".#.", "#..", "###"],
    ",": ["..", "..", "..", ".#", "#."],
    "'": ["#", "#", ".", ".", "."],
    "!": ["#", "#", "#", ".", "#"],
    ".": [".", ".", ".", ".", "#"],
    "-": ["...", "...", "###", "...", "..."],
    " ": ["..", "..", "..", "..", ".."],
}

STYLE = """
  .blink   { animation: blink 1.1s steps(1) infinite; }
  .twinkle { animation: twinkle 2.6s ease-in-out infinite; }
  .win     { animation: winblink 4s steps(1) infinite; }
  .fa      { animation: frameA 1.2s steps(1) infinite; }
  .fb      { animation: frameB 1.2s steps(1) infinite; }
  .eyes    { animation: eyeblink 5s steps(1) infinite; }
  .shoot   { animation: shoot 9s linear infinite; }
  @keyframes blink    { 0%, 49% { opacity: 1; } 50%, 100% { opacity: 0; } }
  @keyframes twinkle  { 0%, 100% { opacity: 1; } 50% { opacity: 0.15; } }
  @keyframes winblink { 0%, 46% { opacity: 1; } 47%, 53% { opacity: 0.1; } 54%, 100% { opacity: 1; } }
  @keyframes frameA   { 0%, 49% { opacity: 1; } 50%, 100% { opacity: 0; } }
  @keyframes frameB   { 0%, 49% { opacity: 0; } 50%, 100% { opacity: 1; } }
  @keyframes eyeblink { 0%, 90% { opacity: 1; } 91%, 96% { opacity: 0; } 97%, 100% { opacity: 1; } }
  @keyframes shoot    { 0% { transform: translate(0, 0); opacity: 0; }
                        4% { opacity: 0.9; }
                        22% { transform: translate(420px, 140px); opacity: 0; }
                        100% { transform: translate(420px, 140px); opacity: 0; } }
  @media (prefers-reduced-motion: reduce) { * { animation: none !important; } }
"""


class Canvas:
    def __init__(self, w, h, transparent=False):
        self.w, self.h = w, h
        self.transparent = transparent
        self.el = []

    def px(self, x, y, color, w=1, h=1, cls=None, style=None):
        a = f'x="{x * U}" y="{y * U}" width="{w * U}" height="{h * U}" fill="{color}"'
        if cls:
            a += f' class="{cls}"'
        if style:
            a += f' style="{style}"'
        self.el.append(f"<rect {a}/>")

    def open_group(self, cls):
        self.el.append(f'<g class="{cls}">')

    def close_group(self):
        self.el.append("</g>")

    def svg(self):
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w * U}" '
            f'height="{self.h * U}" viewBox="0 0 {self.w * U} {self.h * U}" '
            f'shape-rendering="crispEdges" role="img">',
            f"<style>{STYLE}</style>",
        ]
        parts += self.el
        parts.append("</svg>")
        return "\n".join(parts)

    def save(self, path):
        with open(path, "w") as f:
            f.write(self.svg())
        print(f"wrote {path} ({self.w * U}x{self.h * U})")


def glyph_w(ch):
    return len(GLYPHS[ch][0])


def text_w(s, scale=1):
    return (sum(glyph_w(ch) for ch in s) + (len(s) - 1)) * scale


def draw_text(c, x, y, s, scale=1, colors=None, shadow=None):
    """colors: single color string or list cycled per letter."""
    if isinstance(colors, str):
        colors = [colors]
    passes = ([(shadow, scale)] if shadow else []) + [(None, 0)]
    for shadow_color, off in passes:
        cx = x + (off or 0)
        cy = y + (off or 0)
        ci = 0
        for ch in s:
            g = GLYPHS[ch]
            if shadow_color:
                color = shadow_color
            elif ch in ",.'!-" and len(colors) > 1:
                color = C["lgray"]
            else:
                color = colors[ci % len(colors)]
            for gy, row in enumerate(g):
                for gx, cell in enumerate(row):
                    if cell == "#":
                        c.px(cx + gx * scale, cy + gy * scale, color, scale, scale)
            if ch not in " ,.'!":
                ci += 1
            cx += (glyph_w(ch) + 1) * scale


def draw_sprite(c, x, y, rows, legend, cls=None):
    if cls:
        c.open_group(cls)
    for dy, row in enumerate(rows):
        for dx, cell in enumerate(row):
            if cell in legend:
                c.px(x + dx, y + dy, legend[cell])
    if cls:
        c.close_group()


def dither_row(c, y, top_color, bottom_color, w):
    c.px(0, y, bottom_color, w=w)
    for x in range(0, w, 2):
        c.px(x + (y % 2), y, top_color)


# ---------------------------------------------------------------- header
def make_header(name, subtitle, out):
    W, H = 112, 40
    GROUND = 32
    c = Canvas(W, H)
    rng = random.Random(42)

    # sky bands with dithered seams
    c.px(0, 0, SKY_TOP, w=W, h=12)
    dither_row(c, 12, SKY_TOP, SKY_MID, W)
    c.px(0, 13, SKY_MID, w=W, h=7)
    dither_row(c, 20, SKY_MID, SKY_LOW, W)
    c.px(0, 21, SKY_LOW, w=W, h=6)
    dither_row(c, 27, SKY_LOW, C["plum"], W)
    c.px(0, 28, C["plum"], w=W, h=4)
    # ground
    c.px(0, GROUND, SILHOUETTE, w=W, h=H - GROUND)

    # stars
    star_colors = [C["white"]] * 5 + [C["yellow"], C["blue"], C["peach"]]
    placed = set()
    for _ in range(30):
        x, y = rng.randrange(1, W - 1), rng.randrange(1, 20)
        if (x, y) in placed or (3 <= x <= 12 and 1 <= y <= 9) \
                or (13 <= x <= W - 13 and 8 <= y <= 20):
            continue
        placed.add((x, y))
        cls = "twinkle" if rng.random() < 0.7 else None
        delay = f"animation-delay:-{rng.uniform(0, 2.6):.1f}s" if cls else None
        c.px(x, y, rng.choice(star_colors), cls=cls, style=delay)

    # moon
    moon = [".####.", "######", "######", "######", "######", ".####."]
    draw_sprite(c, 4, 2, moon, {"#": C["white"]})
    for mx, my in [(2, 2), (4, 3), (1, 4), (3, 1)]:
        c.px(4 + mx, 2 + my, C["lgray"])

    # shooting star
    c.open_group("shoot")
    for i, (dx, dy) in enumerate([(0, 0), (1, 0), (2, 1), (3, 1)]):
        c.px(20 + dx, 4 + dy, C["white"] if i > 1 else C["blue"])
    c.close_group()

    # city skyline silhouette with lit windows
    x = 0
    while x < W:
        bw = rng.randrange(5, 10)
        bh = rng.randrange(4, 11)
        top = GROUND - bh
        c.px(x, top, BUILDING, w=min(bw, W - x), h=bh)
        if rng.random() < 0.5:  # antenna
            c.px(x + rng.randrange(1, max(2, bw - 1)), top - 1, BUILDING)
        for wx in range(x + 1, min(x + bw, W) - 1, 2):
            for wy in range(top + 1, GROUND - 1, 2):
                if rng.random() < 0.3:
                    c.px(wx, wy, C["yellow"], cls="win",
                         style=f"animation-delay:-{rng.uniform(0, 4):.1f}s")
        x += bw + rng.randrange(1, 3)

    # title
    title = f"HI, I'M {name}"
    tw = text_w(title, 2)
    tx = (W - tw) // 2
    rainbow = [C["blue"], C["lime"], C["yellow"], C["orange"], C["red"], C["pink"]]
    draw_text(c, tx, 9, title, scale=2, colors=rainbow, shadow=C["black"])

    # subtitle + blinking cursor
    sw = text_w(subtitle)
    sx = (W - sw) // 2
    draw_text(c, sx, 23, subtitle, scale=1, colors=C["lgray"], shadow=C["black"])
    c.px(sx + sw + 2, 23, C["white"], w=2, h=5, cls="blink")

    # cat on the ground, tail flicking between two frames
    cat_x, cat_y = W - 13, GROUND - 1
    cat = [
        "#...#....",
        "#####....",
        "#####....",
        "#####....",
        "########.",
        "########.",
        "########.",
        "########.",
    ]
    draw_sprite(c, cat_x, cat_y, cat, {"#": C["orange"]})
    for sx_, sy_ in [(6, 4), (7, 5), (6, 6)]:  # stripes
        c.px(cat_x + sx_, cat_y + sy_, C["brown"])
    c.px(cat_x + 2, cat_y + 7, SILHOUETTE)  # paw gaps
    c.px(cat_x + 5, cat_y + 7, SILHOUETTE)
    c.px(cat_x + 1, cat_y + 1, C["pink"])  # inner ear
    c.open_group("eyes")
    c.px(cat_x + 1, cat_y + 2, C["yellow"])
    c.px(cat_x + 3, cat_y + 2, C["yellow"])
    c.close_group()
    c.px(cat_x + 2, cat_y + 3, C["pink"])  # nose
    c.open_group("fa")  # tail up
    for tx_, ty_ in [(8, 4), (8, 3), (8, 2), (7, 1)]:
        c.px(cat_x + tx_, cat_y + ty_, C["orange"])
    c.close_group()
    c.open_group("fb")  # tail low
    for tx_, ty_ in [(8, 4), (8, 5), (9, 5), (9, 6)]:
        c.px(cat_x + tx_, cat_y + ty_, C["orange"])
    c.close_group()

    c.save(out)


# ---------------------------------------------------------------- divider
def make_divider(out):
    W, H = 104, 3
    c = Canvas(W, H, transparent=True)
    rng = random.Random(7)
    rainbow = [C["red"], C["orange"], C["yellow"], C["lime"], C["blue"], C["pink"]]
    wave = [1, 0, 0, 1, 2, 2]
    for x in range(W):
        y = wave[x % len(wave)]
        cls = "twinkle" if rng.random() < 0.25 else None
        delay = f"animation-delay:-{rng.uniform(0, 2.6):.1f}s" if cls else None
        c.px(x, y, rainbow[(x // 2) % len(rainbow)], cls=cls, style=delay)
    c.save(out)


# ---------------------------------------------------------------- footer
def make_footer(out):
    W, H = 120, 12
    c = Canvas(W, H, transparent=True)
    inv_a = [
        "..#.....#..",
        "...#...#...",
        "..#######..",
        ".##.###.##.",
        "###########",
        "#.#######.#",
        "#.#.....#.#",
        "...##.##...",
    ]
    inv_b = [
        "..#.....#..",
        "#..#...#..#",
        "#.#######.#",
        "###.###.###",
        ".#########.",
        "..#######..",
        "..#.....#..",
        ".#.......#.",
    ]
    msg = "THANKS FOR STOPPING BY!"
    mw = text_w(msg)
    mx = (W - mw) // 2
    draw_text(c, mx, 3, msg, scale=1, colors=C["pink"], shadow=C["plum"])
    for ix in (2, W - 13):
        draw_sprite(c, ix, 2, inv_a, {"#": C["lime"]}, cls="fa")
        draw_sprite(c, ix, 2, inv_b, {"#": C["lime"]}, cls="fb")
    c.save(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="JIM", help="name shown in the banner (A-Z)")
    ap.add_argument("--subtitle", default="WELCOME TO MY PROFILE")
    ap.add_argument("--outdir", default="assets")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    make_header(args.name.upper(), args.subtitle.upper(),
                os.path.join(args.outdir, "header.svg"))
    make_divider(os.path.join(args.outdir, "divider.svg"))
    make_footer(os.path.join(args.outdir, "footer.svg"))
