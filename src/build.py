#!/usr/bin/env python3
"""Build the bilingual (Korean / French) CCICF static site.

Edit the Markdown files, then run:
    python3 src/build.py
  src/content/*.md     Korean pages  -> /<slug>.html
  src/content/fr/*.md  French pages  -> /fr/<slug>.html
Requires: pip install markdown pyyaml beautifulsoup4
"""
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import unquote

import markdown
import yaml
from bs4 import BeautifulSoup

SRC = Path(__file__).resolve().parent
OUT = SRC.parent
SITE = "https://www.ccicf.kr"

YEARS = ["2025", "2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017",
         "2016", "2015", "2014", "2013", "2012", "2011", "2005-2010"]
HERO = "https://static.wixstatic.com/media/dfe178_1431272aa6174bd29eac57c6dd2252ef~mv2.jpg"
SOCIAL = [
    ("LinkedIn", "https://www.linkedin.com/in/ccicf/", "@ccicf"),
    ("Instagram", "https://www.instagram.com/ccicf_official/", "@ccicf_official"),
]

LANGS = {
    "ko": {"dir": SRC / "content", "out": OUT, "root": "", "html_lang": "ko", "label": "한국어"},
    "fr": {"dir": SRC / "content" / "fr", "out": OUT / "fr", "root": "../", "html_lang": "fr", "label": "Français"},
}

# Interface text. Page content lives in the Markdown files.
UI = {
    "ko": {
        "nav": [("소개", [("인사말", "greetings"), ("조직", "governance"), ("정관", "bylaws")]),
                ("회원사", "members"), ("활동", "activities"), ("연락처", "contact")],
        "skip": "본문 바로가기", "menu": "메뉴", "main_nav": "주 메뉴", "lang_nav": "언어 선택",
        "site_name": "주 프랑스 한불상공회의소", "name_html": "주 프랑스<br>한불상공회의소",
        "description": "CCICF 주 프랑스 한불상공회의소는 프랑스에 진출한 한국 기업들을 중심으로 한 한불 양국의 경제 협력을 위해 노력하고 있습니다.",
        "hero_h1": "주 프랑스<br>한불상공회의소",
        "hero_lead": "2005년 창립된 프랑스 정부 승인 공익단체이자 CCI 라벨을 취득한 비영리 경제협회",
        "cta_activities": "활동 보기", "cta_greetings": "인사말",
        "band_h": "CCICF 소식 받기", "band_p": "행사 일정과 활동 소식을 LinkedIn과 Instagram에서 확인하세요.",
        "follow": "팔로우", "follow_label": "CCICF {name} 팔로우 (새 창)", "follow_h": "Follow us",
        "photo": "사진", "photo_open": "원본 크게 보기, 새 창",
        "years_label": "연도별 활동", "postal": "우편 주소", "email": "이메일", "email_cta": "문의는 이메일로",
        "president": "회장", "secretary": "사무총장", "general": "일반 문의",
        "legal": "법적 고지", "privacy": "개인정보 처리방침", "rights": "© CCICF. All rights reserved.",
        "filter_label": "행사 유형", "filter_all": "전체", "filter_count": "{n}개 행사",
        "toc": "목차", "search_label": "행사 검색", "search_ph": "행사명, 장소, 연도 검색",
        "archive_h": "전체 행사 찾기", "archive_p": "2005년부터 지금까지의 모든 행사를 유형과 검색어로 찾아보세요.",
        "no_results": "검색 결과가 없습니다.",
        "cats": {"seminar": "세미나·설명회", "culture": "문화 행사", "golf": "골프", "careers": "취업·창업",
                 "networking": "총회·송년회", "external": "대외 행사·시찰"},
    },
    "fr": {
        "nav": [("À propos", [("Mot du président", "greetings"), ("Organisation", "governance"), ("Statuts", "bylaws")]),
                ("Membres", "members"), ("Activités", "activities"), ("Contact", "contact")],
        "skip": "Aller au contenu", "menu": "Menu", "main_nav": "Menu principal", "lang_nav": "Choix de la langue",
        "site_name": "Chambre de Commerce et d'Industrie Corée France",
        "name_html": "Chambre de Commerce<br>et d'Industrie Corée France",
        "description": "La CCICF réunit les entreprises coréennes implantées en France et œuvre pour la coopération économique entre la Corée et la France.",
        "hero_h1": "Chambre de Commerce<br>et d'Industrie<br>Corée France",
        "hero_lead": "Association économique à but non lucratif fondée en 2005, agréée par le gouvernement français et titulaire du label CCI",
        "cta_activities": "Nos activités", "cta_greetings": "Mot du président",
        "band_h": "Suivre la CCICF", "band_p": "Événements et actualités de la Chambre sur LinkedIn et Instagram.",
        "follow": "Suivre", "follow_label": "Suivre la CCICF sur {name} (nouvel onglet)", "follow_h": "Suivez-nous",
        "photo": "photo", "photo_open": "agrandir, nouvel onglet",
        "years_label": "Activités par année", "postal": "Adresse postale", "email": "E-mail", "email_cta": "Nous écrire",
        "president": "Président", "secretary": "Secrétaire générale", "general": "Renseignements",
        "legal": "Mentions légales", "privacy": "Politique de confidentialité", "rights": "© CCICF. Tous droits réservés.",
        "filter_label": "Type d'événement", "filter_all": "Tous", "filter_count": "{n} événement(s)",
        "toc": "Sommaire", "search_label": "Rechercher un événement", "search_ph": "Nom, lieu, année…",
        "archive_h": "Tous les événements", "archive_p": "Retrouvez tous les événements depuis 2005 par type ou par mot-clé.",
        "no_results": "Aucun résultat.",
        "cats": {"seminar": "Séminaires", "culture": "Culture", "golf": "Golf", "careers": "Emploi & création",
                 "networking": "Assemblées & galas", "external": "Forums & visites"},
    },
}

# Event categories: classified once from the Korean title (body text only as a fallback),
# then reused for the French card at the same position, so both languages filter identically.
TITLE_KEYS = {
    "golf": ["골프"],
    "careers": ["취업", "창업", "채용", "job", "청년과 한국 기업"],
    "seminar": ["세미나", "설명회", "강연", "강의", "웨비나"],
    "culture": ["미술관", "전시", "관람", "특별전", "컬렉션", "기획전", "음악회", "콘서트", "와인", "공연",
                "영화", "백주년", "아티스트", "오리엔트", "시대", "시음", "크루즈", "투어", "아트", "미술사"],
    "networking": ["송년", "신년", "총회", "갈라", "리셉션"],
    "external": ["포럼", "시찰", "미팅", "박람회", "페어", "fair"],
}
BODY_KEYS = {"culture": ["미술관", "전시", "작품", "공연", "와인"], "seminar": ["세미나", "강연"]}
CATS_BY_POS = {}   # slug -> categories in source order (filled while building Korean pages)


def classify(title, body):
    t = title.lower()
    cats = [c for c, keys in TITLE_KEYS.items() if any(k in t for k in keys)]
    if not cats:
        b = body.lower()
        cats = [c for c, keys in BODY_KEYS.items() if any(k in b for k in keys)][:1]
    return cats


FR_MONTHS = {m: i + 1 for i, m in enumerate(
    ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"])}


def asset_version(rel):
    """Short content hash so browsers fetch updated CSS/JS instead of a cached copy."""
    return hashlib.sha1((OUT / rel).read_bytes()).hexdigest()[:8]


def sized(url, w=1200):
    """Resized Wix CDN URL for display; self-hosted images are returned unchanged."""
    m = re.match(r"https://static\.wixstatic\.com/media/([^/]+)$", url)
    if not m:
        return url
    fid = m.group(1)
    return f"https://static.wixstatic.com/media/{fid}/v1/fit/w_{w},h_{w},q_85/{fid}"


def parse_date(text, lang):
    """(year, month, day) from an event meta line; missing parts are 0. None if no year."""
    y = re.search(r"(?:19|20)\d\d", text)
    if not y:
        return None
    year, month, day = int(y.group()), 0, 0
    if lang == "ko":
        m = re.search(r"(\d{1,2})\s*(?:-\s*\d{1,2}\s*)?월", text)
        d = re.search(r"월\s*(\d{1,2})", text)
        month = int(m.group(1)) if m else 0
        day = int(d.group(1)) if d else 0
    else:
        low = text.lower()
        for name, num in FR_MONTHS.items():
            pos = low.find(name)
            if pos >= 0:
                month = num
                d = re.search(r"(\d{1,2})(?:er)?\s*(?:[–-]\s*\d{1,2}\s*)?(?:er\s*)?$", low[:pos].strip())
                day = int(d.group(1)) if d else 0
                break
    return (year, month, day)


def follow_html(lang, variant=""):
    t = UI[lang]
    links = "".join(
        f'<a class="follow-btn" href="{url}" target="_blank" rel="noopener" '
        f'aria-label="{html.escape(t["follow_label"].format(name=name))}"><span class="follow-name">{name}</span>'
        f'<span class="follow-handle">{handle}</span><span class="follow-cta" aria-hidden="true">{t["follow"]} →</span></a>'
        for name, url, handle in SOCIAL)
    return f'<div class="follow {variant}">{links}</div>'


def load(lang, slug):
    path = LANGS[lang]["dir"] / f"{slug}.md"
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        meta = yaml.safe_load(fm) or {}
    return meta, body


def slugify(text):
    s = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.UNICODE)
    return re.sub(r"\s+", "-", s.strip())[:60] or "section"


EVENTS = {"ko": [], "fr": []}   # collected for the all-events search on the activities page


def render_body(body, lang, slug, title=""):
    t = UI[lang]
    raw = markdown.markdown(body, extensions=["extra", "sane_lists"])
    soup = BeautifulSoup(raw, "html.parser")

    # One <h1> per page (the page title): drop an in-content h1 that repeats it, demote any other.
    for h1 in soup.find_all("h1"):
        if h1.get_text(strip=True) == title.strip():
            h1.decompose()
        else:
            h1.name = "h2"

    for img in soup.find_all("img"):
        orig = img["src"]
        img["src"] = sized(orig, 1000)
        img["loading"] = "lazy"
        img["decoding"] = "async"
        if img.parent.name != "a":
            a = soup.new_tag("a", href=orig, target="_blank", rel="noopener")
            a["class"] = "img-link"
            img.wrap(a)

    for p in soup.find_all("p"):
        kids = [c for c in p.children if not (isinstance(c, str) and not c.strip())]
        if kids and all(getattr(k, "name", None) == "a" and k.find("img") for k in kids):
            if len(kids) > 1:
                p.name = "div"
                p["class"] = "gallery"
            else:
                p["class"] = "figure"

    # Each ### heading and what follows it becomes an event card.
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
        ems = [p for p in text.find_all("p") if p.find("em") and p.get_text(strip=True) == p.em.get_text(strip=True)]
        meta_line = ""
        if ems:
            ems[-1]["class"] = "event-meta"
            meta_line = ems[-1].get_text(" ", strip=True)
        if media.contents:
            art.append(media)
        else:
            art["class"] = "event no-media"
        art.append(text)
        pos = len(soup.find_all("article", attrs={"data-pos": True}))
        art["data-pos"] = str(pos)
        if lang == "ko":
            cats = classify(h3.get_text(" "), text.get_text(" "))
            CATS_BY_POS.setdefault(slug, []).append(cats)
        else:
            ko = CATS_BY_POS.get(slug, [])
            cats = ko[pos] if pos < len(ko) else []
        art["data-cats"] = " ".join(cats)
        date = parse_date(meta_line, lang)
        art["data-date"] = "%04d-%02d-%02d" % date if date else ""
        ev_id = slugify(h3.get_text())
        art["id"] = ev_id
        if slug in YEARS:
            EVENTS[lang].append({"t": h3.get_text(strip=True), "m": meta_line, "y": slug,
                                 "c": cats, "id": ev_id, "d": art["data-date"]})

    # Accessible names for photo links.
    n = 0
    for a in soup.find_all("a", class_="img-link"):
        img = a.find("img")
        if not img.get("alt", "").strip():
            art = a.find_parent("article")
            if art and art.find("h3"):
                img["alt"] = f"{art.find('h3').get_text(strip=True)} {t['photo']}"
            else:
                n += 1
                img["alt"] = f"{title} {t['photo']} {n}"
        a["aria-label"] = f"{img['alt']} ({t['photo_open']})"

    # Group consecutive cards into a grid, ordered by date (undated cards keep their place at the end).
    for art in soup.find_all("article", class_="event"):
        if art.parent.name == "div" and "events" in (art.parent.get("class") or []):
            continue
        grid = soup.new_tag("div")
        grid["class"] = "events"
        art.insert_before(grid)
        node = grid.next_sibling
        cards = []
        while node is not None and (getattr(node, "name", None) == "article" or (isinstance(node, str) and not node.strip())):
            nxt = node.next_sibling
            if getattr(node, "name", None) == "article":
                cards.append(node.extract())
            else:
                node.extract()
            node = nxt
        cards.sort(key=lambda c: (c["data-date"] == "", c["data-date"]))
        for c in cards:
            grid.append(c)

    # Statutes: anchor every article and add a table of contents.
    if slug == "bylaws":
        heads = soup.find_all("h2")
        for h in heads:
            h["id"] = slugify(h.get_text())
        if heads:
            toc = BeautifulSoup(
                f'<nav class="toc" aria-label="{t["toc"]}"><h2 class="toc-h">{t["toc"]}</h2><ol>'
                + "".join(f'<li><a href="#{h["id"]}">{html.escape(h.get_text(strip=True))}</a></li>' for h in heads)
                + "</ol></nav>", "html.parser")
            heads[0].insert_before(toc)

    out = str(soup)
    out = re.sub(r"(<p>)?\s*<!--FOLLOW-->\s*(</p>)?", follow_html(lang), out)
    return out


def filters_html(lang, body_html):
    """Category filter buttons, only when the page mixes at least two categories."""
    present = set()
    for m in re.finditer(r'data-cats="([^"]*)"', body_html):
        present.update(m.group(1).split())
    order = [c for c in UI[lang]["cats"] if c in present]
    if len(order) < 2:
        return ""
    t = UI[lang]
    btns = [f'<button type="button" class="chip" data-filter="all" aria-pressed="true">{t["filter_all"]}</button>']
    btns += [f'<button type="button" class="chip" data-filter="{c}" aria-pressed="false">{t["cats"][c]}</button>' for c in order]
    return (f'<div class="filters" role="group" aria-label="{t["filter_label"]}">{"".join(btns)}</div>'
            f'<p class="filter-status" aria-live="polite" data-template="{html.escape(t["filter_count"])}"></p>')


def nav_html(lang, current):
    items = []
    for label, target in UI[lang]["nav"]:
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
            cur = " aria-current=page" if current == target else ""
            items.append(f'<li{" class=active" if active else ""}><a href="{target}.html"{cur}>{label}</a></li>')
    return "".join(items)


def years_html(lang, current):
    links = []
    for y in YEARS:
        label = "2005–2010" if y == "2005-2010" else y
        cur = ' aria-current="page"' if y == current else ""
        links.append(f'<a href="{y}.html"{cur}>{label}</a>')
    return f'<nav class="years" aria-label="{UI[lang]["years_label"]}">{"".join(links)}</nav>'


def url_for(lang, slug):
    base = "" if lang == "ko" else "fr/"
    return f"{SITE}/{base}{'' if slug == 'index' else slug + '.html'}"


def lang_switch(lang, slug):
    other = "fr" if lang == "ko" else "ko"
    href = ("fr/" if other == "fr" else "../") + ("index.html" if slug == "index" else f"{slug}.html")
    code = "FR" if other == "fr" else "KO"
    return (f'<a class="lang-switch" href="{href}" hreflang="{other}" lang="{other}" '
            f'aria-label="{LANGS[other]["label"]}">{code}<span class="lang-full"> · {LANGS[other]["label"]}</span></a>')


def page(lang, slug, title, body_html, home=False):
    t = UI[lang]
    root = LANGS[lang]["root"]
    full_title = f"{t['site_name']} | CCICF" if home else f"{title} | CCICF"
    if home:
        main = body_html
    else:
        extra = years_html(lang, slug) if (slug in YEARS or slug == "activities") else ""
        filt = filters_html(lang, body_html) if slug in YEARS else ""
        main = (f'<header class="page-head"><div class="wrap"><p class="eyebrow">CCICF</p>'
                f'<h1>{html.escape(title)}</h1></div></header>'
                f'<div class="wrap content">{extra}{filt}{body_html}</div>')
    alt = "".join(f'<link rel="alternate" hreflang="{l}" href="{url_for(l, slug)}">' for l in LANGS)
    alt += f'<link rel="alternate" hreflang="x-default" href="{url_for("ko", slug)}">'
    return f"""<!doctype html>
<html lang="{LANGS[lang]['html_lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(full_title)}</title>
<meta name="description" content="{html.escape(t['description'])}">
<link rel="canonical" href="{url_for(lang, slug)}">
{alt}
<meta property="og:title" content="{html.escape(full_title)}">
<meta property="og:description" content="{html.escape(t['description'])}">
<meta property="og:image" content="{sized(HERO, 1200)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="{'ko_KR' if lang == 'ko' else 'fr_FR'}">
<link rel="icon" type="image/svg+xml" href="{root}assets/img/favicon.svg">
<link rel="icon" type="image/png" sizes="192x192" href="{root}assets/img/favicon.png">
<link rel="apple-touch-icon" href="{root}assets/img/icon-512.png">
<link rel="stylesheet" href="{root}assets/style.css?v={asset_version('assets/style.css')}">
</head>
<body class="{'home' if home else 'inner'} page-{slug} lang-{lang}">
<a class="skip" href="#main">{t['skip']}</a>
<header class="site-head">
  <div class="wrap bar">
    <a class="brand" href="index.html"><img src="{root}assets/img/logo.svg" alt="CCICF — Chambre de Commerce &amp; d'Industrie Corée France" width="397" height="144"><span class="name">{t['name_html']}</span></a>
    <div class="bar-right">
      <nav class="langs" aria-label="{t['lang_nav']}">{lang_switch(lang, slug)}</nav>
      <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="site-nav">{t['menu']}</button>
      <nav id="site-nav" class="site-nav" aria-label="{t['main_nav']}"><ul>{nav_html(lang, slug)}</ul></nav>
    </div>
  </div>
</header>
<main id="main">
{main}
</main>
<footer class="site-foot">
  <div class="wrap foot-grid">
    <div>
      <p class="foot-logo"><img src="{root}assets/img/logo.svg" alt="CCICF" width="397" height="144" loading="lazy"></p>
      <p>Chambre de Commerce et d'Industrie Corée France<br>주 프랑스 한불상공회의소</p>
    </div>
    <div>
      <h2>{t['postal']}</h2>
      <p>57 Quai de Grenelle<br>75015 Paris, France<br><a href="contact.html">{t['email_cta']}</a></p>
    </div>
    <div>
      <h2>{t['email']}</h2>
      <p>{t['general']} : <a href="mailto:contact@ccicf.kr">contact@ccicf.kr</a><br>
      {t['secretary']} : <a href="mailto:sg@ccicf.kr">sg@ccicf.kr</a><br>
      {t['president']} : <a href="mailto:direction@ccicf.kr">direction@ccicf.kr</a></p>
    </div>
    <div>
      <h2>{t['follow_h']}</h2>
      {follow_html(lang, "follow-foot")}
    </div>
  </div>
  <div class="wrap copy"><span>{t['rights']}</span><span class="legal-links"><a href="legal.html">{t['legal']}</a><a href="privacy.html">{t['privacy']}</a></span></div>
</footer>
<script src="{root}assets/site.js?v={asset_version('assets/site.js')}" defer></script>
</body>
</html>
"""


def home_page(lang):
    t = UI[lang]
    meta, body = load(lang, "index")
    body = re.sub(r"^# CCICF\s*\n", "", body.strip() + "\n", count=1)
    body = re.sub(r"^Chambre de Commerce & d'Industrie\s*\nCorée France\s*\n", "", body.lstrip(), count=1)
    body = body.lstrip().replace(f"![]({HERO})", "", 1)
    rendered = render_body(body, lang, "index", "CCICF")
    hero = f"""<section class="hero" style="--hero:url('{sized(HERO, 1900)}')">
  <div class="wrap hero-inner">
    <p class="eyebrow">{'Chambre de Commerce et d&#39;Industrie Corée France' if lang == 'ko' else '주 프랑스 한불상공회의소'}</p>
    <h1>{t['hero_h1']}</h1>
    <p class="lead">{t['hero_lead']}</p>
    <p class="hero-cta"><a class="btn" href="activities.html">{t['cta_activities']}</a><a class="btn ghost" href="greetings.html">{t['cta_greetings']}</a></p>
  </div>
</section>"""
    band = (f'<section class="follow-band"><div class="wrap follow-band-inner">'
            f'<div><h2>{t["band_h"]}</h2><p>{t["band_p"]}</p></div>{follow_html(lang)}</div></section>')
    return page(lang, "index", meta.get("title", ""), hero + band + f'<div class="wrap content home-body">{rendered}</div>', home=True)


def archive_html(lang):
    """All events across years, searchable and filterable (progressive enhancement: the list works without JS)."""
    t = UI[lang]
    evs = sorted(EVENTS[lang], key=lambda e: e["d"] or "0000", reverse=True)
    cats = [c for c in t["cats"] if any(c in e["c"] for e in evs)]
    btns = [f'<button type="button" class="chip" data-filter="all" aria-pressed="true">{t["filter_all"]}</button>']
    btns += [f'<button type="button" class="chip" data-filter="{c}" aria-pressed="false">{t["cats"][c]}</button>' for c in cats]
    items = "".join(
        f'<li data-cats="{" ".join(e["c"])}" data-text="{html.escape((e["t"] + " " + e["m"] + " " + e["y"]).lower())}">'
        f'<a href="{e["y"]}.html#{e["id"]}">{html.escape(e["t"])}</a>'
        f'<span class="arch-meta">{html.escape(e["m"])}</span></li>'
        for e in evs)
    return f"""<section class="archive" aria-labelledby="archive-h">
<h2 id="archive-h">{t['archive_h']}</h2>
<p>{t['archive_p']}</p>
<label class="search"><span>{t['search_label']}</span><input type="search" placeholder="{t['search_ph']}" autocomplete="off"></label>
<div class="filters" role="group" aria-label="{t['filter_label']}">{"".join(btns)}</div>
<p class="filter-status" aria-live="polite" data-template="{html.escape(t['filter_count'])}" data-empty="{html.escape(t['no_results'])}"></p>
<ol class="arch-list">{items}</ol>
</section>"""


def redirect(target):
    return (f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={target}">'
            f'<link rel="canonical" href="{target}"><a href="{target}">{target}</a>')


def main():
    count = 0
    for lang, cfg in LANGS.items():
        cfg["out"].mkdir(exist_ok=True)
        slugs = sorted(p.stem for p in cfg["dir"].glob("*.md"))
        # Years first so the activities page can list every event.
        slugs.sort(key=lambda s: (s not in YEARS, s))
        rendered = {}
        for slug in slugs:
            if slug == "index":
                continue
            meta, body = load(lang, slug)
            rendered[slug] = (meta.get("title", slug), render_body(body, lang, slug, meta.get("title", slug)))
        for slug, (title, body_html) in rendered.items():
            if slug == "activities":
                body_html += archive_html(lang)
            (cfg["out"] / f"{slug}.html").write_text(page(lang, slug, title, body_html), encoding="utf-8")
        (cfg["out"] / "index.html").write_text(home_page(lang), encoding="utf-8")
        count += len(slugs)

    # Old Wix URLs keep working.
    legacy = {"copy-of-2024%EB%85%84-1": "2025", "copy-of-2022%EB%85%84-1": "2024",
              "copy-of-2024%EB%85%84": "2023", "copy-of-2021%EB%85%84": "2022",
              "copy-of-2020%EB%85%84": "2021"}
    for old, new in legacy.items():
        d = OUT / unquote(old)
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(redirect(f"../{new}.html"), encoding="utf-8")
    for p in LANGS["ko"]["dir"].glob("*.md"):
        if p.stem == "index":
            continue
        d = OUT / p.stem
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(redirect(f"../{p.stem}.html"), encoding="utf-8")

    # Sitemap with language alternates.
    slugs = sorted(p.stem for p in LANGS["ko"]["dir"].glob("*.md"))
    urls = []
    for s in slugs:
        for l in LANGS:
            alts = "".join(f'<xhtml:link rel="alternate" hreflang="{a}" href="{url_for(a, s)}"/>' for a in LANGS)
            urls.append(f"<url><loc>{url_for(l, s)}</loc>{alts}</url>")
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">' + "".join(urls) + "</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")

    for slug, ko in CATS_BY_POS.items():
        fr_n = sum(1 for e in EVENTS["fr"] if e["y"] == slug)
        if slug in YEARS and fr_n != len(ko):
            print(f"WARNING: {slug} has {len(ko)} KO events but {fr_n} FR events")
    missing = set(p.stem for p in LANGS["ko"]["dir"].glob("*.md")) ^ set(p.stem for p in LANGS["fr"]["dir"].glob("*.md"))
    if missing:
        print("WARNING: pages missing in one language:", sorted(missing))
    print(f"Built {count} pages ({', '.join(LANGS)}), {len(EVENTS['ko'])} KO / {len(EVENTS['fr'])} FR events")


if __name__ == "__main__":
    main()
