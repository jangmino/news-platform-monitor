"""보도자료 전용 Gemini 분석기.

press_data.json → press_analysis.json (embedded 분석 결과)
- 플랫폼 추출, 정책영역 분류, 리스크 점수, 키워드, 요약, 감성, 신뢰도
- 증분 분석: link 기준 기존 결과 재사용
- Atomic write: tmpfile → rename
- 완료 후 dashboard/public/data/ 에 복사
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path

from google import genai

from src.config import load_config
from src.utils.file_io import load_json, ensure_dir, raw_rss_dir, analyzed_dir


_MIN_CONTENT_LENGTH = 50  # 이 미만이면 skipped

_PROMPT = """다음 보도자료를 분석하세요. 반드시 원문에 있는 내용만 기반으로 하고, 원문에 없는 내용을 추가하지 마세요.

## 제목
{title}

## 본문
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
    """단일 보도자료를 분석하여 분석 필드를 반환한다."""
    all_platforms = ", ".join(valid_platforms)
    all_domains = ", ".join(valid_domains)

    prompt = _PROMPT.format(
        title=article.get("title", ""),
        content=article.get("content", "")[:2000],
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


def _atomic_write(data: dict, path: Path) -> None:
    """데이터를 tmpfile에 쓰고 rename하여 atomic하게 저장한다."""
    ensure_dir(path.parent)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _copy_to_dashboard(src: Path) -> None:
    """분석 결과를 dashboard/public/data/ 에 복사한다."""
    # cli.py 또는 __main__.py 기준으로 프로젝트 루트를 찾는다
    project_root = Path(__file__).resolve().parents[2]
    dst_dir = project_root / "dashboard" / "public" / "data"
    dst = dst_dir / "press_analysis.json"

    if not dst_dir.exists():
        return  # dashboard 프로젝트가 아직 초기화되지 않음

    try:
        shutil.copy2(src, dst)
    except OSError:
        pass  # dashboard 복사 실패는 파이프라인을 중단하지 않음


def run_press_analysis(config: dict | None = None, force: bool = False) -> dict:
    """보도자료 JSON을 Gemini API로 분석하고 결과를 저장한다.

    Returns:
        press_analysis dict (저장된 데이터와 동일)
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
    input_path = raw_rss_dir() / "press_data.json"
    articles: list[dict] = load_json(input_path)  # type: ignore
    if not articles:
        print("분석할 보도자료가 없습니다. 먼저 collect를 실행하세요.")
        return {}

    # 기존 분석 결과 로드 (증분 분석용)
    output_path = analyzed_dir() / "press_analysis.json"
    existing: dict = {}              # link → analyzed_article (캐시)
    existing_recs: list = []         # 이전 정책 제언 (재사용)
    existing_rec_count: int | None = None  # 제언 생성 시점의 analyzed_count
    if not force and output_path.exists():
        try:
            existing_data = json.loads(output_path.read_text(encoding="utf-8"))
            for a in existing_data.get("articles", []):
                # analyzed / skipped 만 캐시에 보존 — failed / parse_error 는 재시도
                if a.get("link") and a.get("status") in ("analyzed", "skipped"):
                    existing[a["link"]] = a
            existing_recs = existing_data.get("policy_recommendations", [])
            existing_rec_count = existing_data.get("_rec_analyzed_count")
        except (json.JSONDecodeError, KeyError):
            pass

    # Gemini 클라이언트
    client = genai.Client(api_key=api_key)

    analyzed_articles: list[dict] = []
    new_count = 0
    fail_count = 0
    skip_count = 0

    total = len(articles)
    print(f"보도자료 {total}건 중 분석 시작 (기존 캐시: {len(existing)}건)")

    for i, article in enumerate(articles, 1):
        link = article.get("link", "")

        # 증분: 이미 분석된 항목
        if link and link in existing and not force:
            analyzed_articles.append(existing[link])
            continue

        # 본문 길이 체크
        content = article.get("content", "")
        if len(content) < _MIN_CONTENT_LENGTH:
            result_article = {**article, "platforms": [], "policy_domains": [],
                              "risk_score": 0, "keywords": [], "summary": "",
                              "sentiment": "중립", "confidence": 0.0,
                              "status": "skipped", "raw_response": None}
            analyzed_articles.append(result_article)
            skip_count += 1
            continue

        title_preview = article.get("title", "")[:45]
        print(f"  [{i}/{total}] {title_preview}... ", end="", flush=True)

        try:
            analysis = _analyze_single(client, model, article, valid_platforms, valid_domains)
            result_article = {**article, **analysis}
            analyzed_articles.append(result_article)

            if analysis["status"] == "analyzed":
                new_count += 1
                print(f"완료 (risk={analysis['risk_score']}, platforms={analysis['platforms']})")
            else:
                fail_count += 1
                print("파싱 오류")

        except Exception as e:
            result_article = {**article, "platforms": [], "policy_domains": [],
                              "risk_score": 0, "keywords": [], "summary": "",
                              "sentiment": "중립", "confidence": 0.0,
                              "status": "failed", "raw_response": str(e)[:200]}
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
        "policy_recommendations": existing_recs,
    }
    if existing_rec_count is not None:
        output["_rec_analyzed_count"] = existing_rec_count

    # atomic write
    _atomic_write(output, output_path)
    print(f"\n분석 결과 저장: {output_path}")
    print(f"신규 분석 {new_count}건 | 실패 {fail_count}건 | 스킵 {skip_count}건 | 총 완료 {analyzed_count}건")

    # dashboard 복사
    _copy_to_dashboard(output_path)

    return output
