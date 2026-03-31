"""URL 기반 중복 제거기."""

from __future__ import annotations

from src.models.article import Article


def deduplicate(articles: list[Article]) -> list[Article]:
    """URL 기반으로 중복 기사를 제거하고, 키워드 태그를 병합한다."""
    seen: dict[str, Article] = {}

    for article in articles:
        if article.url in seen:
            # 키워드 병합
            existing = seen[article.url]
            merged_keywords = list(set(
                existing.search_keywords + article.search_keywords
            ))
            existing.search_keywords = merged_keywords
        else:
            seen[article.url] = article

    deduped = list(seen.values())
    removed = len(articles) - len(deduped)
    if removed > 0:
        print(f"  중복 제거: {removed}건 제거, {len(deduped)}건 유지")

    return deduped
