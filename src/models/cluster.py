"""IssueCluster 데이터 클래스 — 이슈 클러스터."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class IssueCluster:
    cluster_id: str
    representative_keywords: list[str]
    article_ids: list[str]
    article_count: int
    risk_score: float  # 0~100
    is_trending: bool = False
    trending_reason: Optional[str] = None
    requires_review: bool = False
    dominant_sentiment: str = "neutral"
    policy_domains: list[str] = field(default_factory=list)
    platform_tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "cluster_id": self.cluster_id,
            "representative_keywords": self.representative_keywords,
            "article_ids": self.article_ids,
            "article_count": self.article_count,
            "risk_score": self.risk_score,
            "is_trending": self.is_trending,
            "trending_reason": self.trending_reason,
            "requires_review": self.requires_review,
            "dominant_sentiment": self.dominant_sentiment,
            "policy_domains": self.policy_domains,
            "platform_tags": self.platform_tags,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "IssueCluster":
        return cls(**d)
