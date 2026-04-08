"""보도자료 상세 페이지 크롤링 및 본문 추출기."""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup


_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": _USER_AGENT})

_NOISE_TAGS = ["script", "style", "iframe", "button", "ins"]
_GENERIC_SELECTORS = [
    "div.view-cont",
    "div.news-content",
    "div.article-content",
    "#articleBodyContents",
]


def extract_web_text(soup: BeautifulSoup, url: str) -> str:
    """파싱된 HTML에서 본문 텍스트를 추출한다.

    korea.kr 페이지 유형별 선택자를 우선 적용하고,
    실패 시 범용 선택자 → 최다 p태그 div 순으로 fallback한다.
    """

    def _clean(tag) -> str:
        for noise in tag(_NOISE_TAGS):
            noise.decompose()
        return tag.get_text("\n", strip=True)

    # 1. pressReleaseView 최적화
    if "pressReleaseView" in url:
        target = soup.select_one("div.view-cont")
        if target:
            text = _clean(target)
            if len(text) > 50:
                return text

    # 2. policyNewsView 최적화
    if "policyNewsView" in url:
        target = soup.select_one("div.news-content") or soup.select_one("#articleBody")
        if target:
            text = _clean(target)
            if len(text) > 50:
                return text

    # 3. 범용 선택자
    for selector in _GENERIC_SELECTORS:
        target = soup.select_one(selector)
        if target:
            text = target.get_text("\n", strip=True)
            if len(text) > 50:
                return text

    # 4. Fallback: p태그 수와 텍스트 길이 기준으로 최적 div 선택
    all_divs = soup.find_all("div")
    if all_divs:
        best = max(
            all_divs,
            key=lambda d: len(d.find_all("p")) + len(d.get_text()) / 1000,
        )
        return best.get_text("\n", strip=True)

    return ""


def crawl_page(url: str, timeout: int = 20) -> tuple[str, list[dict]]:
    """보도자료 상세 페이지를 크롤링하여 본문과 첨부파일 목록을 반환한다.

    Args:
        url: 보도자료 상세 페이지 URL
        timeout: HTTP 요청 타임아웃 (초)

    Returns:
        (web_text, file_list)
        - web_text: 추출된 본문 텍스트. 추출 실패 시 빈 문자열.
        - file_list: [{"name": str, "url": str}, ...] 발견된 첨부파일 목록.
    """
    try:
        resp = _SESSION.get(url, timeout=timeout)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")

        web_text = extract_web_text(soup, url)

        file_list: list[dict] = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if any(key in href for key in ["fileId=", "download", "attachment"]):
                name = link.get_text(strip=True).lower()
                full_url = (
                    href if href.startswith("http") else "https://www.korea.kr" + href
                )
                file_list.append({"name": name, "url": full_url})

        return web_text, file_list

    except Exception:
        return "", []
