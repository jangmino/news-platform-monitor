"""AI 정책 제언 생성기.

분석 완료된 보도자료 전체를 종합하여 Gemini API로
정책 제언 3개(title + description)를 생성한다.

재생성 조건: analyzed_count가 이전 생성 시점과 달라진 경우만.

`generate_combined_recommendations(press_analysis, news_analysis)` 는
보도자료 + 뉴스를 합산하여 통합 제언을 생성한다.
"""

from __future__ import annotations

import json

from google import genai

from src.config import load_config


_RECOMMENDATION_PROMPT = """다음은 최근 수집·분석된 플랫폼 관련 정부 보도자료의 핵심 내용입니다.

{context}

위 내용을 종합하여 한국 디지털 플랫폼 정책 포럼에서 즉시 활용할 수 있는 정책 제언 3개를 도출하세요.
각 제언은 구체적이고 실행 가능한 내용이어야 하며, 보도자료에서 관찰된 실제 트렌드와 이슈를 근거로 해야 합니다.

다음 JSON 형식으로만 응답하세요 (다른 텍스트 없이):

{{
  "policy_recommendations": [
    {{
      "title": "제언 제목 (20자 이내)",
      "description": "구체적 제언 내용 (2~4문장, 현황·문제점·개선방향 포함)"
    }},
    {{
      "title": "제언 제목 2",
      "description": "제언 내용 2"
    }},
    {{
      "title": "제언 제목 3",
      "description": "제언 내용 3"
    }}
  ]
}}
"""


def _build_context(analyzed_articles: list[dict], max_articles: int = 30) -> str:
    """분석 완료 기사에서 종합 컨텍스트 텍스트를 구성한다."""
    analyzed = [
        a for a in analyzed_articles
        if a.get("status") == "analyzed" and a.get("summary")
    ]

    # 리스크 점수 내림차순으로 상위 max_articles건 선택
    analyzed.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
    top = analyzed[:max_articles]

    lines: list[str] = []
    for a in top:
        platforms = ", ".join(a.get("platforms", [])) or "해당없음"
        domains = ", ".join(a.get("policy_domains", [])) or "미분류"
        risk = a.get("risk_score", 0)
        keywords = ", ".join(a.get("keywords", []))
        summary = a.get("summary", "")
        lines.append(
            f"[리스크 {risk}] {a.get('title', '')} | 플랫폼: {platforms} | "
            f"정책영역: {domains} | 키워드: {keywords}\n요약: {summary}"
        )

    return "\n\n".join(lines)


def _parse_recommendations(text: str) -> list[dict]:
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("\n")
        text = "\n".join(parts[1:])
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    try:
        data = json.loads(text)
        recs = data.get("policy_recommendations", [])
        return [
            {"title": str(r.get("title", "")), "description": str(r.get("description", ""))}
            for r in recs
            if r.get("title") and r.get("description")
        ][:3]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


def generate_recommendations(
    press_analysis: dict,
    config: dict | None = None,
) -> list[dict]:
    """정책 제언 3개를 생성하여 반환한다.

    기존 제언이 있고 analyzed_count가 동일하면 재생성하지 않는다.
    """
    if config is None:
        config = load_config()

    articles = press_analysis.get("articles", [])
    analyzed_count = press_analysis.get("analyzed_count", 0)
    existing_recs = press_analysis.get("policy_recommendations", [])

    # 재생성 조건 확인
    prev_analyzed_count = press_analysis.get("_rec_analyzed_count")
    if existing_recs and prev_analyzed_count == analyzed_count:
        print(f"정책 제언 재사용 (analyzed_count={analyzed_count} 변동 없음)")
        return existing_recs

    if analyzed_count == 0:
        print("분석 완료 기사가 없어 정책 제언을 생성할 수 없습니다.")
        return []

    gemini_cfg = config.get("api", {}).get("gemini", {})
    api_key = gemini_cfg.get("api_key", "")
    model = gemini_cfg.get("model", "gemini-2.5-flash-lite")

    if not api_key or api_key.startswith("YOUR_"):
        print("Gemini API 키 미설정 — 정책 제언 생성 건너뜀")
        return existing_recs

    context = _build_context(articles)
    if not context:
        return existing_recs

    print("AI 정책 제언 생성 중...", end="", flush=True)

    client = genai.Client(api_key=api_key)
    prompt = _RECOMMENDATION_PROMPT.format(context=context)

    try:
        response = client.models.generate_content(model=model, contents=prompt)
        recs = _parse_recommendations(response.text)
        if recs:
            print(f" {len(recs)}개 생성 완료")
            return recs
        else:
            print(" 파싱 실패 — 기존 제언 유지")
            return existing_recs
    except Exception as e:
        print(f" 오류: {e} — 기존 제언 유지")
        return existing_recs


def generate_combined_recommendations(
    press_analysis: dict,
    news_analysis: dict,
    config: dict | None = None,
) -> list[dict]:
    """보도자료 + 뉴스 통합 정책 제언 3개를 생성하여 반환한다.

    재생성 조건: 이전 combined_recommendations.json의 source_counts와
    현재 analyzed_count 합계가 다를 때.

    반환: policy_recommendations 리스트 (caller가 파일 저장 담당)
    """
    if config is None:
        config = load_config()

    press_articles = press_analysis.get("articles", [])
    news_articles = news_analysis.get("articles", [])
    all_articles = press_articles + news_articles

    press_analyzed = press_analysis.get("analyzed_count", 0)
    news_analyzed = news_analysis.get("analyzed_count", 0)

    if press_analyzed + news_analyzed == 0:
        print("분석 완료 기사가 없어 통합 정책 제언을 생성할 수 없습니다.")
        return []

    gemini_cfg = config.get("api", {}).get("gemini", {})
    api_key = gemini_cfg.get("api_key", "")
    model = gemini_cfg.get("model", "gemini-2.5-flash-lite")

    if not api_key or api_key.startswith("YOUR_"):
        print("Gemini API 키 미설정 — 통합 정책 제언 생성 건너뜀")
        return []

    context = _build_context(all_articles)
    if not context:
        return []

    print(
        f"AI 통합 정책 제언 생성 중 (보도자료 {press_analyzed}건 + 뉴스 {news_analyzed}건)...",
        end="",
        flush=True,
    )

    client = genai.Client(api_key=api_key)
    prompt = _RECOMMENDATION_PROMPT.format(context=context)

    try:
        response = client.models.generate_content(model=model, contents=prompt)
        recs = _parse_recommendations(response.text)
        if recs:
            print(f" {len(recs)}개 생성 완료")
            return recs
        else:
            print(" 파싱 실패")
            return []
    except Exception as e:
        print(f" 오류: {e}")
        return []
