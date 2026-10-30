# CCICF official website

Static rebuild of www.ccicf.kr (주 프랑스 한불상공회의소), hosted on GitHub Pages.

## Editing content
1. Edit the Markdown files in `src/content/` (one file per page; yearly activity pages are `2025.md`, `2024.md`, …).
2. Rebuild: `pip install markdown pyyaml beautifulsoup4` then `python3 src/build.py`.
3. Commit and push. GitHub Pages republishes automatically.

Event format in yearly pages:

    ### Event title
    ![](https://static.wixstatic.com/media/<image-id>)
    Paragraph text…
    *2025년 9월 11일 · 장소*

## Notes
- Images are currently served from the Wix media CDN (static.wixstatic.com). Copy them into `assets/img/` before closing the Wix account.
- The folders such as `bylaws/` and `copy-of-2024년-1/` only redirect old Wix URLs to the new pages.
