"""전처리 파이프라인 — 중복 제거 + 태깅."""

from __future__ import annotations

from src.config import load_config
from src.models.article import Article
from src.processors.deduplicator import deduplicate
from src.processors.tagger import tag_articles
from src.utils.file_io import (
    load_json, save_json, raw_rss_dir, raw_news_dir, processed_dir,
)


def run_preprocess(config: dict | None = None) -> list[Article]:
    """전처리 파이프라인: RSS + News 통합, 중복 제거, 태깅."""
    if config is None:
        config = load_config()

    # 1. 모든 raw 데이터 로드
    all_articles = []

    # RSS 데이터
    rss_dir = raw_rss_dir()
    if rss_dir.exists():
        for f in rss_dir.glob("*.json"):
            data = load_json(f)
            if isinstance(data, list):
                all_articles.extend([Article.from_dict(d) for d in data])

    # News 데이터
    news_dir = raw_news_dir()
    if news_dir.exists():
        for f in news_dir.glob("*.json"):
            data = load_json(f)
            if isinstance(data, list):
                all_articles.extend([Article.from_dict(d) for d in data])

    print(f"  로드: RSS + News 합계 {len(all_articles)}건")

    if not all_articles:
        print("  전처리할 데이터가 없습니다.")
        return []

    # 2. 중복 제거
    articles = deduplicate(all_articles)

    # 3. 태깅
    articles = tag_articles(articles, config)

    tagged_count = sum(
        1 for a in articles
        if a.platform_tags or a.institution_tags
    )
    print(f"  태깅: {tagged_count}건에 플랫폼/기관 태그 부착")

    # 4. 저장
    save_path = processed_dir() / "articles.json"
    save_json([a.to_dict() for a in articles], save_path)
    print(f"  저장: {save_path} ({len(articles)}건)")

    return articles
