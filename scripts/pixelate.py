#!/usr/bin/env python3
"""Turn a photo into pixel art or ASCII art.

Pixel mode downsamples the image to a coarse pixel grid, snaps colors to a
retro palette (or an adaptive one), and writes crisp SVG or PNG pixel art.
ASCII mode maps brightness to text characters, ready to paste into a
<pre> or code block.

Examples:
    python3 scripts/pixelate.py photo.jpg -o assets/avatar.svg
    python3 scripts/pixelate.py photo.jpg -o avatar.png --width 64 --palette gameboy
    python3 scripts/pixelate.py photo.jpg --ascii --width 80
    python3 scripts/pixelate.py photo.jpg --ascii --invert -o art.txt

Requires Pillow:  pip install Pillow
"""
import argparse
import sys

try:
    from PIL import Image, ImageFilter, ImageOps
except ImportError:
    sys.exit("Pillow is required: pip install Pillow")

# dark -> light; reversed by --invert for light-on-dark displays
ASCII_RAMP = ("$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft"
              "/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. ")

PALETTES = {
    # PICO-8 — matches the palette used by generate_pixel_art.py
    "pico8": [
        "#000000", "#1d2b53", "#7e2553", "#008751",
        "#ab5236", "#5f574f", "#c2c3c7", "#fff1e8",
        "#ff004d", "#ffa300", "#ffec27", "#00e436",
        "#29adff", "#83769c", "#ff77a8", "#ffccaa",
    ],
    # classic DMG Game Boy greens
    "gameboy": ["#0f380f", "#306230", "#8bac0f", "#9bbc0f"],
    # moody 8-color night palette, good for dark GitHub themes
    "night": [
        "#0e0e22", "#1d2b53", "#2a2350", "#7e2553",
        "#83769c", "#c2c3c7", "#ff77a8", "#fff1e8",
    ],
}


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb[:3])


def quantize(img, palette_name, colors, dither):
    dither_mode = Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE
    if palette_name == "adaptive":
        return img.quantize(colors=colors, method=Image.Quantize.MEDIANCUT,
                            dither=dither_mode).convert("RGB")
    rgb = [c for h in PALETTES[palette_name] for c in hex_to_rgb(h)]
    pal_img = Image.new("P", (1, 1))
    pal_img.putpalette(rgb + rgb[:3] * (256 - len(rgb) // 3))
    return img.convert("RGB").quantize(palette=pal_img,
                                       dither=dither_mode).convert("RGB")


def to_svg(img, unit):
    """Emit one rect per horizontal run of same-colored pixels."""
    w, h = img.size
    px = img.load()
    rows = []
    for y in range(h):
        x = 0
        while x < w:
            color = px[x, y]
            run = 1
            while x + run < w and px[x + run, y] == color:
                run += 1
            rows.append(f'<rect x="{x * unit}" y="{y * unit}" '
                        f'width="{run * unit}" height="{unit}" '
                        f'fill="{rgb_to_hex(color)}"/>')
            x += run
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w * unit}" '
        f'height="{h * unit}" viewBox="0 0 {w * unit} {h * unit}" '
        f'shape-rendering="crispEdges" role="img">',
        *rows,
        "</svg>",
    ])


def prep_gray(img):
    """Grayscale with stretched contrast and a sharpening pass so edges
    survive the heavy downsample."""
    gray = ImageOps.autocontrast(img.convert("L"), cutoff=1)
    return gray.filter(ImageFilter.UnsharpMask(radius=3, percent=120))


def to_ascii(img, width, invert):
    """Map brightness to characters. Rows are sampled at half resolution
    because terminal characters are roughly twice as tall as they are wide."""
    ramp = ASCII_RAMP[::-1] if invert else ASCII_RAMP
    gray = prep_gray(img)
    h = max(1, round(gray.height * width / gray.width / 2))
    gray = gray.resize((width, h), Image.Resampling.LANCZOS)
    px = gray.load()
    lines = []
    for y in range(h):
        line = "".join(ramp[px[x, y] * (len(ramp) - 1) // 255]
                       for x in range(width))
        lines.append(line.rstrip())
    return "\n".join(lines) + "\n"


def to_braille(img, width, invert, edges=False, edge_threshold=48):
    """Braille characters give a 2x4 dot grid per character cell — much
    finer detail than one-char-per-pixel ASCII. Dots are set for dark
    pixels by default; --invert sets them for bright pixels instead
    (use it when the text is displayed light-on-dark).

    edges=True dots the luminance edges instead of the shading, producing
    an outline sketch that reads correctly on BOTH light and dark
    backgrounds (dark pen strokes vs. glowing neon strokes)."""
    rows = max(1, round(img.height * width / img.width / 2))
    gray = prep_gray(img).resize((width * 2, rows * 4), Image.Resampling.LANCZOS)
    if edges:
        outline = ImageOps.autocontrast(gray.filter(ImageFilter.FIND_EDGES))
        # hard threshold: dot wherever there is an edge, no dithering
        gray = outline.point(lambda p: 0 if p > edge_threshold else 255)
    elif invert:
        gray = ImageOps.invert(gray)
    bitmap = gray.convert("1").load()  # Floyd-Steinberg dithered 1-bit
    # braille dot bit values by (dx, dy) within the 2x4 cell
    bits = {(0, 0): 1, (0, 1): 2, (0, 2): 4, (1, 0): 8,
            (1, 1): 16, (1, 2): 32, (0, 3): 64, (1, 3): 128}
    lines = []
    for cy in range(rows):
        line = []
        for cx in range(width):
            code = 0
            for (dx, dy), bit in bits.items():
                if bitmap[cx * 2 + dx, cy * 4 + dy] == 0:  # dark pixel -> dot
                    code |= bit
            line.append(chr(0x2800 + code))
        lines.append("".join(line).rstrip("⠀"))
    return "\n".join(lines) + "\n"


BLANKS = " ⠀"  # space and empty braille cell
LINK_SPAN = 20      # characters of art each link occupies


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def weave_links(art, links):
    """Wrap runs of dots in <a> tags so the art contains clickable doors.

    Links are spread vertically across the piece; each one grabs the middle
    of the densest run of non-blank characters on its row. Returns an HTML
    <pre> block (GitHub READMEs render raw <pre>/<a> HTML, where markdown
    code blocks cannot contain links)."""
    lines = art.rstrip("\n").split("\n")
    out = {}
    for i, spec in enumerate(links):
        url, _, tip = spec.partition("|")
        url, tip = url.strip(), tip.strip() or url.strip()
        # spread target rows evenly, skipping the very top and bottom
        row = round((i + 1) * len(lines) / (len(links) + 1)) - 1
        # find a row nearby whose longest dot-run fits a link
        for r in sorted(range(len(lines)), key=lambda r: abs(r - row)):
            if r in out:
                continue
            runs = [(len(m), m_start) for m, m_start in _runs(lines[r])]
            if not runs:
                continue
            length, start = max(runs)
            if length >= LINK_SPAN:
                mid = start + (length - LINK_SPAN) // 2
                out[r] = (mid, mid + LINK_SPAN, url, tip)
                break
        else:
            print(f"warning: no room left for link {url}", file=sys.stderr)
    html = []
    for r, line in enumerate(lines):
        if r in out:
            a, b, url, tip = out[r]
            line = (esc(line[:a])
                    + f'<a href="{esc(url)}" title="{esc(tip)}"><ins>'
                    + esc(line[a:b]) + "</ins></a>" + esc(line[b:]))
        else:
            line = esc(line)
        html.append(line)
    return "<pre>\n" + "\n".join(html) + "\n</pre>\n"


def _runs(line):
    """Yield (run, start_index) for maximal runs of non-blank characters."""
    run, start = "", None
    for i, ch in enumerate(line):
        if ch not in BLANKS:
            if start is None:
                start = i
            run += ch
        elif start is not None:
            yield run, start
            run, start = "", None
    if start is not None:
        yield run, start


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n".join(__doc__.splitlines()[1:]))
    ap.add_argument("input", help="input photo (anything Pillow can read)")
    ap.add_argument("-o", "--output",
                    help="output file, .svg or .png (default: <input>.pixel.svg)")
    ap.add_argument("--width", type=int, default=64,
                    help="width of the pixel grid in pixels (default: 64)")
    ap.add_argument("--palette", default="pico8",
                    choices=[*PALETTES, "adaptive"],
                    help="color palette (default: pico8)")
    ap.add_argument("--colors", type=int, default=16,
                    help="number of colors when --palette adaptive (default: 16)")
    ap.add_argument("--dither", action="store_true",
                    help="Floyd-Steinberg dithering (adds retro texture)")
    ap.add_argument("--unit", type=int, default=8,
                    help="output size of one art pixel in px (default: 8)")
    ap.add_argument("--ascii", action="store_true",
                    help="output ASCII art text instead of pixel art")
    ap.add_argument("--braille", action="store_true",
                    help="output braille-dot text art (8x the detail of --ascii)")
    ap.add_argument("--invert", action="store_true",
                    help="text modes: for light text on a dark background")
    ap.add_argument("--edges", action="store_true",
                    help="braille mode: dot the outlines instead of the "
                         "shading — theme-neutral output that reads correctly "
                         "on both light and dark backgrounds")
    ap.add_argument("--edge-threshold", type=int, default=48, metavar="N",
                    help="edge sensitivity for --edges, 0-255; lower = more "
                         "detail (default: 48)")
    ap.add_argument("--link", action="append", default=[], metavar="URL",
                    help="text modes: embed a clickable link inside the art "
                         "(repeatable; output becomes an HTML <pre> block that "
                         "GitHub READMEs render). Use 'URL|tooltip text' to "
                         "set the hover tooltip.")
    args = ap.parse_args()

    img = Image.open(args.input)
    img = img.convert("RGB")

    if args.ascii or args.braille:
        if args.braille:
            art = to_braille(img, args.width, args.invert, edges=args.edges,
                             edge_threshold=args.edge_threshold)
        else:
            art = to_ascii(img, args.width, args.invert)
        if args.link:
            art = weave_links(art, args.link)
        if args.output:
            with open(args.output, "w") as f:
                f.write(art)
            print(f"wrote {args.output} ({args.width} columns)")
        else:
            sys.stdout.write(art)
        return

    out = args.output or f"{args.input.rsplit('.', 1)[0]}.pixel.svg"
    grid_h = max(1, round(img.height * args.width / img.width))
    small = img.resize((args.width, grid_h), Image.Resampling.BOX)
    small = quantize(small, args.palette, args.colors, args.dither)

    if out.lower().endswith(".png"):
        big = small.resize((small.width * args.unit, small.height * args.unit),
                           Image.Resampling.NEAREST)
        big.save(out)
    elif out.lower().endswith(".svg"):
        with open(out, "w") as f:
            f.write(to_svg(small, args.unit))
    else:
        sys.exit("output must end in .svg or .png")

    print(f"wrote {out} ({small.width}x{small.height} art pixels, "
          f"palette: {args.palette})")


if __name__ == "__main__":
    main()
