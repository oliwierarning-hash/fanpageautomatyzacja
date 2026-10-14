"""Generuje markowe grafiki do postów: images/<nazwa-posta>.jpg.

Dane (tytuł, podtytuł, hashtag, numer zdjęcia) są w assets/grafiki.csv,
wycięte zdjęcia w assets/photos/foto-NN.png. Wymaga biblioteki Pillow.

    python3 scripts/make_graphics.py            # wszystkie posty z CSV
    python3 scripts/make_graphics.py ikze-dla-kogo   # tylko pasujące do fragmentu nazwy
"""
import csv
import glob
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 864, 720          # układ rysowany we współrzędnych oryginalnych grafik
S = 2                    # supersampling
OUT = (1080, 900)
BLUE = (3, 82, 115)
INK = (22, 22, 22)
PHONE = "792 942 509"
EMAIL = "oliwier.arning@phinance.pl"

F_TITLE = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
F_NAME = "/System/Library/Fonts/Supplemental/Baskerville.ttc"
F_SANS = os.path.expanduser("~/Library/Fonts/DMSans_18pt-Bold.ttf")
F_SYM = "/Library/Fonts/Arial Unicode.ttf"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def font(path, size, index=0):
    return ImageFont.truetype(path, int(size * S), index=index)


def poly(points):
    return [(x * S, y * S) for x, y in points]


def wrap(draw, text, fnt, max_w):
    lines, cur = [], ""
    for word in text.split():
        test = f"{cur} {word}".strip()
        if draw.textlength(test, font=fnt) <= max_w * S or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def fit_title(draw, text, max_w, max_h):
    for size in range(44, 17, -1):
        fnt = font(F_TITLE, size)
        lines = wrap(draw, text, fnt, max_w)
        widest = max(draw.textlength(l, font=fnt) for l in lines) / S
        line_h = size * 1.22
        if widest <= max_w and len(lines) * line_h <= max_h:
            return fnt, lines, line_h
    return fnt, lines, line_h


def circle(img, cx, cy, r):
    """Biały okrąg wygładzony przez 4-krotne supersamplowanie."""
    k = 4
    box = int((r + 2) * 2 * S)
    mask = Image.new("L", (box * k, box * k), 0)
    ImageDraw.Draw(mask).ellipse([2 * S * k, 2 * S * k, (box - 2 * S) * k, (box - 2 * S) * k], fill=255)
    mask = mask.resize((box, box), Image.LANCZOS)
    img.paste((255, 255, 255), (int(cx * S - box / 2), int(cy * S - box / 2)), mask)


def draw_icon(kind):
    """Ikona w kolorze niebieskim na przezroczystym tle, przycięta do swojej zawartości."""
    k = 8
    size = int(40 * S) * k
    tile = Image.new("L", (size, size), 0)
    t = ImageDraw.Draw(tile)
    c = size / 2
    if kind == "mail":
        w, h = size * 0.56, size * 0.40
        x0, y0, x1, y1 = c - w / 2, c - h / 2, c + w / 2, c + h / 2
        lw = int(size * 0.045)
        t.rounded_rectangle([x0, y0, x1, y1], radius=size * 0.04, outline=255, width=lw)
        t.line([(x0 + lw / 2, y0 + lw / 2), (c, c + h * 0.08), (x1 - lw / 2, y0 + lw / 2)], fill=255, width=lw, joint="curve")
    else:
        r = size * 0.30
        lw = int(size * 0.13)
        t.arc([c - r, c - r, c + r, c + r], start=20, end=160, fill=255, width=lw)
        import math
        for ang in (20, 160):
            a = math.radians(ang)
            ex, ey = c + (r - lw / 2) * math.cos(a), c + (r - lw / 2) * math.sin(a)
            t.ellipse([ex - lw * 0.78, ey - lw * 0.78, ex + lw * 0.78, ey + lw * 0.78], fill=255)
        tile = tile.rotate(-45, resample=Image.BICUBIC)
    tile = tile.crop(tile.getbbox())
    target = int((21 if kind == "phone" else 24) * S)
    scale = target / max(tile.size)
    tile = tile.resize((max(1, int(tile.width * scale)), max(1, int(tile.height * scale))), Image.LANCZOS)
    out = Image.new("RGBA", tile.size, BLUE + (0,))
    out.putalpha(tile)
    return out


def render(title, sub, tag, photo_no):
    img = Image.new("RGB", (W * S, H * S), "white")
    photo = Image.open(os.path.join(ROOT, "assets/photos", f"foto-{int(photo_no):02d}.png")).convert("RGBA")
    photo = photo.resize((W * S, H * S), Image.LANCZOS)
    img.paste(photo, (0, 0), photo)
    d = ImageDraw.Draw(img)

    # niebieskie bloki
    d.polygon(poly([(0.455 * W, 0), (W, 0), (W, 0.286 * H), (0.575 * W, 0.286 * H)]), fill=BLUE)
    d.polygon(poly([(0, 0.653 * H), (0.419 * W, 0.653 * H), (0.56 * W, H), (0, H)]), fill=BLUE)

    # hashtag
    tag = tag if tag.startswith("#") else "#" + tag
    for size in range(44, 14, -1):
        f = font(F_TITLE, size)
        if d.textlength(tag, font=f) <= 330 * S:
            break
    d.text((665 * S, 100 * S), tag, font=f, fill="white", anchor="mm")

    # tytuł i podtytuł
    fnt, lines, line_h = fit_title(d, title.upper(), 365, 290)
    sub_f = font(F_TITLE, 23)
    sub_lines = wrap(d, sub, sub_f, 365) if sub else []
    block_h = len(lines) * line_h + (24 + len(sub_lines) * 32 if sub_lines else 0)
    y = 255 - block_h / 2
    y = max(y, 40)
    for line in lines:
        d.text((28 * S, y * S), line, font=fnt, fill=INK)
        y += line_h
    y += 24
    for line in sub_lines:
        d.text((28 * S, y * S), line, font=sub_f, fill=INK)
        y += 32

    # wizytówka
    d.text((190 * S, 513 * S), "OLIWIER ARNING", font=font(F_NAME, 31), fill="white", anchor="mm")
    d.text((190 * S, 547 * S), "DORADZTWO FINANSOWE", font=font(F_NAME, 18), fill="white", anchor="mm")
    d.rectangle([42 * S, 577 * S, 355 * S, 580 * S], fill="white")
    for cy, kind, text, size in ((628, "phone", PHONE, 29), (682, "mail", EMAIL, 26)):
        circle(img, 55, cy, 18)
        glyph = draw_icon(kind)
        img.paste(glyph, (int(55 * S - glyph.width / 2), int(cy * S - glyph.height / 2)), glyph)
        d.text((86 * S, cy * S), text, font=font(F_NAME, size, index=4), fill="white", anchor="lm")
    return img.resize(OUT, Image.LANCZOS)


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    rows = list(csv.DictReader(open(os.path.join(ROOT, "assets/grafiki.csv"), encoding="utf-8")))
    os.makedirs(os.path.join(ROOT, "images"), exist_ok=True)
    n = 0
    for r in rows:
        if only and only not in r["slug"]:
            continue
        matches = glob.glob(os.path.join(ROOT, "posts", f"*-{r['slug']}.md"))
        if not matches:
            print("BRAK POSTA:", r["slug"])
            continue
        stem = os.path.splitext(os.path.basename(matches[0]))[0]
        render(r["tytul"], r["podtytul"], r["hashtag"], r["zdjecie"]).save(
            os.path.join(ROOT, "images", stem + ".jpg"), quality=90, optimize=True)
        n += 1
    print(f"Wygenerowano {n} grafik w images/")


if __name__ == "__main__":
    main()
