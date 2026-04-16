"""뉴스 기사 전용 Gemini 분석기.

data/processed/articles.json → news_analysis.json (embedded 분석 결과)
- 플랫폼 추출, 정책영역 분류, 리스크 점수, 키워드, 요약, 감성, 신뢰도
- 증분 분석: id 기준 기존 결과 재사용 (없으면 link/url 대체)
- Atomic write: tmpfile → rename
- 완료 후 dashboard/public/data/ 에 복사
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path

from google import genai

from src.config import load_config
from src.utils.file_io import (
    load_json, ensure_dir, processed_dir, analyzed_dir,
    atomic_write, copy_to_dashboard,
)


_MIN_CONTENT_LENGTH = 30  # title+description 합산 기준

_PROMPT = """다음 뉴스 기사를 분석하세요. 반드시 원문에 있는 내용만 기반으로 하고, 원문에 없는 내용을 추가하지 마세요.

## 기사 제목
{title}

## 기사 요약
{content}

## 분석 요청
다음 JSON 형식으로만 응답하세요 (다른 텍스트 없이 JSON만):

{{
  "platforms": ["언급된 플랫폼명1", "플랫폼명2"],
  "policy_domains": ["해당 정책영역1"],
  "risk_score": 50,
  "keywords": ["핵심키워드1", "키워드2", "키워드3", "키워드4", "키워드5"],
  "summary": "3문장 이내 한국어 요약",
  "sentiment": "중립",
  "confidence": 0.85
}}

platforms는 다음 목록 중 본문에서 직접 언급된 것만 선택하세요 (없으면 빈 배열):
{platforms}

policy_domains는 다음 중 해당하는 것을 모두 선택하세요 (멀티라벨, 없으면 빈 배열):
{domains}

risk_score 기준 (정수 0~100):
- 0~30: 중립적 정보 제공, 정책 발표
- 31~60: 규제 논의, 제도 개선, 조사 착수
- 61~80: 과징금·처분·갈등 본격화
- 81~100: 심각한 법적 제재, 긴급 규제, 소비자 피해

keywords는 최대 5개, 본문 핵심 주제어를 추출하세요.
sentiment: "긍정" / "부정" / "중립" 중 하나.
confidence: 전체 분석 신뢰도 0.0~1.0.
"""


def _clean_html(text: str) -> str:
    """HTML 태그를 제거한다."""
    return re.sub(r"<[^>]+>", "", text).strip()


def _build_input_text(article: dict) -> str:
    """분석 입력 텍스트를 구성한다 (title + content, 최대 600자)."""
    title = _clean_html(article.get("title", ""))
    content = _clean_html(article.get("content", ""))
    return (title + "\n" + content)[:600]


def _dedup_key(article: dict) -> str:
    """증분 분석용 중복 판별 키를 반환한다."""
    return article.get("id") or article.get("link") or article.get("url", "")


def _parse_response(text: str) -> dict | None:
    text = text.strip()
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


def _validate_result(result: dict, valid_platforms: list[str], valid_domains: list[str]) -> dict:
    """API 응답 결과를 검증·정제한다."""
    raw_platforms = result.get("platforms", [])
    raw_domains = result.get("policy_domains", [])

    platforms = [p for p in raw_platforms if p in valid_platforms]
    domains = [d for d in raw_domains if d in valid_domains]

    risk_score = result.get("risk_score", 0)
    if not isinstance(risk_score, int):
        try:
            risk_score = int(float(risk_score))
        except (ValueError, TypeError):
            risk_score = 0
    risk_score = max(0, min(100, risk_score))

    keywords = result.get("keywords", [])
    if isinstance(keywords, list):
        keywords = [str(k) for k in keywords[:5]]
    else:
        keywords = []

    sentiment = result.get("sentiment", "중립")
    if sentiment not in ("긍정", "부정", "중립"):
        sentiment = "중립"

    confidence = result.get("confidence", 0.0)
    try:
        confidence = float(confidence)
        confidence = max(0.0, min(1.0, confidence))
    except (ValueError, TypeError):
        confidence = 0.0

    summary = str(result.get("summary", "")).strip()

    return {
        "platforms": platforms,
        "policy_domains": domains,
        "risk_score": risk_score,
        "keywords": keywords,
        "summary": summary,
        "sentiment": sentiment,
        "confidence": confidence,
    }


def _analyze_single(
    client,
    model: str,
    article: dict,
    valid_platforms: list[str],
    valid_domains: list[str],
) -> dict:
    """단일 뉴스 기사를 분석하여 분석 필드를 반환한다."""
    all_platforms = ", ".join(valid_platforms)
    all_domains = ", ".join(valid_domains)

    input_text = _build_input_text(article)
    title = _clean_html(article.get("title", ""))

    prompt = _PROMPT.format(
        title=title,
        content=input_text,
        platforms=all_platforms,
        domains=all_domains,
    )

    response = client.models.generate_content(model=model, contents=prompt)
    result = _parse_response(response.text)

    if not result:
        return {
            "platforms": [],
            "policy_domains": [],
            "risk_score": 0,
            "keywords": [],
            "summary": "",
            "sentiment": "중립",
            "confidence": 0.0,
            "status": "parse_error",
            "raw_response": response.text[:500],
        }

    validated = _validate_result(result, valid_platforms, valid_domains)
    validated["status"] = "analyzed"
    validated["raw_response"] = None
    return validated


def run_news_analysis(config: dict | None = None, force: bool = False) -> dict:
    """뉴스 기사 JSON을 Gemini API로 분석하고 결과를 저장한다.

    Returns:
        news_analysis dict (저장된 데이터와 동일)
    """
    if config is None:
        config = load_config()

    gemini_cfg = config.get("api", {}).get("gemini", {})
    api_key = gemini_cfg.get("api_key", "")
    model = gemini_cfg.get("model", "gemini-2.5-flash-lite")

    if not api_key or api_key.startswith("YOUR_"):
        raise ValueError("Gemini API 키가 설정되지 않았습니다. GEMINI_API_KEY 환경변수 또는 config.yaml을 확인하세요.")

    # config에서 유효 목록 로드
    platforms_cfg = config.get("platforms", {})
    valid_platforms: list[str] = (
        platforms_cfg.get("domestic", []) + platforms_cfg.get("foreign", [])
    )
    valid_domains: list[str] = config.get("policy_domains", [])

    # 입력 로드
    input_path = processed_dir() / "articles.json"
    if not input_path.exists():
        print("전처리 데이터가 없습니다. 먼저 'python -m src collect --news && python -m src preprocess'를 실행하세요.")
        return {}

    articles: list[dict] = load_json(input_path)  # type: ignore
    if not articles:
        print("분석할 뉴스 기사가 없습니다. 먼저 collect를 실행하세요.")
        return {}

    # 기존 분석 결과 로드 (증분 분석용)
    output_path = analyzed_dir() / "news_analysis.json"
    existing: dict = {}  # dedup_key → analyzed_article (캐시)
    if not force and output_path.exists():
        try:
            existing_data = json.loads(output_path.read_text(encoding="utf-8"))
            for a in existing_data.get("articles", []):
                key = _dedup_key(a)
                if key and a.get("status") in ("analyzed", "skipped"):
                    existing[key] = a
        except (json.JSONDecodeError, KeyError):
            pass

    # Gemini 클라이언트
    client = genai.Client(api_key=api_key)

    analyzed_articles: list[dict] = []
    new_count = 0
    fail_count = 0
    skip_count = 0

    total = len(articles)
    print(f"뉴스 기사 {total}건 중 분석 시작 (기존 캐시: {len(existing)}건)")

    for i, article in enumerate(articles, 1):
        key = _dedup_key(article)

        # 증분: 이미 분석된 항목
        if key and key in existing and not force:
            analyzed_articles.append(existing[key])
            continue

        # 입력 텍스트 길이 체크
        input_text = _build_input_text(article)
        if len(input_text) < _MIN_CONTENT_LENGTH:
            result_article = {
                **article,
                "platforms": [], "policy_domains": [],
                "risk_score": 0, "keywords": [], "summary": "",
                "sentiment": "중립", "confidence": 0.0,
                "status": "skipped", "raw_response": None,
                "source_type": "news",
            }
            analyzed_articles.append(result_article)
            skip_count += 1
            continue

        title_preview = _clean_html(article.get("title", ""))[:45]
        print(f"  [{i}/{total}] {title_preview}... ", end="", flush=True)

        try:
            analysis = _analyze_single(client, model, article, valid_platforms, valid_domains)
            result_article = {**article, **analysis, "source_type": "news"}
            analyzed_articles.append(result_article)

            if analysis["status"] == "analyzed":
                new_count += 1
                print(f"완료 (risk={analysis['risk_score']}, platforms={analysis['platforms']})")
            else:
                fail_count += 1
                print("파싱 오류")

        except Exception as e:
            result_article = {
                **article,
                "platforms": [], "policy_domains": [],
                "risk_score": 0, "keywords": [], "summary": "",
                "sentiment": "중립", "confidence": 0.0,
                "status": "failed", "raw_response": str(e)[:200],
                "source_type": "news",
            }
            analyzed_articles.append(result_article)
            fail_count += 1
            print(f"오류: {e}")

        time.sleep(1.0)

    analyzed_count = sum(1 for a in analyzed_articles if a.get("status") == "analyzed")

    output: dict = {
        "generated_at": datetime.now().isoformat(),
        "total_count": len(analyzed_articles),
        "analyzed_count": analyzed_count,
        "articles": analyzed_articles,
    }

    # atomic write
    atomic_write(output, output_path)
    print(f"\n분석 결과 저장: {output_path}")
    print(f"신규 분석 {new_count}건 | 실패 {fail_count}건 | 스킵 {skip_count}건 | 총 완료 {analyzed_count}건")

    # dashboard 복사
    copy_to_dashboard(output_path, "news_analysis.json")

    return output
