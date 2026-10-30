#!/usr/bin/env python3
"""Download every Wix-hosted image referenced in src/content into assets/media/.

Run by .github/workflows/fetch-images.yml (GitHub's runners can reach Wix).
Images are saved at most 1600px on the long side, which is plenty for the site
and keeps the repository small. Already-downloaded files are skipped.
"""
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / "assets" / "media"
PATTERN = re.compile(r"https://static\.wixstatic\.com/media/([A-Za-z0-9_~.%-]+\.(?:jpe?g|png|webp|gif))", re.I)


def main():
    MEDIA.mkdir(parents=True, exist_ok=True)
    ids = set()
    for md in (ROOT / "src").rglob("*.md"):
        ids.update(PATTERN.findall(md.read_text(encoding="utf-8")))
    ids.update(PATTERN.findall((ROOT / "src" / "build.py").read_text(encoding="utf-8")))
    failed = []
    for fid in sorted(ids):
        dest = MEDIA / fid
        if dest.exists() and dest.stat().st_size > 0:
            continue
        url = f"https://static.wixstatic.com/media/{fid}/v1/fit/w_1600,h_1600,q_85/{fid}"
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "ccicf-site-migration"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    dest.write_bytes(r.read())
                break
            except Exception as e:  # noqa: BLE001 - report and retry
                if attempt == 2:
                    failed.append((fid, str(e)))
                time.sleep(2)
    print(f"{len(ids)} images referenced, {len(failed)} failed")
    for fid, err in failed:
        print("FAILED", fid, err)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
