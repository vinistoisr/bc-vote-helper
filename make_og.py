"""Draw the 1200x630 link-preview image (assets/og.png) with Pillow.

Usage: python -I make_og.py <Archivo.ttf> <AtkinsonHyperlegibleNext.ttf>
Fonts: Google Fonts (SIL Open Font License), the same faces the site uses.
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
S = 2  # draw at 2x, then downscale
W, H = 1200 * S, 630 * S
INK, BG, MUTED, LINE = "#121A1F", "#ECEFEE", "#A3AFB6", "#2C373E"
PARTY = ["#EC5C34", "#2C4494", "#12B259", "#EE2D30", "#D2A65C"]  # NDP, Con, Green, CentreBC, OneBC


def font(path, size, wght, wdth=None):
    f = ImageFont.truetype(path, size * S)
    axes = []
    for a in f.get_variation_axes():
        name = a.get("name", b"")
        name = name.decode() if isinstance(name, bytes) else str(name)
        axes.append(wdth if name.lower().startswith("width") and wdth else wght if name.lower().startswith("weight") else a["default"])
    f.set_variation_by_axes(axes)
    return f


def main(archivo, atkinson):
    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)
    x0 = 72 * S
    eyebrow = font(atkinson, 24, 700)
    d.text((x0, 64 * S), "BC ELECTION  |  OCTOBER 24, 2026", font=eyebrow, fill=MUTED)
    head = font(archivo, 74, 850, 88)
    y = 112 * S
    for line in ["Which party and", "candidate match", "your views?"]:
        d.text((x0, y), line, font=head, fill="#FFFFFF")
        y += 82 * S
    body = font(atkinson, 28, 500)
    d.text((x0, y + 22 * S), "16 short questions. All 93 ridings.", font=body, fill="#E8EDEF")
    d.text((x0, y + 62 * S), "Plain words or every detail, your pick.", font=body, fill="#E8EDEF")

    # Right: postal code card
    cx, cy, cw, ch = 752 * S, 136 * S, 376 * S, 272 * S
    d.rounded_rectangle((cx, cy, cx + cw, cy + ch), radius=22 * S, fill="#FFFFFF")
    lab = font(atkinson, 21, 700)
    d.text((cx + 30 * S, cy + 28 * S), "Your postal code", font=lab, fill="#4A5661")
    d.rounded_rectangle((cx + 30 * S, cy + 62 * S, cx + cw - 30 * S, cy + 130 * S), radius=12 * S, outline=INK, width=3 * S)
    pc = font(archivo, 38, 800, 100)
    d.text((cx + 50 * S, cy + 74 * S), "V3S 1A1", font=pc, fill=INK)
    d.text((cx + 30 * S, cy + 154 * S), "Your riding", font=lab, fill="#4A5661")
    rid = font(archivo, 34, 800, 92)
    d.text((cx + 30 * S, cy + 184 * S), "Surrey-Panorama", font=rid, fill=INK)
    sm = font(atkinson, 21, 500)
    d.text((cx + 30 * S, cy + 232 * S), "Compare your candidates", font=sm, fill="#4A5661")

    # Bottom: equal party colour strip and footer
    seg = W / 5
    for i, c in enumerate(PARTY):
        d.rectangle((int(i * seg), H - 14 * S, int((i + 1) * seg), H), fill=c)
    foot = font(atkinson, 26, 700)
    d.text((x0, H - 74 * S), "votebc.vinceroyer.ca", font=foot, fill="#FFFFFF")
    note = font(atkinson, 24, 500)
    t = "Free. Anonymous. Open source."
    tw = d.textlength(t, font=note)
    d.text((W - x0 - tw, H - 72 * S), t, font=note, fill=MUTED)

    out = img.resize((1200, 630), Image.LANCZOS)
    os.makedirs(os.path.join(HERE, "assets"), exist_ok=True)
    out.save(os.path.join(HERE, "assets", "og.png"), optimize=True)
    print("wrote assets/og.png", os.path.getsize(os.path.join(HERE, "assets", "og.png")), "bytes")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
