"""뉴스/보도자료 중복 제거기."""

from __future__ import annotations

from src.models.article import Article


def dedup_key(article: Article) -> str:
    return article.originallink or article.link or article.url or article.title


def deduplicate(articles: list[Article]) -> list[Article]:
    seen: dict[str, Article] = {}

    for article in articles:
        key = dedup_key(article)

        if key in seen:
            existing = seen[key]

            existing.search_keywords = list(set(
                existing.search_keywords + article.search_keywords
            ))

            if article.category and article.category not in existing.category.split(","):
                if existing.category:
                    existing.category = ",".join(
                        sorted(set(existing.category.split(",") + [article.category]))
                    )
                else:
                    existing.category = article.category
        else:
            seen[key] = article

    deduped = list(seen.values())
    removed = len(articles) - len(deduped)

    if removed > 0:
        print(f"중복 제거 후 기사 수: {len(deduped)} (제거 {removed}건)")
    else:
        print(f"중복 제거 후 기사 수: {len(deduped)}")

    return deduped