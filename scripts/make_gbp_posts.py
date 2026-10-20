"""Tworzy wpisy GBP w gbp-posts/ na podstawie postów z posts/ (status ready/draft).

Usuwa hashtagi i linki z treści (GBP ich nie lubi), przycina do 1500 znaków
na granicy akapitu. Istniejących plików nie nadpisuje.
Użycie: python3 scripts/make_gbp_posts.py [--status ready]"""
import glob
import os
import re
import sys

MAX_LEN = 1500
FRONT = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.S)
want = sys.argv[sys.argv.index("--status") + 1] if "--status" in sys.argv else "ready"

os.makedirs("gbp-posts", exist_ok=True)
made = 0
for path in sorted(glob.glob("posts/*.md")):
    m = FRONT.match(open(path, encoding="utf-8").read())
    if not m:
        continue
    meta = dict(l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)
    meta = {k.strip(): v.strip() for k, v in meta.items()}
    if meta.get("status") != want:
        continue
    out = os.path.join("gbp-posts", os.path.basename(path))
    if os.path.exists(out):
        continue

    lines = [l for l in m.group(2).splitlines() if not re.fullmatch(r"(\s*#\w+)+\s*", l)]
    text = re.sub(r"https?://\S+", "", "\n".join(lines))
    text = re.sub(r"[ \t]+\n", "\n", re.sub(r"\n{3,}", "\n\n", text)).strip()
    while len(text) > MAX_LEN:
        text = text.rsplit("\n\n", 1)[0].strip()

    link = meta.get("link", "https://phinance.pl")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"---\npublish_at: {meta['publish_at']}\nstatus: ready\nlink: {link}\n---\n{text}\n")
    made += 1
print(f"Utworzono {made} wpisów w gbp-posts/")
