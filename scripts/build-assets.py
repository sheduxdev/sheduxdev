"""Renders the README header as a self-contained SVG with the name set in Sen.

GitHub shows README images through an <img>, which loads no fonts, so the
text is converted to outlines. Both themes share one geometry and differ only
in fills. Sen[wght] is instanced at one weight and shaped with HarfBuzz so
kerning survives the conversion.

    pip install fonttools brotli uharfbuzz
    python scripts/build-assets.py
"""

import io
import subprocess
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".fontcache" / "sen.ttf"
OUT = ROOT / "assets"
SOURCE = "https://github.com/google/fonts/raw/main/ofl/sen/Sen%5Bwght%5D.ttf"

NAME = "Deniz Usta"
WEIGHT = 700
SIZE = 56
TRACKING = -0.025  # em

# The README column is about 860px on desktop and 330px on a phone, so one
# SVG unit is one CSS px on desktop and 0.38px on a phone. Only the name is
# large enough to survive that; everything smaller lives in the markdown.
W, H = 860, 92
BASELINE = 78
MARK = 10  # accent square, sits above the cap line

THEMES = {
    "dark": {"fg": "#e6edf3", "accent": "#e02424"},
    "light": {"fg": "#1f2328", "accent": "#bb0000"},
}


def load_font() -> TTFont:
    if not CACHE.exists():
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["curl", "-sL", "-o", str(CACHE), SOURCE], check=True)
    return instantiateVariableFont(TTFont(CACHE), {"wght": WEIGHT}, inplace=False)


def text_path(font: TTFont, text: str, x: float, y: float, size: float) -> str:
    """Shapes `text` and returns a single SVG path `d` for the whole run."""
    blob = io.BytesIO()
    font.save(blob)
    hb_font = hb.Font(hb.Face(blob.getvalue()))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hb_font, buf)

    scale = size / font["head"].unitsPerEm
    glyphs = font.getGlyphSet()
    names = font.getGlyphOrder()
    pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        gx, gy = x + pos.x_offset * scale, y - pos.y_offset * scale
        glyphs[names[info.codepoint]].draw(TransformPen(pen, (scale, 0, 0, -scale, gx, gy)))
        x += pos.x_advance * scale + TRACKING * size
    return pen.getCommands()


def header(c: dict, d: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">
<title>{NAME}</title>
<rect x="0" y="12" width="{MARK}" height="{MARK}" fill="{c['accent']}"/>
<path fill="{c['fg']}" d="{d}"/>
</svg>
"""


def main() -> None:
    d = text_path(load_font(), NAME, 0, BASELINE, SIZE)
    OUT.mkdir(exist_ok=True)
    for theme, colours in THEMES.items():
        path = OUT / f"header-{theme}.svg"
        path.write_text(header(colours, d), encoding="utf-8")
        print(f"{path.relative_to(ROOT)}  {path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
