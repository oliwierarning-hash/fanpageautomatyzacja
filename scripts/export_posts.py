"""Eksportuje opublikowane posty strony Facebook do archive/ (markdown + index.csv).

Użycie:
    FB_PAGE_TOKEN=... python3 scripts/export_posts.py [--limit 200] [--insights]

Zmienne środowiskowe:
    FB_PAGE_TOKEN  token strony (wymagany)
    FB_PAGE_ID     ID strony (domyślnie 100736349151366)
"""
import argparse
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://graph.facebook.com/v21.0"
PAGE = os.environ.get("FB_PAGE_ID", "100736349151366")
TOKEN = os.environ.get("FB_PAGE_TOKEN")

FIELDS = (
    "id,message,created_time,permalink_url,full_picture,status_type,"
    "reactions.summary(true).limit(0),comments.summary(true).limit(0),shares"
)


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        sys.exit(f"Błąd API ({e.code}): {re.sub(r'access_token=[^&\"]+', 'access_token=***', body)}")


def fetch_posts(limit):
    params = urllib.parse.urlencode({"fields": FIELDS, "limit": 50, "access_token": TOKEN})
    url = f"{API}/{PAGE}/published_posts?{params}"
    posts = []
    while url and len(posts) < limit:
        data = get(url)
        posts.extend(data.get("data", []))
        url = data.get("paging", {}).get("next")
    return posts[:limit]


def fetch_insights(post_id):
    """Zasięg posta. Metryki Mety się zmieniają, więc błąd nie przerywa eksportu."""
    for metric in ("post_media_view", "post_impressions_unique", "post_impressions"):
        params = urllib.parse.urlencode({"metric": metric, "access_token": TOKEN})
        try:
            with urllib.request.urlopen(f"{API}/{post_id}/insights?{params}", timeout=60) as r:
                values = json.load(r).get("data", [])
            if values and values[0].get("values"):
                return metric, values[0]["values"][0]["value"]
        except urllib.error.HTTPError:
            continue
    return "", ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--insights", action="store_true", help="pobierz też zasięg (wolniejsze)")
    args = ap.parse_args()
    if not TOKEN:
        sys.exit("Ustaw FB_PAGE_TOKEN w środowisku.")

    os.makedirs("archive", exist_ok=True)
    posts = fetch_posts(args.limit)
    rows = []
    for p in posts:
        text = (p.get("message") or "").strip()
        reactions = p.get("reactions", {}).get("summary", {}).get("total_count", 0)
        comments = p.get("comments", {}).get("summary", {}).get("total_count", 0)
        shares = p.get("shares", {}).get("count", 0)
        metric, reach = fetch_insights(p["id"]) if args.insights else ("", "")
        date = p["created_time"][:10]
        short_id = p["id"].split("_")[-1]
        rows.append({
            "date": date, "id": p["id"], "type": p.get("status_type", ""),
            "reactions": reactions, "comments": comments, "shares": shares,
            "reach_metric": metric, "reach": reach,
            "chars": len(text), "url": p.get("permalink_url", ""),
        })
        meta = [
            "---",
            f"date: {p['created_time']}",
            f"url: {p.get('permalink_url', '')}",
            f"type: {p.get('status_type', '')}",
            f"reactions: {reactions}",
            f"comments: {comments}",
            f"shares: {shares}",
        ]
        if reach != "":
            meta.append(f"reach: {reach}")
        if p.get("full_picture"):
            meta.append(f"image_url: {p['full_picture']}")
        meta += ["---", "", text, ""]
        with open(f"archive/{date}-{short_id}.md", "w", encoding="utf-8") as f:
            f.write("\n".join(meta))

    with open("archive/index.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["date"])
        w.writeheader()
        w.writerows(rows)
    print(f"Zapisano {len(rows)} postów do archive/ (index.csv + pliki .md)")


if __name__ == "__main__":
    main()
