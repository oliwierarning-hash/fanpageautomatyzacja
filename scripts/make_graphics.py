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


def font(path, size):
    return ImageFont.truetype(path, int(size * S))


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
        f = font(F_SANS, size)
        if d.textlength(tag, font=f) <= 330 * S:
            break
    d.text((665 * S, 96 * S), tag, font=f, fill="white", anchor="mm")

    # tytuł i podtytuł
    fnt, lines, line_h = fit_title(d, title.upper(), 365, 290)
    sub_f = font(F_TITLE, 15)
    sub_lines = wrap(d, sub, sub_f, 365) if sub else []
    block_h = len(lines) * line_h + (22 + len(sub_lines) * 21 if sub_lines else 0)
    y = 255 - block_h / 2
    y = max(y, 40)
    for line in lines:
        d.text((28 * S, y * S), line, font=fnt, fill=INK)
        y += line_h
    y += 22
    for line in sub_lines:
        d.text((28 * S, y * S), line, font=sub_f, fill=INK)
        y += 21

    # wizytówka
    d.text((190 * S, 513 * S), "OLIWIER ARNING", font=font(F_NAME, 31), fill="white", anchor="mm")
    d.text((190 * S, 547 * S), "DORADZTWO FINANSOWE", font=font(F_NAME, 18), fill="white", anchor="mm")
    d.rectangle([42 * S, 577 * S, 355 * S, 580 * S], fill="white")
    sym = font(F_SYM, 27)
    for cy, glyph, text, size in ((628, "☎", PHONE, 26), (682, "✉", EMAIL, 23)):
        d.ellipse([38 * S, (cy - 17) * S, 72 * S, (cy + 17) * S], fill="white")
        d.text((55 * S, cy * S), glyph, font=sym, fill=BLUE, anchor="mm")
        d.text((86 * S, cy * S), text, font=font(F_SANS, size), fill="white", anchor="lm")
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
