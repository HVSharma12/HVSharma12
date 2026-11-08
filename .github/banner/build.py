"""Needs: pip install fonttools uharfbuzz; fonts via NAME_FONT / MONO_FONT env vars.
Build assets/banner-{dark,light}.svg. Text is converted to outlines (Inter Display /
JetBrains Mono) so the banner looks identical on every OS. Run from the repo root."""
import os
import random

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
NAME_FONT = os.environ.get("NAME_FONT", f"{HERE}/InterDisplay-SemiBold.ttf")
MONO_FONT = os.environ.get("MONO_FONT", f"{HERE}/JetBrainsMono-Medium.ttf")

THEMES = {
    "dark":  dict(bg="#0d1117", border="#30363d", text="#e6edf3", muted="#7d8590",
                  accent="#2ed8c0", dot="#3d4d5c", glow=".16"),
    "light": dict(bg="#ffffff", border="#d0d7de", text="#1f2328", muted="#656d76",
                  accent="#0f9e8a", dot="#c5ced8", glow=".10"),
}
W, H = 1200, 240
GREETINGS = ["HELLO, I'M", "NAMASTE, I'M", "HALLO, ICH BIN"]


def outline(font_path, text, size, x, y, tracking=0.0):
    """Shape `text` with HarfBuzz (kerning, ligatures) and return one SVG path d-string."""
    blob = hb.Blob.from_file_path(font_path)
    face = hb.Face(blob)
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True})
    tt = TTFont(font_path)
    gs = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    scale = size / tt["head"].unitsPerEm
    pen = SVGPathPen(gs)
    pen_x = 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        gx = x + (pen_x + pos.x_offset) * scale
        gy = y - pos.y_offset * scale
        gs[order[info.codepoint]].draw(TransformPen(pen, (scale, 0, 0, -scale, gx, gy)))
        pen_x += pos.x_advance + tracking * tt["head"].unitsPerEm
    return pen.getCommands()


def dots(t):
    """Dot field on the right; a few dots lit in the accent colour with a slow pulse."""
    rnd = random.Random(12)  # fixed seed: same picture every build
    out = []
    for gx in range(560, W, 20):
        for gy in range(10, H, 20):
            fade = (gx - 560) / (W - 560)
            if rnd.random() > 0.25 + fade:
                continue
            if rnd.random() < 0.035:
                d = rnd.uniform(0, 6)
                out.append(f'<circle cx="{gx}" cy="{gy}" r="2" fill="{t["accent"]}" opacity="0">'
                           f'<animate attributeName="opacity" values="0;.9;0" dur="6s" begin="{d:.1f}s" '
                           f'repeatCount="indefinite"/></circle>')
            out.append(f'<circle cx="{gx}" cy="{gy}" r="1.5" fill="{t["dot"]}" opacity="{0.25 + 0.75 * fade:.2f}"/>')
    return "\n    ".join(out)


NAME_D = outline(NAME_FONT, "Harshvardhan Sharma", 58, 64, 148, tracking=-0.01)
GREET_D = [outline(MONO_FONT, g, 20, 67, 86, tracking=0.2) for g in GREETINGS]
N = len(GREETINGS)
CYCLE = 4 * N  # seconds: each greeting holds ~4s

TPL = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%">
  <title>Harshvardhan Sharma</title>
  <style>
    .in{{opacity:0;animation:in 1s .1s ease-out forwards}}
    .in2{{opacity:0;animation:in 1s .35s ease-out forwards}}
    @keyframes in{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
    .rule{{transform-box:fill-box;transform:scaleX(0);animation:grow .9s .6s cubic-bezier(.2,.8,.2,1) forwards}}
    @keyframes grow{{to{{transform:scaleX(1)}}}}
    .g{{opacity:0;animation:cyc {CYCLE}s linear infinite}}
    @keyframes cyc{{0%{{opacity:0}}{a}%,{b}%{{opacity:1}}{c}%,100%{{opacity:0}}}}
  </style>
  <defs>
    <radialGradient id="glow" cx="88%" cy="50%" r="45%">
      <stop offset="0" stop-color="{accent}" stop-opacity="{glow}"/>
      <stop offset="1" stop-color="{accent}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="edge" x1="0" x2="1">
      <stop offset="0" stop-color="{accent}" stop-opacity="0"/>
      <stop offset=".5" stop-color="{accent}" stop-opacity=".9"/>
      <stop offset="1" stop-color="{accent}" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="card"><rect x=".5" y=".5" width="{W1}" height="{H1}" rx="12"/></clipPath>
  </defs>
  <g clip-path="url(#card)">
    <rect width="{W}" height="{H}" fill="{bg}"/>
    <rect width="{W}" height="{H}" fill="url(#glow)"/>
    {dots}
    <rect x="0" y="0" width="{W}" height="1.5" fill="url(#edge)"/>
  </g>
  <rect x=".5" y=".5" width="{W1}" height="{H1}" rx="12" fill="none" stroke="{border}"/>
  <g class="in" fill="{muted}">
    {greetings}
  </g>
  <path class="in2" fill="{text}" d="{name}"/>
  <rect class="rule" x="68" y="174" width="64" height="3" rx="1.5" fill="{accent}"/>
</svg>
"""

# keyframe percentages: fade in over 0.6s, hold, fade out over 0.6s, within each 1/N slot
slot = 100 / N
fade = 0.6 / CYCLE * 100
a, b, c = fade, slot - fade, slot

for name, t in THEMES.items():
    greetings = "\n    ".join(
        f'<path class="g" style="animation-delay:{i * CYCLE / N - 0:.1f}s" d="{d}"/>' for i, d in enumerate(GREET_D)
    )
    svg = TPL.format(W=W, H=H, W1=W - 1, H1=H - 1, dots=dots(t), greetings=greetings, name=NAME_D,
                     CYCLE=CYCLE, a=f"{a:.1f}", b=f"{b:.1f}", c=f"{c:.1f}", **t)
    open(f"assets/banner-{name}.svg", "w").write(svg)
    print(f"assets/banner-{name}.svg {len(svg)//1024} KB")
