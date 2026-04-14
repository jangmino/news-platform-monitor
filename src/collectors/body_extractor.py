"""네이버 뉴스 본문 추출기."""

from __future__ import annotations

import time

import requests
from bs4 import BeautifulSoup

from src.models.article import Article

_USER_AGENT = "Mozilla/5.0"
_SELECTORS = [
    "#dic_area",
    "#newsct_article",
    "div#articeBody",
    "div.article_body",
    "div.news_end",
    "div#newsEndContents",
    "article",
]


def fetch_article_body(url: str, timeout: int = 15) -> str | None:
    try:
        res = requests.get(url, headers={"User-Agent": _USER_AGENT}, timeout=timeout)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")

        for sel in _SELECTORS:
            node = soup.select_one(sel)
            if node:
                text = node.get_text(" ", strip=True)
                if len(text) > 100:
                    return text

        return None

    except Exception as e:
        print(f"[에러] {url} / {e}")
        return None


def enrich_news_bodies(articles: list[Article], sleep_sec: float = 0.3) -> list[Article]:
    """중복 제거 후 뉴스 기사 본문을 네이버 링크 기준으로 보강한다."""
    success = 0
    fail = 0

    for i, article in enumerate(articles, start=1):
        if article.source_type != "naver_api":
            continue

        body = None
        target_url = article.link or article.url

        if target_url:
            body = fetch_article_body(target_url)

        if body:
            article.content = body
            success += 1
        else:
            fail += 1

        time.sleep(sleep_sec)

    print("\n[본문 수집 결과]")
    print(f"성공: {success}개")
    print(f"실패: {fail}개")
    print(f"전체: {sum(1 for a in articles if a.source_type == 'naver_api')}개")

    return articles