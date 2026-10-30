#!/usr/bin/env python3
"""Build the CCICF static site.

Edit the Markdown files in src/content/, then run:
    python3 src/build.py
The HTML pages are written to the repository root (served by GitHub Pages).
Requires: pip install markdown pyyaml beautifulsoup4
"""
import hashlib
import html
import re
from pathlib import Path

import markdown
import yaml
from bs4 import BeautifulSoup

SRC = Path(__file__).resolve().parent
CONTENT = SRC / "content"
OUT = SRC.parent


def asset_version(rel):
    """Short content hash so browsers fetch updated CSS/JS instead of a cached copy."""
    return hashlib.sha1((OUT / rel).read_bytes()).hexdigest()[:8]

YEARS = ["2025", "2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017",
         "2016", "2015", "2014", "2013", "2012", "2011", "2005-2010"]

NAV = [
    ("소개", [("인사말", "greetings"), ("조직", "governance"), ("정관", "bylaws")]),
    ("회원사", "members"),
    ("활동", "activities"),
    ("연락처", "contact"),
]

HERO = "https://static.wixstatic.com/media/dfe178_1431272aa6174bd29eac57c6dd2252ef~mv2.jpg"
DESCRIPTION = ("CCICF 주 프랑스 한불상공회의소는 프랑스에 진출한 한국 기업들을 중심으로 "
               "한 한불 양국의 경제 협력을 위해 노력하고 있습니다.")


SOCIAL = [
    ("LinkedIn", "https://www.linkedin.com/in/ccicf/", "@ccicf"),
    ("Instagram", "https://www.instagram.com/ccicf_official/", "@ccicf_official"),
]


def follow_html(variant=""):
    links = "".join(
        f'<a class="follow-btn" href="{url}" target="_blank" rel="noopener" '
        f'aria-label="CCICF {name} 팔로우 (새 창)"><span class="follow-name">{name}</span>'
        f'<span class="follow-handle">{handle}</span><span class="follow-cta" aria-hidden="true">팔로우 →</span></a>'
        for name, url, handle in SOCIAL)
    return f'<div class="follow {variant}">{links}</div>'


def sized(url, w=1200):
    """Return a resized Wix CDN URL for display; original stays available."""
    m = re.match(r"https://static\.wixstatic\.com/media/([^/]+)$", url)
    if not m:
        return url
    fid = m.group(1)
    return f"https://static.wixstatic.com/media/{fid}/v1/fit/w_{w},h_{w},q_85/{fid}"


def load(slug):
    text = (CONTENT / f"{slug}.md").read_text(encoding="utf-8")
    meta, body = {}, text
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        meta = yaml.safe_load(fm) or {}
    return meta, body


def render_body(body, slug, title=""):
    raw = markdown.markdown(body, extensions=["extra", "sane_lists"])
    soup = BeautifulSoup(raw, "html.parser")

    # Images: lazy-load resized versions, link to the original.
    for img in soup.find_all("img"):
        orig = img["src"]
        img["src"] = sized(orig, 1000)
        img["loading"] = "lazy"
        img["decoding"] = "async"
        if img.parent.name != "a":
            a = soup.new_tag("a", href=orig, target="_blank", rel="noopener")
            a["class"] = "img-link"
            img.wrap(a)

    # Paragraphs made only of images become galleries.
    for p in soup.find_all("p"):
        kids = [c for c in p.children if not (isinstance(c, str) and not c.strip())]
        if kids and all(getattr(k, "name", None) == "a" and k.find("img") for k in kids):
            if len(kids) > 1:
                p.name = "div"
                p["class"] = "gallery"
            else:
                p["class"] = "figure"

    # Group each ### event with its content into a card.
    for h3 in soup.find_all("h3"):
        art = soup.new_tag("article")
        art["class"] = "event"
        h3.insert_before(art)
        node = h3.next_sibling
        nodes = []
        while node is not None and getattr(node, "name", None) not in ("h1", "h2", "h3"):
            nodes.append(node)
            node = node.next_sibling
        media = soup.new_tag("div")
        media["class"] = "event-media"
        text = soup.new_tag("div")
        text["class"] = "event-body"
        for n in nodes:
            n.extract()
            if getattr(n, "get", None) and "figure" in (n.get("class") or []) and not media.contents:
                media.append(n)
            else:
                text.append(n)
        h3.extract()
        text.insert(0, h3)
        # Last italic line = date · place
        ems = [p for p in text.find_all("p") if p.find("em") and p.get_text(strip=True) == p.em.get_text(strip=True)]
        if ems:
            ems[-1]["class"] = "event-meta"
        if media.contents:
            art.append(media)
        else:
            art["class"] = "event no-media"
        art.append(text)

    # Accessible names for photo links: alt text when the source gave none.
    n = 0
    for a in soup.find_all("a", class_="img-link"):
        img = a.find("img")
        if img.get("alt", "").strip():
            continue
        art = a.find_parent("article")
        if art and art.find("h3"):
            img["alt"] = f"{art.find('h3').get_text(strip=True)} 사진"
        else:
            n += 1
            img["alt"] = f"{title} 사진 {n}"
    for a in soup.find_all("a", class_="img-link"):
        a["aria-label"] = f"{a.find('img')['alt']} (원본 크게 보기, 새 창)"

    # Wrap runs of event cards into a grid.
    for art in soup.find_all("article", class_="event"):
        if art.parent.name == "div" and "events" in (art.parent.get("class") or []):
            continue
        grid = soup.new_tag("div")
        grid["class"] = "events"
        art.insert_before(grid)
        node = grid.next_sibling
        while node is not None and (getattr(node, "name", None) == "article" or (isinstance(node, str) and not node.strip())):
            nxt = node.next_sibling
            grid.append(node.extract())
            node = nxt
    out = str(soup)
    out = re.sub(r"(<p>)?\s*<!--FOLLOW-->\s*(</p>)?", follow_html(), out)
    return out


def nav_html(current):
    items = []
    for label, target in NAV:
        if isinstance(target, list):
            active = current in [s for _, s in target]
            sub = "".join(
                f'<li><a href="{s}.html"{" aria-current=page" if s == current else ""}>{html.escape(l)}</a></li>'
                for l, s in target)
            items.append(
                f'<li class="has-sub{" active" if active else ""}"><button type="button" aria-expanded="false">{label}</button>'
                f'<ul class="sub">{sub}</ul></li>')
        else:
            active = current == target or (target == "activities" and current in YEARS)
            items.append(f'<li{" class=active" if active else ""}><a href="{target}.html">{label}</a></li>')
    return "".join(items)


def years_html(current):
    links = []
    for y in YEARS:
        label = "2005–2010" if y == "2005-2010" else y
        cur = ' aria-current="page"' if y == current else ""
        links.append(f'<a href="{y}.html"{cur}>{label}</a>')
    return f'<nav class="years" aria-label="연도별 활동">{"".join(links)}</nav>'


def page(slug, title, body_html, home=False):
    full_title = "주 프랑스 한불상공회의소 | CCICF" if home else f"{title} | CCICF"
    if home:
        main = body_html
    else:
        extra = years_html(slug) if (slug in YEARS or slug == "activities") else ""
        main = (f'<header class="page-head"><div class="wrap"><p class="eyebrow">CCICF</p>'
                f'<h1>{html.escape(title)}</h1></div></header>'
                f'<div class="wrap content">{extra}{body_html}</div>')
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(full_title)}</title>
<meta name="description" content="{html.escape(DESCRIPTION)}">
<meta property="og:title" content="{html.escape(full_title)}">
<meta property="og:description" content="{html.escape(DESCRIPTION)}">
<meta property="og:image" content="{sized(HERO, 1200)}">
<meta property="og:type" content="website">
<link rel="icon" type="image/svg+xml" href="assets/img/favicon.svg">
<link rel="icon" type="image/png" sizes="192x192" href="assets/img/favicon.png">
<link rel="apple-touch-icon" href="assets/img/icon-512.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Noto+Serif+KR:wght@600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css?v={asset_version('assets/style.css')}">
</head>
<body class="{'home' if home else 'inner'} page-{slug}">
<a class="skip" href="#main">본문 바로가기</a>
<header class="site-head">
  <div class="wrap bar">
    <a class="brand" href="index.html"><img src="assets/img/logo.svg" alt="CCICF — Chambre de Commerce &amp; d'Industrie Corée France" width="397" height="144"><span class="name">주 프랑스<br>한불상공회의소</span></a>
    <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="site-nav">메뉴</button>
    <nav id="site-nav" class="site-nav" aria-label="주 메뉴"><ul>{nav_html(slug)}</ul></nav>
  </div>
</header>
<main id="main">
{main}
</main>
<footer class="site-foot">
  <div class="wrap foot-grid">
    <div>
      <p class="foot-logo"><img src="assets/img/logo.svg" alt="CCICF" width="397" height="144" loading="lazy"></p>
      <p>Chambre de Commerce et d'Industrie Corée France<br>주 프랑스 한불상공회의소</p>
    </div>
    <div>
      <h2>Postal address</h2>
      <p>57 Quai de Grenelle<br>75015 Paris, France<br><a href="contact.html">문의는 이메일로</a></p>
    </div>
    <div>
      <h2>Email</h2>
      <p>President : <a href="mailto:direction@ccicf.kr">direction@ccicf.kr</a><br>
      General Secretary : <a href="mailto:sg@ccicf.kr">sg@ccicf.kr</a><br>
      General enquiry : <a href="mailto:contact@ccicf.kr">contact@ccicf.kr</a></p>
    </div>
    <div>
      <h2>Follow us</h2>
      {follow_html("follow-foot")}
    </div>
  </div>
  <div class="wrap copy">Copyright CCICF All rights reserved</div>
</footer>
<script src="assets/site.js?v={asset_version('assets/site.js')}" defer></script>
</body>
</html>
"""


def home_page():
    meta, body = load("index")
    # Drop the "# CCICF" title, the French name lines and the hero image: the hero renders them.
    body = re.sub(r"^# CCICF\s*\n", "", body.strip() + "\n", count=1)
    body = re.sub(r"^Chambre de Commerce & d'Industrie\s*\nCorée France\s*\n", "", body.lstrip(), count=1)
    body = body.lstrip().replace(f"![]({HERO})", "", 1)
    rendered = render_body(body, "index", "CCICF 행사")
    hero = f"""<section class="hero" style="--hero:url('{sized(HERO, 1900)}')">
  <div class="wrap hero-inner">
    <p class="eyebrow">Chambre de Commerce et d'Industrie Corée France</p>
    <h1>주 프랑스<br>한불상공회의소</h1>
    <p class="lead">2005년 창립된 프랑스 정부 승인 공익단체이자 CCI 라벨을 취득한 비영리 경제협회</p>
    <p class="hero-cta"><a class="btn" href="activities.html">활동 보기</a><a class="btn ghost" href="greetings.html">인사말</a></p>
  </div>
</section>"""
    band = (f'<section class="follow-band"><div class="wrap follow-band-inner">'
            f'<div><h2>CCICF 소식 받기</h2><p>행사 일정과 활동 소식을 LinkedIn과 Instagram에서 확인하세요.</p></div>'
            f'{follow_html()}</div></section>')
    return page("index", meta.get("title", ""), hero + band + f'<div class="wrap content home-body">{rendered}</div>', home=True)


def main():
    slugs = [p.stem for p in CONTENT.glob("*.md")]
    for slug in slugs:
        if slug == "index":
            out = home_page()
        else:
            meta, body = load(slug)
            out = page(slug, meta.get("title", slug), render_body(body, slug, meta.get("title", slug)))
        (OUT / f"{slug}.html").write_text(out, encoding="utf-8")
    # Old Wix URLs (without .html) keep working on GitHub Pages via folder index redirects.
    legacy = {"copy-of-2024%EB%85%84-1": "2025", "copy-of-2022%EB%85%84-1": "2024",
              "copy-of-2024%EB%85%84": "2023", "copy-of-2021%EB%85%84": "2022",
              "copy-of-2020%EB%85%84": "2021"}
    from urllib.parse import unquote
    for old, new in legacy.items():
        d = OUT / unquote(old)
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(redirect(f"../{new}.html"), encoding="utf-8")
    for slug in slugs:
        if slug == "index":
            continue
        d = OUT / slug
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(redirect(f"../{slug}.html"), encoding="utf-8")
    print(f"Built {len(slugs)} pages")


def redirect(target):
    return (f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={target}">'
            f'<link rel="canonical" href="{target}"><a href="{target}">{target}</a>')


if __name__ == "__main__":
    main()
