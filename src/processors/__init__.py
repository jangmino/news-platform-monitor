"""전처리 파이프라인 — 중복 제거 + 태깅 + 관련 기사 본문 보강."""

from __future__ import annotations

from src.config import load_config
from src.models.article import Article
from src.processors.deduplicator import deduplicate
from src.processors.tagger import tag_articles
from src.collectors.body_extractor import enrich_news_bodies
from src.utils.file_io import (
    load_json,
    save_json,
    raw_rss_dir,
    raw_news_dir,
    processed_dir,
)


def run_preprocess(config: dict | None = None) -> list[Article]:
    if config is None:
        config = load_config()

    all_articles: list[Article] = []

    rss_dir = raw_rss_dir()
    if rss_dir.exists():
        for f in rss_dir.glob("*.json"):
            data = load_json(f)
            if isinstance(data, list):
                all_articles.extend([Article.from_dict(d) for d in data])

    news_dir = raw_news_dir()
    if news_dir.exists():
        for f in news_dir.glob("*.json"):
            data = load_json(f)
            if isinstance(data, list):
                all_articles.extend([Article.from_dict(d) for d in data])

    print(f"로드된 전체 기사 수: {len(all_articles)}건")

    if not all_articles:
        print("전처리할 데이터가 없습니다.")
        return []

    # 1. 중복 제거
    articles = deduplicate(all_articles)
    print(f"중복 제거 후 기사 수: {len(articles)}")

    # 2. 먼저 태깅
    articles = tag_articles(articles, config)

    tagged_articles = [
        a for a in articles
        if a.platform_tags or a.institution_tags
    ]
    print(f"태그 있는 기사 수: {len(tagged_articles)}")

    # 3. 태그 있는 기사만 본문 보강
    tagged_articles = enrich_news_bodies(tagged_articles, sleep_sec=0.3)

    # 4. 저장
    save_path = processed_dir() / "articles.json"
    save_json([a.to_dict() for a in tagged_articles], save_path)
    print(f"저장 완료: {save_path} ({len(tagged_articles)}건)")

    return tagged_articles