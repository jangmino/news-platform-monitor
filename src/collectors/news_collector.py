"""Naver Search API 뉴스 수집기."""

from __future__ import annotations

import time
import requests

from src.config import load_config
from src.models.article import Article
from src.utils.file_io import save_json, raw_news_dir
from src.utils.text_utils import generate_id, normalize_text

_API_URL = "https://openapi.naver.com/v1/search/news.json"
_MAX_DISPLAY = 100
_NAVER_NEWS_PREFIX = "https://n.news.naver.com/"


def _fetch_news(query: str, client_id: str, client_secret: str,
                display: int = 100, start: int = 1) -> dict:
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {
        "query": query,
        "display": display,
        "start": start,
        "sort": "date",
    }
    response = requests.get(_API_URL, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def is_naver_news_link(url: str) -> bool:
    if not url:
        return False
    return url.startswith(_NAVER_NEWS_PREFIX)


def build_query_to_category(config: dict) -> dict[str, str]:
    query_to_category: dict[str, str] = {}

    query_categories = config.get("news_query_categories", {})
    if query_categories:
        for category, keywords in query_categories.items():
            for kw in keywords:
                query_to_category[kw] = category
        return query_to_category

    # fallback
    for kw in config.get("search_keywords", []):
        query_to_category[kw] = ""

    return query_to_category


def collect_news(config: dict | None = None) -> list[Article]:
    """카테고리별 query 기준으로 네이버 뉴스 제휴 기사만 수집한다."""
    if config is None:
        config = load_config()

    naver_config = config.get("api", {}).get("naver", {})
    client_id = naver_config.get("client_id", "")
    client_secret = naver_config.get("client_secret", "")

    if not client_id or not client_secret or "YOUR_" in client_id:
        print("Naver API 인증 정보가 설정되지 않았습니다. config.yaml을 확인하세요.")
        return []

    query_to_category = build_query_to_category(config)
    print("DEBUG news_query_categories =", config.get("news_query_categories"))
    print("DEBUG query_to_category =", query_to_category)
    if not query_to_category:
        print("검색 키워드가 설정되지 않았습니다.")
        return []

    all_articles: list[Article] = []
    total_api_calls = 0

    print("네이버 뉴스 제휴 기사만 필터링")

    for query, category in query_to_category.items():
        print(f"  [{query} / {category}] 수집 중... ", end="")
        query_articles: list[Article] = []

        try:
            data = _fetch_news(
                query,
                client_id,
                client_secret,
                display=_MAX_DISPLAY,
                start=1,
            )
            total_api_calls += 1

            items = data.get("items", [])
            for item in items:
                link = item.get("link", "")
                if not is_naver_news_link(link):
                    continue

                originallink = item.get("originallink") or ""
                canonical_url = originallink or link

                title = normalize_text(item.get("title", ""))
                description = normalize_text(item.get("description", ""))
                pub_date = item.get("pubDate", "")

                article = Article(
                    id=generate_id(canonical_url),
                    title=title,
                    content=description,  # 초기값은 description
                    url=canonical_url,
                    source_type="naver_api",
                    source_name="Naver 뉴스",
                    published_at=pub_date,
                    search_keywords=[query],
                    link=link,
                    originallink=originallink,
                    description=description,
                    query_used=query,
                    category=category,
                )
                query_articles.append(article)

            save_path = raw_news_dir() / f"{query}.json"
            save_json([a.to_dict() for a in query_articles], save_path)

            print(f"{len(query_articles)}건")
            all_articles.extend(query_articles)
            time.sleep(0.1)

        except requests.RequestException as e:
            print(f"API 오류: {e}")
            continue

    print(f"\n네이버 뉴스 필터링 후 수집된 기사 수: {len(all_articles)}")
    print(f"API 호출 수: {total_api_calls}")

    return all_articles