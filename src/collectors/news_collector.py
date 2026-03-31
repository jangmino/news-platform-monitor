"""Naver Search API 뉴스 수집기."""

from __future__ import annotations

import time

import requests

from src.config import load_config
from src.models.article import Article
from src.utils.file_io import load_json, save_json, raw_news_dir
from src.utils.text_utils import generate_id, normalize_text


_API_URL = "https://openapi.naver.com/v1/search/news.json"
_MAX_DISPLAY = 100
_MAX_START = 901  # start 최대 1000, display=100이면 901까지


def _fetch_news(query: str, client_id: str, client_secret: str,
                display: int = 100, start: int = 1) -> dict:
    """Naver 뉴스 검색 API를 호출한다."""
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


def collect_news(config: dict | None = None) -> list[Article]:
    """정책 키워드별로 Naver 뉴스를 수집한다."""
    if config is None:
        config = load_config()

    naver_config = config.get("api", {}).get("naver", {})
    client_id = naver_config.get("client_id", "")
    client_secret = naver_config.get("client_secret", "")

    if not client_id or not client_secret or "YOUR_" in client_id:
        print("Naver API 인증 정보가 설정되지 않았습니다. config.yaml을 확인하세요.")
        return []

    keywords = config.get("search_keywords", [])
    if not keywords:
        print("검색 키워드가 설정되지 않았습니다.")
        return []

    all_articles = []
    total_api_calls = 0

    for keyword in keywords:
        print(f"  [{keyword}] 수집 중... ", end="")
        keyword_articles = []

        try:
            for start in range(1, _MAX_START + 1, _MAX_DISPLAY):
                # API 한도 체크 (보수적)
                if total_api_calls >= 24000:
                    print("\nAPI 일일 호출 한도에 근접합니다. 수집을 중단합니다.")
                    break

                data = _fetch_news(keyword, client_id, client_secret,
                                   display=_MAX_DISPLAY, start=start)
                total_api_calls += 1

                items = data.get("items", [])
                if not items:
                    break

                for item in items:
                    url = item.get("originallink") or item.get("link", "")
                    if not url:
                        continue

                    title = normalize_text(item.get("title", ""))
                    description = normalize_text(item.get("description", ""))
                    pub_date = item.get("pubDate", "")

                    article = Article(
                        id=generate_id(url),
                        title=title,
                        content=description,
                        url=url,
                        source_type="naver_api",
                        source_name="Naver 뉴스",
                        published_at=pub_date,
                        search_keywords=[keyword],
                    )
                    keyword_articles.append(article)

                # 결과가 display보다 적으면 마지막 페이지
                if len(items) < _MAX_DISPLAY:
                    break

                time.sleep(0.1)  # API rate limiting

        except requests.RequestException as e:
            print(f"API 오류: {e}")
            continue

        # 키워드별 저장
        save_path = raw_news_dir() / f"{keyword}.json"
        save_json([a.to_dict() for a in keyword_articles], save_path)

        print(f"{len(keyword_articles)}건")
        all_articles.extend(keyword_articles)

    print(f"\n뉴스 수집 완료: 총 {len(all_articles)}건, API 호출 {total_api_calls}회")
    return all_articles
