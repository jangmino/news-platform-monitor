"""급상승 이슈 탐지기."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from src.config import load_config
from src.models.cluster import IssueCluster
from src.utils.file_io import load_json, scored_dir


def _load_previous_clusters() -> list[IssueCluster] | None:
    """이전 주 클러스터 데이터를 로드한다."""
    clusters_dir = scored_dir()
    if not clusters_dir.exists():
        return None

    # history/ 디렉토리에서 이전 파일 찾기
    history_dir = clusters_dir / "history"
    if not history_dir.exists():
        return None

    history_files = sorted(history_dir.glob("clusters_*.json"))
    if not history_files:
        return None

    # 가장 최근 파일 로드
    prev_data = load_json(history_files[-1])
    if not prev_data:
        return None

    return [IssueCluster.from_dict(d) for d in prev_data]


def detect_trends(
    clusters: list[IssueCluster],
    config: dict | None = None,
) -> list[IssueCluster]:
    """급상승 이슈를 탐지한다."""
    if config is None:
        config = load_config()

    trending_ratio = config.get("risk", {}).get("trending_ratio", 2.0)

    # 이전 데이터 로드
    prev_clusters = _load_previous_clusters()

    if prev_clusters is None:
        print("  급상승 탐지: 이전 데이터 없음 (최초 실행) — 건너뜀")
        return clusters

    # 이전 키워드별 기사 수 매핑
    prev_keyword_counts: dict[str, int] = {}
    for pc in prev_clusters:
        for kw in pc.representative_keywords:
            prev_keyword_counts[kw] = max(
                prev_keyword_counts.get(kw, 0),
                pc.article_count,
            )

    trending_count = 0
    for cluster in clusters:
        for kw in cluster.representative_keywords:
            prev_count = prev_keyword_counts.get(kw, 0)
            if prev_count > 0:
                ratio = cluster.article_count / prev_count
                if ratio >= trending_ratio:
                    cluster.is_trending = True
                    cluster.trending_reason = (
                        f"키워드 '{kw}' 언급량 {ratio:.1f}배 증가 "
                        f"(전주 {prev_count}건 → 금주 {cluster.article_count}건)"
                    )
                    trending_count += 1
                    break

    print(f"  급상승 탐지: {trending_count}건 급상승 이슈 발견")
    return clusters
