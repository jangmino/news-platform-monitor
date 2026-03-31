"""키워드 기반 이슈 클러스터링."""

from __future__ import annotations

from collections import defaultdict

from src.models.analysis import Analysis
from src.models.article import Article
from src.models.cluster import IssueCluster
from src.utils.text_utils import generate_id


def cluster_by_keywords(
    articles: list[Article],
    analyses: list[Analysis],
) -> list[IssueCluster]:
    """LLM 추출 키워드 일치/부분 일치로 기사를 클러스터링한다."""
    # article_id → article/analysis 매핑
    article_map = {a.id: a for a in articles}
    analysis_map = {a.article_id: a for a in analyses if a.status == "completed"}

    # 키워드 → article_id 역색인
    keyword_to_articles: dict[str, list[str]] = defaultdict(list)
    for article_id, analysis in analysis_map.items():
        for kw in analysis.keywords:
            keyword_to_articles[kw].append(article_id)

    # 키워드 빈도순 정렬 (가장 많이 등장하는 키워드부터)
    sorted_keywords = sorted(
        keyword_to_articles.items(),
        key=lambda x: len(x[1]),
        reverse=True,
    )

    assigned: set[str] = set()
    clusters: list[IssueCluster] = []

    for keyword, article_ids in sorted_keywords:
        # 아직 할당되지 않은 기사만
        unassigned = [aid for aid in article_ids if aid not in assigned]
        if len(unassigned) < 2:
            continue

        # 관련 키워드 확장 (부분 일치)
        related_keywords = set()
        related_article_ids = set(unassigned)

        for other_kw, other_ids in sorted_keywords:
            if other_kw == keyword:
                continue
            # 부분 일치 체크
            if keyword in other_kw or other_kw in keyword:
                overlap = set(other_ids) & related_article_ids
                if overlap:
                    related_keywords.add(other_kw)
                    related_article_ids.update(
                        aid for aid in other_ids if aid not in assigned
                    )

        final_ids = list(related_article_ids)
        assigned.update(final_ids)

        # 클러스터 메타데이터 집계
        rep_keywords = [keyword] + sorted(related_keywords)[:4]
        all_domains = []
        all_platforms = []
        sentiments = []

        for aid in final_ids:
            if aid in analysis_map:
                a = analysis_map[aid]
                all_domains.extend(a.policy_domains)
                sentiments.append(a.sentiment)
            if aid in article_map:
                art = article_map[aid]
                all_platforms.extend(art.platform_tags)

        # 지배적 감성
        sentiment_counts = defaultdict(int)
        for s in sentiments:
            sentiment_counts[s] += 1
        dominant = max(sentiment_counts, key=sentiment_counts.get) if sentiment_counts else "neutral"

        cluster = IssueCluster(
            cluster_id=generate_id(keyword + str(len(clusters))),
            representative_keywords=rep_keywords,
            article_ids=final_ids,
            article_count=len(final_ids),
            risk_score=0.0,  # risk_scorer에서 채움
            dominant_sentiment=dominant,
            policy_domains=list(set(all_domains)),
            platform_tags=list(set(all_platforms)),
        )
        clusters.append(cluster)

    # 미할당 기사를 개별 클러스터로
    for article_id in analysis_map:
        if article_id not in assigned:
            a = analysis_map[article_id]
            art = article_map.get(article_id)
            cluster = IssueCluster(
                cluster_id=generate_id(article_id),
                representative_keywords=a.keywords[:3],
                article_ids=[article_id],
                article_count=1,
                risk_score=0.0,
                dominant_sentiment=a.sentiment,
                policy_domains=a.policy_domains,
                platform_tags=art.platform_tags if art else [],
            )
            clusters.append(cluster)

    print(f"  클러스터링: {len(clusters)}개 클러스터 생성")
    return clusters
