"""스코어링 파이프라인 — 클러스터링 + 리스크 점수 + 급상승 탐지."""

from __future__ import annotations

from datetime import date

from src.config import load_config
from src.models.article import Article
from src.models.analysis import Analysis
from src.models.cluster import IssueCluster
from src.scorers.clusterer import cluster_by_keywords
from src.scorers.risk_scorer import score_clusters
from src.scorers.trend_detector import detect_trends
from src.utils.file_io import (
    load_json, save_json, processed_dir, analyzed_dir, scored_dir,
)


def run_scoring(config: dict | None = None) -> list[IssueCluster]:
    """스코어링 파이프라인: 클러스터링 → 리스크 점수 → 급상승 탐지."""
    if config is None:
        config = load_config()

    # 데이터 로드
    articles_data = load_json(processed_dir() / "articles.json")
    analyses_data = load_json(analyzed_dir() / "analyses.json")

    if not articles_data or not analyses_data:
        print("스코어링할 데이터가 없습니다. analyze를 먼저 실행하세요.")
        return []

    articles = [Article.from_dict(d) for d in articles_data]
    analyses = [Analysis.from_dict(d) for d in analyses_data]

    # 1. 클러스터링
    clusters = cluster_by_keywords(articles, analyses)

    # 2. 리스크 점수 산출
    clusters = score_clusters(clusters, articles, analyses, config)

    # 3. 급상승 탐지
    clusters = detect_trends(clusters, config)

    # 이전 결과를 history에 백업
    clusters_path = scored_dir() / "clusters.json"
    existing = load_json(clusters_path)
    if existing:
        history_dir = scored_dir() / "history"
        history_path = history_dir / f"clusters_{date.today().isoformat()}.json"
        save_json(existing, history_path)

    # 저장
    save_json([c.to_dict() for c in clusters], clusters_path)
    print(f"\n스코어링 완료: {len(clusters)}개 클러스터")

    return clusters
