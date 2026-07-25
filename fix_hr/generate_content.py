#!/usr/bin/env python3
"""
Builds content/posts.json from the markdown files in content/blog and
content/fiction. Run after adding/editing posts:  python3 generate_content.py
Each .md starts with front matter between --- lines:
  title, kind (blog|fiction), type, date (YYYY-MM-DD), minutes, tags, excerpt

The first ![...](...) image found in the post BODY (not the front matter) is
recorded as "image" — the featured-post card on blog.html/fiction.html uses
it automatically. No extra field to fill in; just use an image early in
whichever post is newest and it becomes the featured thumbnail.
"""
import json, os, re

def parse(path):
    raw = open(path, encoding="utf-8").read()
    raw = raw.lstrip("\ufeff").replace("\r\n", "\n")
    m = re.match(r"---\n(.*?)\n---\n", raw, re.S)
    meta = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    body = raw[m.end():] if m else raw
    img = re.search(r"!\[[^\]]*\]\(([^)\s]+)", body)
    if img:
        meta["image"] = img.group(1)
    meta["slug"] = os.path.splitext(os.path.basename(path))[0]
    return meta

posts = []
for kind in ("blog", "fiction"):
    d = os.path.join("content", kind)
    if not os.path.isdir(d): continue
    for f in os.listdir(d):
        if f.endswith(".md"):
            p = parse(os.path.join(d, f))
            p.setdefault("kind", kind)
            posts.append(p)

posts.sort(key=lambda p: p.get("date", ""), reverse=True)
json.dump(posts, open("content/posts.json", "w", encoding="utf-8"), indent=2)
print(f"content/posts.json written — {len(posts)} posts")
