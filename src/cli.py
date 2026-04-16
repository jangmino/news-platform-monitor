"""CLI 진입점 — 파이프라인 단계별 명령어."""

import argparse
import sys


def cmd_collect(args):
    """데이터 수집 (RSS 보도자료 + Naver 뉴스)."""
    from src.collectors.rss_collector import collect_rss
    from src.collectors.news_collector import collect_news

    if args.rss or (not args.rss and not args.news):
        print("=== RSS 보도자료 수집 ===")
        collect_rss()

    if args.news or (not args.rss and not args.news):
        print("\n=== Naver 뉴스 수집 ===")
        collect_news()


def cmd_preprocess(args):
    """전처리 (중복 제거 + 태깅)."""
    from src.processors import run_preprocess
    print("=== 전처리 ===")
    run_preprocess(news_only=args.news_only)


def cmd_analyze(args):
    """보도자료(RSS) LLM 분석."""
    from src.analyzers.press_analyzer import run_press_analysis
    print("=== 보도자료 LLM 분석 ===")
    run_press_analysis(force=args.force)



def cmd_analyze_press(args):
    """보도자료 전용 LLM 분석 + 정책 제언 생성."""
    from src.analyzers.press_analyzer import run_press_analysis
    from src.analyzers.recommendation_generator import generate_recommendations
    from src.utils.file_io import analyzed_dir, atomic_write, copy_to_dashboard

    print("=== 보도자료 LLM 분석 ===")
    result = run_press_analysis(force=args.force)
    if not result:
        return

    print("\n=== AI 정책 제언 생성 ===")
    recs = generate_recommendations(result)

    if recs:
        result["policy_recommendations"] = recs
        result["_rec_analyzed_count"] = result.get("analyzed_count", 0)

        output_path = analyzed_dir() / "press_analysis.json"
        atomic_write(result, output_path)
        copy_to_dashboard(output_path, "press_analysis.json")

    analyzed = result.get("analyzed_count", 0)
    total = result.get("total_count", 0)
    print(f"\n완료: {analyzed}/{total}건 분석, 정책 제언 {len(recs)}개")


def cmd_analyze_news(args):
    """뉴스 전용 LLM 분석."""
    from src.analyzers.news_analyzer import run_news_analysis

    print("=== 뉴스 LLM 분석 ===")
    result = run_news_analysis(force=args.force)
    if not result:
        return

    analyzed = result.get("analyzed_count", 0)
    total = result.get("total_count", 0)
    print(f"\n완료: {analyzed}/{total}건 분석")


def cmd_generate_recommendations(args):
    """보도자료 + 뉴스 통합 정책 제언 생성."""
    from src.analyzers.recommendation_generator import generate_combined_recommendations
    from src.utils.file_io import analyzed_dir, atomic_write, copy_to_dashboard
    import json, datetime

    analyzed = analyzed_dir()
    press_path = analyzed / "press_analysis.json"
    news_path = analyzed / "news_analysis.json"

    if not press_path.exists():
        print("press_analysis.json 없음 — 먼저 analyze-press 를 실행하세요.")
        return

    with open(press_path, encoding="utf-8") as f:
        press_analysis = json.load(f)

    news_analysis: dict = {}
    if news_path.exists():
        with open(news_path, encoding="utf-8") as f:
            news_analysis = json.load(f)
    else:
        print("news_analysis.json 없음 — 보도자료만 사용하여 통합 제언 생성")

    press_analyzed = press_analysis.get("analyzed_count", 0)
    news_analyzed = news_analysis.get("analyzed_count", 0)

    # 재생성 조건 확인: 기존 combined_recommendations.json의 source_counts와 비교
    combined_path = analyzed / "combined_recommendations.json"
    if combined_path.exists() and not args.force:
        with open(combined_path, encoding="utf-8") as f:
            existing = json.load(f)
        existing_counts = existing.get("source_counts", {})
        if (
            existing_counts.get("press") == press_analyzed
            and existing_counts.get("news") == news_analyzed
            and existing.get("policy_recommendations")
        ):
            print(
                f"통합 제언 재사용 (보도자료 {press_analyzed}건 + 뉴스 {news_analyzed}건 변동 없음)"
            )
            return

    print("=== 통합 정책 제언 생성 ===")
    recs = generate_combined_recommendations(press_analysis, news_analysis)
    if not recs:
        print("정책 제언 생성 실패")
        return

    result = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_counts": {"press": press_analyzed, "news": news_analyzed},
        "policy_recommendations": recs,
    }

    atomic_write(result, combined_path)
    copy_to_dashboard(combined_path, "combined_recommendations.json")

    print(f"\n완료: 정책 제언 {len(recs)}개 (보도자료 {press_analyzed}건 + 뉴스 {news_analyzed}건 기반)")


def cmd_run_all(args):
    """전체 파이프라인 실행."""
    print("========== 전체 파이프라인 실행 ==========\n")
    cmd_collect(argparse.Namespace(rss=True, news=True))
    cmd_preprocess(argparse.Namespace(news_only=True))
    cmd_analyze(argparse.Namespace(force=False))
    cmd_analyze_news(argparse.Namespace(force=False))
    cmd_generate_recommendations(argparse.Namespace(force=False))
    print("\n========== 파이프라인 완료 ==========")


def cmd_status(args):
    """수집·분석 상태 요약."""
    from src.utils.file_io import (
        load_json, processed_dir, analyzed_dir, scored_dir, reports_dir,
        raw_rss_dir, raw_news_dir,
    )
    from pathlib import Path
    import glob

    # 수집 현황
    rss_files = list(raw_rss_dir().glob("*.json"))
    news_files = list(raw_news_dir().glob("*.json"))
    rss_count = sum(len(load_json(f)) for f in rss_files)
    news_count = sum(len(load_json(f)) for f in news_files)

    # 전처리
    processed_path = processed_dir() / "articles.json"
    processed_data = load_json(processed_path)
    processed_count = len(processed_data) if isinstance(processed_data, list) else 0

    # 분석
    analyses_path = analyzed_dir() / "analyses.json"
    analyses = load_json(analyses_path)
    analyses = analyses if isinstance(analyses, list) else []
    completed = sum(1 for a in analyses if a.get("status") == "completed")
    failed = sum(1 for a in analyses if a.get("status") == "failed")
    skipped = sum(1 for a in analyses if a.get("status") == "skipped")

    # 스코어링
    clusters_path = scored_dir() / "clusters.json"
    clusters = load_json(clusters_path)
    cluster_count = len(clusters) if isinstance(clusters, list) else 0

    # 리포트
    report_files = list(reports_dir().glob("briefing_*.md"))

    print("=== 시스템 상태 ===")
    print(f"수집: RSS {rss_count}건 ({len(rss_files)} 파일), 뉴스 {news_count}건 ({len(news_files)} 파일)")
    print(f"전처리: {processed_count}건 (중복 제거 후)")
    print(f"분석: 완료 {completed}건, 실패 {failed}건, 스킵 {skipped}건")
    print(f"클러스터: {cluster_count}개")
    print(f"리포트: {len(report_files)}개")
    if report_files:
        latest = sorted(report_files)[-1]
        print(f"최근 리포트: {latest.name}")


def main():
    parser = argparse.ArgumentParser(
        prog="python -m src.cli",
        description="플랫폼 산업 자동 모니터링 시스템",
    )
    subparsers = parser.add_subparsers(dest="command", help="실행할 명령")

    # collect
    p_collect = subparsers.add_parser("collect", help="데이터 수집")
    p_collect.add_argument("--rss", action="store_true", help="RSS 보도자료만 수집")
    p_collect.add_argument("--news", action="store_true", help="Naver 뉴스만 수집")
    p_collect.set_defaults(func=cmd_collect)

    # preprocess
    p_preprocess = subparsers.add_parser("preprocess", help="전처리")
    p_preprocess.add_argument("--all", dest="news_only", action="store_false", help="RSS 보도자료 + 뉴스 전체 전처리")
    p_preprocess.set_defaults(func=cmd_preprocess, news_only=True)

    # analyze-rss
    p_analyze = subparsers.add_parser("analyze-rss", help="보도자료(RSS) LLM 분석")
    p_analyze.add_argument("--force", action="store_true", help="이미 분석된 항목도 재분석")
    p_analyze.set_defaults(func=cmd_analyze)

    # run-all
    p_run_all = subparsers.add_parser("run-all", help="전체 파이프라인 실행")
    p_run_all.set_defaults(func=cmd_run_all)

    # analyze-press
    p_analyze_press = subparsers.add_parser("analyze-press", help="보도자료 LLM 분석 + 정책 제언 생성")
    p_analyze_press.add_argument("--force", action="store_true", help="이미 분석된 항목도 재분석")
    p_analyze_press.set_defaults(func=cmd_analyze_press)

    # analyze-news
    p_analyze_news = subparsers.add_parser("analyze-news", help="뉴스 LLM 분석")
    p_analyze_news.add_argument("--force", action="store_true", help="이미 분석된 항목도 재분석")
    p_analyze_news.set_defaults(func=cmd_analyze_news)

    # generate-recommendations
    p_gen_recs = subparsers.add_parser("generate-recommendations", help="보도자료 + 뉴스 통합 정책 제언 생성")
    p_gen_recs.add_argument("--force", action="store_true", help="이미 생성된 제언도 재생성")
    p_gen_recs.set_defaults(func=cmd_generate_recommendations)

    # status
    p_status = subparsers.add_parser("status", help="상태 확인")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
