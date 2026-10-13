"""Publikuje na fanpage posty z katalogu posts/, których status to "ready"
i których publish_at już minęło. Po publikacji ustawia status "published"."""
import datetime as dt
import glob
import os
import re
import sys

import requests

API = "https://graph.facebook.com/v21.0"
PAGE = os.environ["FB_PAGE_ID"]
TOKEN = os.environ["FB_PAGE_TOKEN"]
DRY_RUN = os.environ.get("DRY_RUN") == "1"

FRONT = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.S)


def parse(raw):
    m = FRONT.match(raw)
    if not m:
        return None, None
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2).strip()


def find_image(meta):
    """Jeśli w images/ leży plik o tej samej nazwie co post, użyj go automatycznie."""
    stem = meta.get("_stem")
    for ext in ("jpg", "jpeg", "png"):
        path = f"images/{stem}.{ext}"
        if stem and os.path.exists(path):
            return path
    return None


def publish(meta, text):
    link = meta.get("link")
    image = meta.get("image") or find_image(meta)
    if image:
        caption = f"{text}\n\n{link}" if link else text
        with open(image, "rb") as f:
            return requests.post(
                f"{API}/{PAGE}/photos",
                data={"caption": caption, "access_token": TOKEN},
                files={"source": f},
                timeout=60,
            )
    data = {"message": text, "access_token": TOKEN}
    if link:
        data["link"] = link
    return requests.post(f"{API}/{PAGE}/feed", data=data, timeout=60)


def main():
    now = dt.datetime.now(dt.timezone.utc)
    failed = False
    for path in sorted(glob.glob("posts/*.md")):
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        meta, text = parse(raw)
        if meta is not None:
            meta["_stem"] = os.path.splitext(os.path.basename(path))[0]
        if meta is None:
            print(f"POMINIĘTO (zły format): {path}")
            continue
        if meta.get("status") != "ready":
            continue
        when = dt.datetime.fromisoformat(meta["publish_at"])
        if when.tzinfo is None:
            print(f"POMINIĘTO (brak strefy czasowej w publish_at): {path}")
            continue
        if when > now:
            continue

        if DRY_RUN:
            print(f"[DRY RUN] opublikowałbym: {path}")
            continue

        r = publish(meta, text)
        if r.ok:
            print(f"OK: {path} -> {r.json().get('post_id') or r.json().get('id')}")
            raw = re.sub(r"^status: ready$", "status: published", raw, count=1, flags=re.M)
            with open(path, "w", encoding="utf-8") as f:
                f.write(raw)
        else:
            print(f"BŁĄD: {path}: {r.text}", file=sys.stderr)
            failed = True
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
