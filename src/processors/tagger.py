"""플랫폼명/기관명 자동 태거."""

from __future__ import annotations

from src.config import load_config
from src.models.article import Article


def tag_articles(articles: list[Article], config: dict | None = None) -> list[Article]:
    if config is None:
        config = load_config()

    platforms_config = config.get("platforms", {})
    all_platforms = (
        platforms_config.get("domestic", []) +
        platforms_config.get("foreign", [])
    )

    institutions = config.get("institutions", [])

    for article in articles:
        text = " ".join([
            article.title or "",
            article.description or "",
            article.content or "",
        ])

        platform_tags = [p for p in all_platforms if p in text]
        institution_tags = [i for i in institutions if i in text]

        article.platform_tags = list(set(article.platform_tags + platform_tags))
        article.institution_tags = list(set(article.institution_tags + institution_tags))

    return articles