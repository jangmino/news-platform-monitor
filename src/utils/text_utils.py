"""텍스트 처리 유틸리티."""

from __future__ import annotations

import hashlib
import re


def remove_html_tags(text: str) -> str:
    """HTML 태그를 제거한다."""
    return re.sub(r"<[^>]+>", "", text)


def normalize_text(text: str) -> str:
    """텍스트를 정규화한다 (연속 공백 제거, strip)."""
    text = remove_html_tags(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_content_sufficient(text: str, min_length: int = 100) -> bool:
    """본문이 분석에 충분한 길이인지 확인한다."""
    return len(text.strip()) >= min_length


def generate_id(url: str) -> str:
    """URL로부터 고유 ID를 생성한다 (SHA-256 해시 앞 16자)."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
