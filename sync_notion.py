#!/usr/bin/env python3
"""
Notion -> content/{blog,fiction}/*.md sync for "On the Record".

Reads a Notion database, converts each PUBLISHED page's body into Markdown
matching this site's front-matter format, downloads any images into
assets/uploads/ (Notion's own image URLs expire ~1hr after being fetched),
and writes/updates the corresponding .md file. Safe to re-run any time —
it only creates/updates files, never deletes.

Requires two environment variables (see README for how to obtain them):
  NOTION_TOKEN        - the integration's "Internal Integration Secret"
  NOTION_DATABASE_ID  - the database's 32-character ID (from its URL)

Run locally to test before relying on the GitHub Action:
  NOTION_TOKEN=secret_xxx NOTION_DATABASE_ID=xxxx python3 sync_notion.py

Notion database columns expected (name is flexible for Title; others must
match, case-insensitive):
  Title (the built-in title column, any name)
  Kind         select   Blog | Fiction
  Type         select   Case note | Field note | Commentary | Explainer | Story | Poem
  Date         date
  Minutes      number   (optional — defaults to 5 if blank)
  Tags         multi-select or text
  Excerpt      text
  Status       select   Draft | Published   <- only "Published" rows sync
  Slug         text     (optional — auto-generated from the title if blank)

Supported page-body blocks: paragraph, heading (1-3, rendered as a small
section label), quote (rendered as a pull-quote), bulleted/numbered lists,
image (downloaded + captioned), code, divider. Other block types (tables,
columns, toggles, embeds, callouts, video) are skipped for now — keep post
bodies to the supported types, or ask for the converter to be extended.
"""
import json, os, re, sys, time, urllib.request, urllib.error

TOKEN = os.environ.get("NOTION_TOKEN")
DB_ID = os.environ.get("NOTION_DATABASE_ID")
API = "https://api.notion.com/v1"
VER = "2022-06-28"


def call(path, method="GET", body=None):
    req = urllib.request.Request(
        API + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Notion-Version": VER,
            "Content-Type": "application/json",
        },
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:300]
            if e.code == 429 and attempt < 4:
                time.sleep(int(e.headers.get("Retry-After", "1")) + 1)
                continue
            raise RuntimeError(f"Notion API error {e.code} on {path}: {detail}")
    raise RuntimeError("Notion API: too many retries")


def query_database():
    pages, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        r = call(f"/databases/{DB_ID}/query", "POST", body)
        pages.extend(r["results"])
        if not r.get("has_more"):
            break
        cursor = r["next_cursor"]
    return pages


def get_blocks(block_id):
    blocks, cursor = [], None
    while True:
        path = f"/blocks/{block_id}/children?page_size=100"
        if cursor:
            path += f"&start_cursor={cursor}"
        r = call(path)
        blocks.extend(r["results"])
        if not r.get("has_more"):
            break
        cursor = r["next_cursor"]
    return blocks


def prop_text(prop):
    if not prop:
        return ""
    t = prop.get("type")
    if t == "title":
        return "".join(x["plain_text"] for x in prop["title"])
    if t == "rich_text":
        return "".join(x["plain_text"] for x in prop["rich_text"])
    if t == "select":
        return (prop["select"] or {}).get("name", "")
    if t == "multi_select":
        return ", ".join(x["name"] for x in prop["multi_select"])
    if t == "date":
        return (prop["date"] or {}).get("start", "")
    if t == "number":
        return prop["number"]
    return ""


def get_title(props):
    for v in props.values():
        if v.get("type") == "title":
            return prop_text(v)
    return ""


def find_prop(props, *names):
    low = {k.lower(): v for k, v in props.items()}
    for n in names:
        if n.lower() in low:
            return low[n.lower()]
    return None


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s) or "untitled"


def rich_to_md(rich):
    out = []
    for r in rich:
        t = r["plain_text"]
        if not t:
            continue
        a = r.get("annotations", {})
        link = r.get("href")
        if a.get("code"):
            t = f"`{t}`"
        else:
            if a.get("bold"):
                t = f"**{t}**"
            if a.get("italic"):
                t = f"*{t}*"
        if link:
            t = f"[{t}]({link})"
        out.append(t)
    return "".join(out)


def download_image(url, slug, i, root):
    ext = ".jpg"
    for cand in (".png", ".jpeg", ".jpg", ".webp", ".gif"):
        if cand in url.lower():
            ext = cand
            break
    folder = os.path.join(root, "assets", "uploads")
    os.makedirs(folder, exist_ok=True)
    name = f"{slug}-{i + 1}{ext}"
    path = os.path.join(folder, name)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r, open(path, "wb") as f:
        f.write(r.read())
    return f"assets/uploads/{name}"


def blocks_to_md(blocks, slug, root):
    lines, img_i = [], 0
    for b in blocks:
        t = b["type"]
        d = b.get(t, {})
        if t == "paragraph":
            lines.append(rich_to_md(d.get("rich_text", [])))
        elif t in ("heading_1", "heading_2", "heading_3"):
            lines.append("##### " + rich_to_md(d.get("rich_text", [])))
        elif t == "quote":
            txt = rich_to_md(d.get("rich_text", []))
            lines.append("> " + txt.replace("\n", "\n> "))
        elif t == "bulleted_list_item":
            lines.append("- " + rich_to_md(d.get("rich_text", [])))
        elif t == "numbered_list_item":
            lines.append("1. " + rich_to_md(d.get("rich_text", [])))
        elif t == "divider":
            lines.append("---")
        elif t == "image":
            src = (d.get("file") or {}).get("url") or (d.get("external") or {}).get("url")
            cap = rich_to_md(d.get("caption", []))
            if src:
                try:
                    local = download_image(src, slug, img_i, root)
                    img_i += 1
                    lines.append(f"![{cap or 'image'}]({local})")
                    if cap:
                        lines.append(f"*{cap}*")
                except Exception as e:
                    print(f"  ! image download failed for {slug}: {e}")
        elif t == "code":
            txt = "".join(x["plain_text"] for x in d.get("rich_text", []))
            lang = d.get("language", "")
            lines.append(f"```{lang}\n{txt}\n```")
        # other block types (tables, columns, toggles, embeds…) are skipped
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def main():
    if not TOKEN or not DB_ID:
        sys.exit("Missing NOTION_TOKEN or NOTION_DATABASE_ID environment variables.")
    root = os.getcwd()
    pages = query_database()
    written = 0
    for page in pages:
        props = page["properties"]
        status = prop_text(find_prop(props, "Status"))
        if status.strip().lower() != "published":
            continue
        title = get_title(props)
        if not title:
            continue
        kind = (prop_text(find_prop(props, "Kind")) or "blog").strip().lower()
        ptype = prop_text(find_prop(props, "Type"))
        date = prop_text(find_prop(props, "Date")) or time.strftime("%Y-%m-%d")
        minutes = prop_text(find_prop(props, "Minutes")) or 5
        tags = prop_text(find_prop(props, "Tags"))
        excerpt = prop_text(find_prop(props, "Excerpt"))
        slug = prop_text(find_prop(props, "Slug")) or slugify(title)

        blocks = get_blocks(page["id"])
        body_md = blocks_to_md(blocks, slug, root)

        front_matter = (
            "---\n"
            f"title: {title}\n"
            f"kind: {kind}\n"
            f"type: {ptype}\n"
            f"date: {date}\n"
            f"minutes: {minutes}\n"
            f"tags: {tags}\n"
            f"excerpt: {excerpt}\n"
            "---\n"
        )
        folder = os.path.join(root, "content", kind)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{slug}.md")
        open(path, "w", encoding="utf-8").write(front_matter + body_md)
        written += 1
        print(f"  wrote {path}")

    print(f"Synced {written} published post(s) from Notion.")


if __name__ == "__main__":
    main()
