"""주간 브리핑 생성기."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from src.config import load_config
from src.models.article import Article
from src.models.cluster import IssueCluster
from src.models.report import BriefingReport, TopIssue
from src.utils.text_utils import generate_id


def _generate_policy_questions(cluster: IssueCluster, client=None, model: str = "") -> list[str]:
    """정책 질문을 자동 도출한다. Gemini API가 있으면 활용, 없으면 규칙 기반."""
    if client and model:
        try:
            prompt = (
                f"다음 이슈에 대해 정책 포럼에서 논의할 만한 질문을 1~2개 도출하세요.\n"
                f"이슈 키워드: {', '.join(cluster.representative_keywords)}\n"
                f"정책 영역: {', '.join(cluster.policy_domains)}\n"
                f"관련 기사 수: {cluster.article_count}건\n"
                f"감성: {cluster.dominant_sentiment}\n\n"
                f"질문만 JSON 배열로 응답하세요: [\"질문1\", \"질문2\"]"
            )
            response = client.models.generate_content(model=model, contents=prompt)
            text = response.text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:])
                if text.endswith("```"):
                    text = text[:-3]
            questions = json.loads(text.strip())
            if isinstance(questions, list):
                return questions[:2]
        except Exception:
            pass

    # 규칙 기반 폴백
    questions = []
    domains = cluster.policy_domains
    keywords = cluster.representative_keywords

    if domains:
        questions.append(
            f"'{keywords[0]}' 관련 {', '.join(domains[:2])} 영역에서 "
            f"현행 규제 체계의 적정성은?"
        )
    if cluster.requires_review:
        questions.append(
            f"리스크 점수 {cluster.risk_score}점으로 평가된 "
            f"'{keywords[0]}' 이슈에 대한 선제적 정책 대응 방안은?"
        )

    return questions[:2]


def generate_briefing(
    clusters: list[IssueCluster],
    articles: list[Article],
    config: dict | None = None,
) -> BriefingReport:
    """TOP 10 이슈 브리핑을 생성한다."""
    if config is None:
        config = load_config()

    # Gemini 클라이언트 (선택적)
    client = None
    model = ""
    gemini_config = config.get("api", {}).get("gemini", {})
    api_key = gemini_config.get("api_key", "")
    if api_key and "YOUR_" not in api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            model = gemini_config.get("model", "gemini-2.5-flash-lite")
        except Exception:
            pass

    article_map = {a.id: a for a in articles}

    # 리스크 점수 상위 10개
    sorted_clusters = sorted(clusters, key=lambda c: c.risk_score, reverse=True)
    top_clusters = sorted_clusters[:10]

    today = date.today()
    period_start = (today - timedelta(days=7)).isoformat()
    period_end = today.isoformat()

    top_issues = []
    for rank, cluster in enumerate(top_clusters, 1):
        # 원문 링크 수집
        source_links = []
        for aid in cluster.article_ids[:5]:  # 상위 5개 링크
            art = article_map.get(aid)
            if art:
                source_links.append(art.url)

        # 이슈 제목 (대표 키워드 기반)
        title = " · ".join(cluster.representative_keywords[:3])

        # 요약 (클러스터 내 기사 수 + 감성 + 영역)
        summary = (
            f"{cluster.article_count}건의 관련 기사. "
            f"주요 감성: {cluster.dominant_sentiment}. "
            f"관련 정책영역: {', '.join(cluster.policy_domains) or 'N/A'}."
        )

        # 정책 질문
        questions = _generate_policy_questions(cluster, client, model)

        issue = TopIssue(
            rank=rank,
            cluster_id=cluster.cluster_id,
            title=title,
            summary=summary,
            source_links=source_links,
            policy_questions=questions,
            risk_score=cluster.risk_score,
            requires_review=cluster.requires_review,
        )
        top_issues.append(issue)

    report = BriefingReport(
        report_id=generate_id(f"briefing_{today.isoformat()}"),
        period_start=period_start,
        period_end=period_end,
        top_issues=top_issues,
    )

    print(f"  브리핑: TOP {len(top_issues)} 이슈 생성")
    return report
