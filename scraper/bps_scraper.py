import argparse
import json
import re
import time
import urllib.parse as urlparse
from collections import deque
from pathlib import Path
from typing import List, Dict, Set, Tuple
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib import robotparser

HEADERS = {
    "User-Agent": "BPS-Medan-Chatbot/1.0 (+https://medankota.bps.go.id)"
}

def read_robots(domain: str) -> Tuple[robotparser.RobotFileParser, List[str]]:
    robots_url = urlparse.urljoin(domain, "/robots.txt")
    rp = robotparser.RobotFileParser()
    try:
        r = requests.get(robots_url, headers=HEADERS, timeout=10)
        rp.parse(r.text.splitlines())
        sitemaps = []
        for line in r.text.splitlines():
            if line.lower().startswith("sitemap:"):
                sitemaps.append(line.split(":", 1)[1].strip())
        return rp, sitemaps
    except Exception:
        rp.set_url(robots_url)
        return rp, []

def get_xml_links(xml_url: str) -> List[str]:
    try:
        resp = requests.get(xml_url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "xml")
        locs = [loc.text.strip() for loc in soup.find_all("loc")]
        return locs
    except Exception:
        return []

def normalize_url(base_domain: str, href: str) -> str:
    if not href:
        return ""
    u = urlparse.urljoin(base_domain, href)
    parsed = urlparse.urlparse(u)
    # only keep same host, strip fragments
    base_host = urlparse.urlparse(base_domain).netloc
    if parsed.netloc != base_host:
        return ""
    cleaned = parsed._replace(fragment="").geturl()
    return cleaned

def is_html(resp: requests.Response) -> bool:
    ctype = resp.headers.get("Content-Type", "")
    return "text/html" in ctype

def extract_text(html: str) -> Tuple[str, str, str]:
    soup = BeautifulSoup(html, "lxml")
    title = (soup.title.string.strip() if soup.title and soup.title.string else "")[:200]

    # meta description
    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = desc_tag.get("content", "").strip() if desc_tag else ""

    # heuristic: prefer <article>, then main/content areas
    candidates = []
    for sel in ["article", "main", "[role=main]", ".content", ".entry-content", "#content"]:
        nums = soup.select(sel)
        for n in nums:
            candidates.append(n.get_text(separator=" ", strip=True))
    body_text = soup.get_text(separator=" ", strip=True)

    text = ""
    for c in candidates:
        if len(c) > len(text):
            text = c
    if len(text) < 400:  # fallback to body
        text = body_text

    # cleanup whitespace
    text = re.sub(r"\s+", " ", text)
    description = re.sub(r"\s+", " ", description)
    return title, description[:300], text[:4000]

def from_sitemaps(domain: str, sitemap_urls: List[str]) -> List[str]:
    urls = []
    seen = set()
    for sm in sitemap_urls:
        locs = get_xml_links(sm)
        # if it's a sitemap index, it returns more sitemaps
        child_sitemaps = [u for u in locs if u.endswith(".xml")]
        if child_sitemaps and len(child_sitemaps) < 2000:
            for csm in child_sitemaps:
                for u in get_xml_links(csm):
                    if u.endswith(".xml"):
                        continue
                    if urlparse.urlparse(u).netloc == urlparse.urlparse(domain).netloc and u not in seen:
                        urls.append(u); seen.add(u)
        else:
            for u in locs:
                if u.endswith(".xml"):
                    continue
                if urlparse.urlparse(u).netloc == urlparse.urlparse(domain).netloc and u not in seen:
                    urls.append(u); seen.add(u)
    return urls

def light_crawl(domain: str, rp: robotparser.RobotFileParser, limit: int = 1500) -> List[str]:
    start = domain
    q = deque([start])
    seen: Set[str] = set([start])
    out = []

    with tqdm(total=limit, desc="Crawling") as pbar:
        while q and len(out) < limit:
            url = q.popleft()
            try:
                if rp and hasattr(rp, "can_fetch") and not rp.can_fetch(HEADERS["User-Agent"], url):
                    continue
            except Exception:
                pass
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200 or not is_html(r):
                continue
            out.append(url)
            pbar.update(1)
            soup = BeautifulSoup(r.text, "lxml")
            for a in soup.find_all("a", href=True):
                nu = normalize_url(domain, a["href"])
                if nu and nu not in seen:
                    seen.add(nu)
                    q.append(nu)
            time.sleep(0.8)  # polite delay
    return out

def build_index(domain: str, max_pages: int) -> List[Dict]:
    rp, sitemaps = read_robots(domain)
    urls = []
    if sitemaps:
        urls = from_sitemaps(domain, sitemaps)
    if not urls:
        urls = light_crawl(domain, rp, limit=max_pages)
    else:
        # cap
        urls = urls[:max_pages]

    records = []
    for u in tqdm(urls, desc="Indexing"):
        try:
            if rp and hasattr(rp, "can_fetch") and not rp.can_fetch(HEADERS["User-Agent"], u):
                continue
        except Exception:
            pass
        try:
            r = requests.get(u, headers=HEADERS, timeout=20)
            if r.status_code != 200 or not is_html(r):
                continue
            title, description, text = extract_text(r.text)
            # filter halaman yang paling relevan (opsional: publikasi/berita/indikator)
            if not title and not text:
                continue
            records.append({
                "url": u,
                "title": title,
                "description": description,
                "text": text
            })
            time.sleep(0.4)  # polite
        except Exception:
            continue
    return records

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default="https://medankota.bps.go.id", help="Domain root")
    ap.add_argument("--max-pages", type=int, default=1500, help="Batas halaman")
    ap.add_argument("--out", default="../public/bps_index.json")
    args = ap.parse_args()

    domain = args.domain.rstrip("/")
    idx = build_index(domain, args.max_pages)
    out_path = Path(__file__).parent.joinpath(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "domain": domain,
            "count": len(idx),
            "generated_at": int(time.time()),
            "records": idx
        }, f, ensure_ascii=False)
    print(f"Saved index -> {out_path} ({len(idx)} pages)")

if __name__ == "__main__":
    main()