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
    run_preprocess()


def cmd_analyze(args):
    """LLM 분석 (요약, 감성, 정책 분류)."""
    from src.analyzers.gemini_analyzer import run_analysis
    print("=== LLM 분석 ===")
    run_analysis(force=args.force)


def cmd_score(args):
    """리스크 스코어링."""
    from src.scorers import run_scoring
    print("=== 리스크 스코어링 ===")
    run_scoring()


def cmd_report(args):
    """브리핑 리포트 생성."""
    from src.reporters import run_report
    print("=== 브리핑 리포트 생성 ===")
    run_report()


def cmd_analyze_press(args):
    """보도자료 전용 LLM 분석 + 정책 제언 생성."""
    from src.analyzers.press_analyzer import run_press_analysis
    from src.analyzers.recommendation_generator import generate_recommendations
    import json, os, tempfile
    from pathlib import Path

    print("=== 보도자료 LLM 분석 ===")
    result = run_press_analysis(force=args.force)
    if not result:
        return

    print("\n=== AI 정책 제언 생성 ===")
    recs = generate_recommendations(result)

    if recs:
        result["policy_recommendations"] = recs
        result["_rec_analyzed_count"] = result.get("analyzed_count", 0)

        # atomic write (재저장)
        from src.utils.file_io import analyzed_dir, ensure_dir
        output_path = analyzed_dir() / "press_analysis.json"
        ensure_dir(output_path.parent)
        fd, tmp_path = tempfile.mkstemp(dir=output_path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, output_path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

        # dashboard 복사
        project_root = Path(__file__).resolve().parents[1]
        dst = project_root / "dashboard" / "public" / "data" / "press_analysis.json"
        if dst.parent.exists():
            import shutil
            shutil.copy2(output_path, dst)
            print(f"대시보드 복사 완료: {dst}")

    analyzed = result.get("analyzed_count", 0)
    total = result.get("total_count", 0)
    print(f"\n완료: {analyzed}/{total}건 분석, 정책 제언 {len(recs)}개")


def cmd_run_all(args):
    """전체 파이프라인 실행."""
    print("========== 전체 파이프라인 실행 ==========\n")
    cmd_collect(argparse.Namespace(rss=False, news=False))
    cmd_preprocess(argparse.Namespace())
    cmd_analyze(argparse.Namespace(force=False))
    cmd_score(argparse.Namespace())
    cmd_report(argparse.Namespace())
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
    p_preprocess.set_defaults(func=cmd_preprocess)

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="LLM 분석")
    p_analyze.add_argument("--force", action="store_true", help="이미 분석된 항목도 재분석")
    p_analyze.set_defaults(func=cmd_analyze)

    # score
    p_score = subparsers.add_parser("score", help="리스크 스코어링")
    p_score.set_defaults(func=cmd_score)

    # report
    p_report = subparsers.add_parser("report", help="브리핑 리포트 생성")
    p_report.set_defaults(func=cmd_report)

    # run-all
    p_run_all = subparsers.add_parser("run-all", help="전체 파이프라인 실행")
    p_run_all.set_defaults(func=cmd_run_all)

    # analyze-press
    p_analyze_press = subparsers.add_parser("analyze-press", help="보도자료 LLM 분석 + 정책 제언 생성")
    p_analyze_press.add_argument("--force", action="store_true", help="이미 분석된 항목도 재분석")
    p_analyze_press.set_defaults(func=cmd_analyze_press)

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
