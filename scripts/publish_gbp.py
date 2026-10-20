"""Publikuje na Profilu Firmy Google (GBP) wpisy z katalogu gbp-posts/, których status to "ready"
i których publish_at już minęło. Po publikacji ustawia status "published".

Format pliku jak w posts/: nagłówek (publish_at, status, opcjonalnie link i cta) + treść."""
import datetime as dt
import glob
import os
import re
import sys

import requests

ACCOUNT = os.environ["GBP_ACCOUNT_ID"]
LOCATION = os.environ["GBP_LOCATION_ID"]
DRY_RUN = os.environ.get("DRY_RUN") == "1"
DEFAULT_LINK = os.environ.get("GBP_DEFAULT_LINK", "https://phinance.pl")
MAX_LEN = 1500

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


def access_token():
    r = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": os.environ["GBP_CLIENT_ID"],
            "client_secret": os.environ["GBP_CLIENT_SECRET"],
            "refresh_token": os.environ["GBP_REFRESH_TOKEN"],
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def publish(token, meta, text):
    body = {
        "languageCode": "pl",
        "topicType": "STANDARD",
        "summary": text[:MAX_LEN],
        "callToAction": {
            "actionType": meta.get("cta", "LEARN_MORE"),
            "url": meta.get("link") or DEFAULT_LINK,
        },
    }
    return requests.post(
        f"https://mybusiness.googleapis.com/v4/accounts/{ACCOUNT}/locations/{LOCATION}/localPosts",
        json=body,
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )


def main():
    now = dt.datetime.now(dt.timezone.utc)
    token = None
    failed = False
    for path in sorted(glob.glob("gbp-posts/*.md")):
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        meta, text = parse(raw)
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
        if len(text) > MAX_LEN:
            print(f"UWAGA: {path} ma {len(text)} znaków, zostanie przycięty do {MAX_LEN}")

        if DRY_RUN:
            print(f"[DRY RUN] opublikowałbym: {path}")
            continue

        token = token or access_token()
        r = publish(token, meta, text)
        if r.ok:
            print(f"OK: {path} -> {r.json().get('name')}")
            raw = re.sub(r"^status: ready$", "status: published", raw, count=1, flags=re.M)
            with open(path, "w", encoding="utf-8") as f:
                f.write(raw)
        else:
            print(f"BŁĄD: {path}: {r.text}", file=sys.stderr)
            failed = True
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
