# CCICF official website

Static site for www.ccicf.kr (주 프랑스 한불상공회의소 / Chambre de Commerce et d'Industrie Corée France), in Korean and French, hosted on GitHub Pages.

## Editing content
- Korean pages: `src/content/<page>.md` → `/<page>.html`
- French pages: `src/content/fr/<page>.md` → `/fr/<page>.html`
- Keep both languages in step: every page exists in both folders, and yearly pages list events in the same order (the French page reuses the Korean event categories by position).

Rebuild after editing: `pip install markdown pyyaml beautifulsoup4`, then `python3 src/build.py`. Commit and push; GitHub Pages republishes automatically.

Event format in yearly pages:

    ### Event title
    ![Short description of the photo](assets/media/… or Wix URL)
    Paragraph text…
    *2025년 9월 11일 · 장소*        (French: *11 septembre 2025 · Lieu*)

Events are sorted by the date in the last italic line. Categories (seminars, culture, golf…) are inferred from the Korean title; see `TITLE_KEYS` in `src/build.py`.

## Images and fonts
- Photos live in `assets/media/`. To add new Wix images, reference the Wix URL and run the "Fetch images from Wix" workflow (Actions tab), which downloads them and rebuilds.
- Fonts are self-hosted in `assets/fonts/` (Noto Sans KR, SIL Open Font License); no request goes to Google.

## Still to complete before going live on ccicf.kr
- `legal.md` / `privacy.md` (both languages): registered office, RNA number, director of publication, email retention period (highlighted on the pages).
