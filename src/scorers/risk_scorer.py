"""리스크 점수 산출."""

from __future__ import annotations

from collections import defaultdict

from src.config import load_config
from src.models.analysis import Analysis
from src.models.article import Article
from src.models.cluster import IssueCluster


def score_clusters(
    clusters: list[IssueCluster],
    articles: list[Article],
    analyses: list[Analysis],
    config: dict | None = None,
) -> list[IssueCluster]:
    """클러스터별 리스크 점수를 산출하고 requires_review를 설정한다."""
    if config is None:
        config = load_config()

    threshold = config.get("risk", {}).get("threshold", 70)

    article_map = {a.id: a for a in articles}
    analysis_map = {a.article_id: a for a in analyses if a.status == "completed"}

    for cluster in clusters:
        score = 0.0

        # 1. 기사 수 기반 (최대 30점)
        count_score = min(cluster.article_count * 5, 30)
        score += count_score

        # 2. 규제기관 동반 언급 빈도 (최대 25점)
        institution_count = 0
        for aid in cluster.article_ids:
            art = article_map.get(aid)
            if art and art.institution_tags:
                institution_count += 1
        institution_ratio = institution_count / max(cluster.article_count, 1)
        score += institution_ratio * 25

        # 3. 부정 감성 비율 (최대 25점)
        negative_count = 0
        for aid in cluster.article_ids:
            a = analysis_map.get(aid)
            if a and a.sentiment == "negative":
                negative_count += 1
        negative_ratio = negative_count / max(cluster.article_count, 1)
        score += negative_ratio * 25

        # 4. 정책영역 다중 해당 (최대 20점)
        domain_count = len(cluster.policy_domains)
        score += min(domain_count * 5, 20)

        cluster.risk_score = round(min(score, 100), 1)
        cluster.requires_review = cluster.risk_score >= threshold

    reviewed = sum(1 for c in clusters if c.requires_review)
    print(f"  리스크 스코어링: {reviewed}건 사람 확인 필요 (임계값 {threshold})")
    return clusters
