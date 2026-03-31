"""플랫폼명/기관명 자동 태거."""

from __future__ import annotations

from src.config import load_config
from src.models.article import Article


def tag_articles(articles: list[Article], config: dict | None = None) -> list[Article]:
    """기사 목록에 플랫폼명과 기관명 태그를 부착한다."""
    if config is None:
        config = load_config()

    # 플랫폼 사전 로드
    platforms_config = config.get("platforms", {})
    all_platforms = (
        platforms_config.get("domestic", []) +
        platforms_config.get("foreign", [])
    )

    # 기관 사전 로드
    institutions = config.get("institutions", [])

    for article in articles:
        text = f"{article.title} {article.content}"

        # 플랫폼 태깅
        platform_tags = [p for p in all_platforms if p in text]
        article.platform_tags = list(set(article.platform_tags + platform_tags))

        # 기관 태깅
        institution_tags = [i for i in institutions if i in text]
        article.institution_tags = list(set(article.institution_tags + institution_tags))

    return articles
