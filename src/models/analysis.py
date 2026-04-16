"""Analysis 데이터 클래스 — LLM 분석 결과."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Analysis:
    article_id: str
    summary: str
    keywords: list[str]
    sentiment: str  # "positive" | "negative" | "neutral"
    sentiment_confidence: float
    policy_domains: list[str]  # 멀티라벨
    policy_confidence: float
    analyzed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    model_used: str = ""
    status: str = "analyzed"  # "analyzed" | "failed" | "skipped"
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "article_id": self.article_id,
            "summary": self.summary,
            "keywords": self.keywords,
            "sentiment": self.sentiment,
            "sentiment_confidence": self.sentiment_confidence,
            "policy_domains": self.policy_domains,
            "policy_confidence": self.policy_confidence,
            "analyzed_at": self.analyzed_at,
            "model_used": self.model_used,
            "status": self.status,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Analysis":
        return cls(**d)
