"""Gemini API 분석기 — 요약, 키워드, 감성, 정책영역 분류."""

from __future__ import annotations

import json
import time

from google import genai

from src.config import load_config
from src.models.article import Article
from src.models.analysis import Analysis
from src.utils.file_io import load_json, save_json, processed_dir, analyzed_dir
from src.utils.text_utils import is_content_sufficient


_POLICY_DOMAINS = [
    "공정거래", "소비자보호", "개인정보", "노동",
    "콘텐츠/저작권", "안전", "AI/자동화",
]

_ANALYSIS_PROMPT = """다음 뉴스 기사를 분석하세요. 반드시 원문에 있는 내용만 기반으로 분석하고, 원문에 없는 내용을 추가하지 마세요.

## 기사 제목
{title}

## 기사 본문
{content}

## 분석 요청
다음 JSON 형식으로 응답하세요 (다른 텍스트 없이 JSON만):

{{
  "summary": "한국어 요약 (3문장 이내, 원문 기반만)",
  "keywords": ["핵심 키워드1", "키워드2", ...],
  "sentiment": "positive 또는 negative 또는 neutral",
  "sentiment_confidence": 0.0~1.0 사이의 신뢰도,
  "policy_domains": ["해당 정책영역1", ...],
  "policy_confidence": 0.0~1.0 사이의 신뢰도
}}

키워드는 최대 5개까지만 추출하세요.
정책영역은 다음 7개 중 해당하는 것을 모두 선택하세요 (멀티라벨):
{domains}

정책영역에 해당하지 않으면 빈 리스트 []로 응답하세요.
"""


def _parse_response(text: str) -> dict | None:
    """Gemini 응답에서 JSON을 파싱한다."""
    text = text.strip()
    # ```json 블록 제거
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _analyze_single(client, model: str, article: Article) -> Analysis:
    """단일 기사를 분석한다."""
    prompt = _ANALYSIS_PROMPT.format(
        title=article.title,
        content=article.content[:3000],  # 토큰 절약
        domains=", ".join(_POLICY_DOMAINS),
    )

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    result = _parse_response(response.text)
    if not result:
        return Analysis(
            article_id=article.id,
            summary="",
            keywords=[],
            sentiment="neutral",
            sentiment_confidence=0.0,
            policy_domains=[],
            policy_confidence=0.0,
            model_used=model,
            status="failed",
            error_message="JSON 파싱 실패",
        )

    # 정책영역 유효성 검증
    valid_domains = [d for d in result.get("policy_domains", []) if d in _POLICY_DOMAINS]

    return Analysis(
        article_id=article.id,
        summary=result.get("summary", ""),
        keywords=result.get("keywords", [])[:5],
        sentiment=result.get("sentiment", "neutral"),
        sentiment_confidence=float(result.get("sentiment_confidence", 0.0)),
        policy_domains=valid_domains,
        policy_confidence=float(result.get("policy_confidence", 0.0)),
        model_used=model,
        status="completed",
    )


def run_analysis(config: dict | None = None, force: bool = False) -> list[Analysis]:
    """전처리된 기사들에 대해 LLM 분석을 수행한다."""
    if config is None:
        config = load_config()

    gemini_config = config.get("api", {}).get("gemini", {})
    api_key = gemini_config.get("api_key", "")
    model = gemini_config.get("model", "gemini-2.5-flash-lite")

    if not api_key or "YOUR_" in api_key:
        print("Gemini API 키가 설정되지 않았습니다. config.yaml을 확인하세요.")
        return []

    # 기사 로드
    articles_path = processed_dir() / "articles.json"
    articles_data = load_json(articles_path)
    if not articles_data:
        print("분석할 기사가 없습니다. collect → preprocess를 먼저 실행하세요.")
        return []

    articles = [Article.from_dict(d) for d in articles_data]

    # 기존 분석 결과 로드
    analyses_path = analyzed_dir() / "analyses.json"
    existing_data = load_json(analyses_path)
    existing_analyses = [Analysis.from_dict(d) for d in existing_data] if existing_data else []
    analyzed_ids = {a.article_id for a in existing_analyses} if not force else set()

    # Gemini 클라이언트 초기화
    client = genai.Client(api_key=api_key)

    new_analyses = []
    total = len(articles)
    skipped_short = 0

    for i, article in enumerate(articles, 1):
        # 이미 분석된 항목 스킵
        if article.id in analyzed_ids:
            continue

        # 본문 길이 체크
        if not is_content_sufficient(article.content):
            analysis = Analysis(
                article_id=article.id,
                summary="",
                keywords=[],
                sentiment="neutral",
                sentiment_confidence=0.0,
                policy_domains=[],
                policy_confidence=0.0,
                model_used=model,
                status="skipped",
                error_message="본문 100자 미만",
            )
            new_analyses.append(analysis)
            skipped_short += 1
            continue

        print(f"  [{i}/{total}] {article.title[:50]}... ", end="")

        try:
            analysis = _analyze_single(client, model, article)
            new_analyses.append(analysis)
            print(f"{'완료' if analysis.status == 'completed' else '실패'}")
        except Exception as e:
            analysis = Analysis(
                article_id=article.id,
                summary="",
                keywords=[],
                sentiment="neutral",
                sentiment_confidence=0.0,
                policy_domains=[],
                policy_confidence=0.0,
                model_used=model,
                status="failed",
                error_message=str(e),
            )
            new_analyses.append(analysis)
            print(f"오류: {e}")

        time.sleep(0.5)  # API rate limiting

    # 결과 저장 (기존 + 신규)
    all_analyses = existing_analyses + new_analyses if not force else new_analyses
    save_json([a.to_dict() for a in all_analyses], analyses_path)

    completed = sum(1 for a in new_analyses if a.status == "completed")
    failed = sum(1 for a in new_analyses if a.status == "failed")
    print(f"\n분석 완료: 신규 {completed}건 완료, {failed}건 실패, {skipped_short}건 스킵")
    return all_analyses
