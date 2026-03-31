"""Article 데이터 클래스 — 수집된 뉴스 기사/보도자료."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class FileInfo:
    name: str
    url: str
    parse_status: str = "pending"  # pending, success, failed


@dataclass
class Article:
    id: str  # URL 해시값
    title: str
    content: str
    url: str  # 중복 판별 기준
    source_type: str  # "rss" | "naver_api"
    source_name: str  # 출처 기관명
    published_at: str  # 게시일
    collected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    search_keywords: list[str] = field(default_factory=list)
    platform_tags: list[str] = field(default_factory=list)
    institution_tags: list[str] = field(default_factory=list)
    file_info: Optional[FileInfo] = None

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "source_type": self.source_type,
            "source_name": self.source_name,
            "published_at": self.published_at,
            "collected_at": self.collected_at,
            "search_keywords": self.search_keywords,
            "platform_tags": self.platform_tags,
            "institution_tags": self.institution_tags,
            "file_info": None,
        }
        if self.file_info:
            d["file_info"] = {
                "name": self.file_info.name,
                "url": self.file_info.url,
                "parse_status": self.file_info.parse_status,
            }
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Article":
        fi = d.get("file_info")
        file_info = FileInfo(**fi) if fi else None
        return cls(
            id=d["id"],
            title=d["title"],
            content=d["content"],
            url=d["url"],
            source_type=d["source_type"],
            source_name=d["source_name"],
            published_at=d["published_at"],
            collected_at=d.get("collected_at", ""),
            search_keywords=d.get("search_keywords", []),
            platform_tags=d.get("platform_tags", []),
            institution_tags=d.get("institution_tags", []),
            file_info=file_info,
        )
