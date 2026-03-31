# Implementation Plan: 플랫폼 산업 자동 모니터링 파이프라인

**Branch**: `001-platform-monitor-pipeline` | **Date**: 2026-03-31 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-platform-monitor-pipeline/spec.md`

## Summary

KISDI 디지털플랫폼 정책포럼을 위한 자동 모니터링 시스템. 정책브리핑 RSS 피드(7개 기관)와 Naver Search API를 통해 뉴스·보도자료를 수집하고, Google Gemini API로 요약·감성·정책영역 분류를 수행한 뒤, 리스크 스코어링 및 주간 브리핑 리포트를 자동 생성하는 CLI 기반 파이프라인.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: feedparser, requests, google-genai, pyyaml, matplotlib, seaborn
**Storage**: 로컬 파일 시스템 (JSON), 히트맵 이미지 (PNG)
**Testing**: pytest
**Target Platform**: Windows 10/11 (KISDI 랩탑), macOS/Linux 호환
**Project Type**: CLI 파이프라인 도구
**Performance Goals**: 전체 파이프라인 1회 실행 30분 이내
**Constraints**: Naver API 일일 25,000회, Gemini API 할당량, 외부 DB 없음
**Scale/Scope**: 일일 수집 기사 수백~수천 건, 단일 사용자

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Pipeline-First | PASS | 수집→전처리→분석→평가→리포트 5단계, 각 단계 독립 실행 가능 (FR-013) |
| II. Source Traceability | PASS | 모든 Article에 url 필수, 리포트에 source_links 포함 (FR-011, FR-012) |
| III. Human-in-the-Loop | PASS | risk_score >= 70 시 requires_review=true (FR-009), 신뢰도 점수 포함 (FR-007) |
| IV. Local-First | PASS | 로컬 파일 저장, CLI 실행, 외부 서비스는 API 호출만 (FR-014) |
| V. Simplicity | PASS | 의존성 6개, 파일 기반 저장, hwpx는 stdlib로 파싱 |
| VI. Policy-Domain | PASS | 7대 영역 enum, 멀티라벨 분류, 히트맵 매트릭스 (FR-006, FR-010) |

**Gate result**: ALL PASS — no violations

## Project Structure

### Documentation (this feature)

```text
specs/001-platform-monitor-pipeline/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: technology research
├── data-model.md        # Phase 1: data model
├── quickstart.md        # Phase 1: setup & usage guide
└── tasks.md             # Phase 2: task list (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── cli.py               # CLI 진입점 (argparse)
├── config.py            # 설정 로드 (config.yaml + 환경 변수)
├── collectors/
│   ├── __init__.py
│   ├── rss_collector.py      # RSS 피드 수집 (feedparser)
│   ├── news_collector.py     # Naver Search API 수집
│   └── hwpx_parser.py        # HWPX 텍스트 추출 (stdlib)
├── processors/
│   ├── __init__.py
│   ├── deduplicator.py       # URL 기반 중복 제거
│   └── tagger.py             # 플랫폼명/기관명 태깅
├── analyzers/
│   ├── __init__.py
│   └── gemini_analyzer.py    # Gemini API 분석 (요약, 감성, 정책 분류)
├── scorers/
│   ├── __init__.py
│   ├── risk_scorer.py        # 리스크 점수 산출
│   ├── trend_detector.py     # 급상승 이슈 탐지
│   └── clusterer.py          # 키워드 기반 이슈 클러스터링
├── reporters/
│   ├── __init__.py
│   ├── briefing_generator.py # 주간 브리핑 Markdown 생성
│   └── heatmap_generator.py  # 리스크 히트맵 PNG 생성
├── models/
│   ├── __init__.py
│   ├── article.py            # Article 데이터 클래스
│   ├── analysis.py           # Analysis 데이터 클래스
│   ├── cluster.py            # IssueCluster 데이터 클래스
│   └── report.py             # BriefingReport 데이터 클래스
└── utils/
    ├── __init__.py
    ├── file_io.py            # JSON 읽기/쓰기 유틸리티
    └── text_utils.py         # HTML 태그 제거, 텍스트 정규화

data/                          # 런타임 데이터 (gitignored)
├── raw/
│   ├── rss/                   # 기관별 보도자료 JSON
│   └── news/                  # Naver 뉴스 검색 결과 JSON
├── processed/
│   └── articles.json          # 중복 제거 후 통합
├── analyzed/
│   └── analyses.json          # LLM 분석 결과
├── scored/
│   └── clusters.json          # 이슈 클러스터 + 리스크 점수
└── reports/
    ├── briefing_YYYY-MM-DD.md
    ├── briefing_YYYY-MM-DD.json
    └── heatmap_YYYY-MM-DD.png

config.yaml                    # 설정 파일 (API 키, 키워드 목록, RSS URLs)
config.yaml.example            # 설정 파일 예시 (git 포함)
requirements.txt               # Python 의존성
```

**Structure Decision**: CLI 파이프라인 프로젝트 — 단일 프로젝트 구조. 파이프라인 5단계에 맞춰 `collectors/`, `processors/`, `analyzers/`, `scorers/`, `reporters/` 모듈로 분리. Constitution I 원칙(Pipeline-First)에 따라 각 단계를 독립 모듈로 구성.

## Complexity Tracking

> No Constitution Check violations — this section is not applicable.
