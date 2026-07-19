#!/usr/bin/env python3
"""
Instagram → content/instagram.json (and optionally self-hosted images).

Instagram no longer offers anonymous public-feed access, so pick a source:

A) Behold.so feed (recommended, free tier, ~3 min setup, no code):
   1. behold.so → sign in with the Instagram account (@stormy.fables)
   2. Create a feed → copy its JSON feed URL (https://feeds.behold.so/XXXX)
   3. Run:  python3 fetch_instagram.py --behold https://feeds.behold.so/XXXX --download

B) Instagram Graph API (professional/creator account + Meta app token):
   Run:  python3 fetch_instagram.py --token YOUR_LONG_LIVED_TOKEN --download

--download saves images into assets/ig/ and points the JSON at those copies.
STRONGLY recommended with --token, because Graph API media URLs EXPIRE.
Re-run any time to refresh. The Fiction page reads content/instagram.json.
"""
import json, os, sys, urllib.request, urllib.parse

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def save_image(url, i):
    os.makedirs("assets/ig", exist_ok=True)
    ext = ".jpg"
    path = f"assets/ig/post-{i+1}{ext}"
    open(path, "wb").write(get(url))
    return path

def from_behold(feed_url, download):
    data = json.loads(get(feed_url))
    posts = data.get("posts", data if isinstance(data, list) else [])
    out = []
    for i, p in enumerate(posts[:9]):
        img = p.get("mediaUrl") or p.get("thumbnailUrl") or ""
        if download and img:
            img = save_image(img, i)
        out.append({
            "image": img,
            "caption": (p.get("caption") or "")[:220],
            "permalink": p.get("permalink", "https://instagram.com/stormy.fables"),
            "date": (p.get("timestamp") or "")[:10],
        })
    return out

def from_graph(token, download, limit=9):
    fields = "caption,media_url,thumbnail_url,permalink,timestamp,media_type"
    url = ("https://graph.instagram.com/me/media?fields=" + fields +
           "&limit=" + str(limit) + "&access_token=" + urllib.parse.quote(token))
    data = json.loads(get(url)).get("data", [])
    out = []
    for i, p in enumerate(data[:limit]):
        img = p.get("thumbnail_url") or p.get("media_url") or ""
        if download and img:
            img = save_image(img, i)
        out.append({
            "image": img,
            "caption": (p.get("caption") or "")[:220],
            "permalink": p.get("permalink", ""),
            "date": (p.get("timestamp") or "")[:10],
        })
    return out

if __name__ == "__main__":
    args = sys.argv[1:]
    download = "--download" in args
    posts = None
    if "--behold" in args:
        posts = from_behold(args[args.index("--behold") + 1], download)
    elif "--token" in args:
        posts = from_graph(args[args.index("--token") + 1], download)
    else:
        print(__doc__); sys.exit(1)
    os.makedirs("content", exist_ok=True)
    json.dump(posts, open("content/instagram.json", "w", encoding="utf-8"), indent=2)
    print(f"content/instagram.json written — {len(posts)} posts"
          + (" (images saved to assets/ig/)" if download else ""))
