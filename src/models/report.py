"""BriefingReport 및 TopIssue 데이터 클래스."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TopIssue:
    rank: int
    cluster_id: str
    title: str
    summary: str
    source_links: list[str]
    policy_questions: list[str]
    risk_score: float
    requires_review: bool = False

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "cluster_id": self.cluster_id,
            "title": self.title,
            "summary": self.summary,
            "source_links": self.source_links,
            "policy_questions": self.policy_questions,
            "risk_score": self.risk_score,
            "requires_review": self.requires_review,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TopIssue":
        return cls(**d)


@dataclass
class BriefingReport:
    report_id: str
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    period_start: str = ""
    period_end: str = ""
    top_issues: list[TopIssue] = field(default_factory=list)
    heatmap_data: dict = field(default_factory=dict)
    heatmap_image_path: str = ""

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "top_issues": [i.to_dict() for i in self.top_issues],
            "heatmap_data": self.heatmap_data,
            "heatmap_image_path": self.heatmap_image_path,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BriefingReport":
        issues = [TopIssue.from_dict(i) for i in d.get("top_issues", [])]
        return cls(
            report_id=d["report_id"],
            generated_at=d.get("generated_at", ""),
            period_start=d.get("period_start", ""),
            period_end=d.get("period_end", ""),
            top_issues=issues,
            heatmap_data=d.get("heatmap_data", {}),
            heatmap_image_path=d.get("heatmap_image_path", ""),
        )
