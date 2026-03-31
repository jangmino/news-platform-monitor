"""리포트 파이프라인 — 브리핑 + 히트맵 생성."""

from __future__ import annotations

from datetime import date

from src.config import load_config
from src.models.article import Article
from src.models.cluster import IssueCluster
from src.models.report import BriefingReport
from src.reporters.briefing_generator import generate_briefing
from src.reporters.heatmap_generator import (
    build_heatmap_data,
    generate_heatmap_image,
    generate_heatmap_markdown_table,
)
from src.utils.file_io import (
    load_json, save_json, save_text,
    processed_dir, scored_dir, reports_dir,
)


def _render_markdown(report: BriefingReport, heatmap_md: str) -> str:
    """BriefingReport를 Markdown으로 렌더링한다."""
    lines = [
        f"# 주간 이슈 브리핑",
        f"",
        f"**기간**: {report.period_start} ~ {report.period_end}",
        f"**생성일**: {report.generated_at[:10]}",
        f"",
        f"---",
        f"",
        f"## TOP {len(report.top_issues)} 이슈",
        f"",
    ]

    for issue in report.top_issues:
        review_flag = " [사람 확인 필요]" if issue.requires_review else ""
        lines.append(f"### {issue.rank}. {issue.title}{review_flag}")
        lines.append(f"")
        lines.append(f"**리스크 점수**: {issue.risk_score}")
        lines.append(f"")
        lines.append(f"{issue.summary}")
        lines.append(f"")

        if issue.policy_questions:
            lines.append(f"**정책 질문**:")
            for q in issue.policy_questions:
                lines.append(f"- {q}")
            lines.append(f"")

        if issue.source_links:
            lines.append(f"**근거 자료**:")
            for link in issue.source_links:
                lines.append(f"- {link}")
            lines.append(f"")

        lines.append(f"---")
        lines.append(f"")

    # 히트맵
    lines.append(f"## 리스크 히트맵 (플랫폼 x 정책영역)")
    lines.append(f"")
    lines.append(heatmap_md)
    lines.append(f"")

    if report.heatmap_image_path:
        lines.append(f"![히트맵]({report.heatmap_image_path})")
        lines.append(f"")

    return "\n".join(lines)


def run_report(config: dict | None = None) -> BriefingReport | None:
    """리포트 파이프라인: 브리핑 생성 + 히트맵 생성."""
    if config is None:
        config = load_config()

    # 데이터 로드
    articles_data = load_json(processed_dir() / "articles.json")
    clusters_data = load_json(scored_dir() / "clusters.json")

    if not clusters_data:
        print("리포트를 생성할 데이터가 없습니다. score를 먼저 실행하세요.")
        return None

    articles = [Article.from_dict(d) for d in articles_data]
    clusters = [IssueCluster.from_dict(d) for d in clusters_data]

    # 1. 브리핑 생성
    report = generate_briefing(clusters, articles, config)

    # 2. 히트맵 데이터 생성
    heatmap_data = build_heatmap_data(clusters)
    report.heatmap_data = heatmap_data

    # 3. 히트맵 이미지 생성
    today = date.today().isoformat()
    image_path = reports_dir() / f"heatmap_{today}.png"
    report.heatmap_image_path = generate_heatmap_image(heatmap_data, image_path)

    # 4. Markdown 테이블 생성
    heatmap_md = generate_heatmap_markdown_table(heatmap_data)

    # 5. Markdown 리포트 저장
    md_content = _render_markdown(report, heatmap_md)
    md_path = reports_dir() / f"briefing_{today}.md"
    save_text(md_content, md_path)
    print(f"  Markdown: {md_path} 저장")

    # 6. JSON 리포트 저장
    json_path = reports_dir() / f"briefing_{today}.json"
    save_json(report.to_dict(), json_path)
    print(f"  JSON: {json_path} 저장")

    print(f"\n리포트 생성 완료")
    return report
