# news-platform-monitor Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-16

## Active Technologies
- Python 3.10+ + feedparser, requests, beautifulsoup4 (신규), pymupdf (신규), odfpy (신규), pyyaml (기존 유지) (002-integrate-press-data)
- 로컬 파일 시스템 (JSON) — 기존 방식 유지 (002-integrate-press-data)
- Python 3.10+ (백엔드), TypeScript / React 18 (대시보드) + google-genai (기존), Recharts (기존), shadcn/ui Badge (기존) (004-extend-news-analysis)

- Python 3.10+ + feedparser, requests, google-genai, pyyaml, matplotlib, seaborn (001-platform-monitor-pipeline)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.10+: Follow standard conventions

## Recent Changes
- 004-extend-news-analysis: Added Python 3.10+ (백엔드), TypeScript / React 18 (대시보드) + google-genai (기존), Recharts (기존), shadcn/ui Badge (기존)
- 002-integrate-press-data: Added Python 3.10+ + feedparser, requests, beautifulsoup4 (신규), pymupdf (신규), odfpy (신규), pyyaml (기존 유지)

- 001-platform-monitor-pipeline: Added Python 3.10+ + feedparser, requests, google-genai, pyyaml, matplotlib, seaborn

<!-- MANUAL ADDITIONS START -->
## spec-003: LLM 분석 + 대시보드 (003-llm-analysis-dashboard)

**분석 파이프라인** (Python, 기존 구조 유지)
- `src/analyzers/press_analyzer.py` — Gemini API 기반 보도자료 분석
- `src/analyzers/recommendation_generator.py` — 정책 제언 생성
- `python -m src analyze-press` 로 실행
- 출력: `data/analyzed/press_analysis.json` (canonical) + `dashboard/public/data/press_analysis.json` (복사)

**웹 대시보드** (`dashboard/` 디렉토리, 완전히 분리된 프로젝트)
- Bun + Vite + React + TypeScript + shadcn/ui + Recharts
- `cd dashboard && bun run dev` 로 실행 (포트 5173)
- `fetch('/data/press_analysis.json')` 으로 분석 결과 읽기 전용 접근
- 히트맵: HTML table + Tailwind (Recharts 네이티브 히트맵 없음)
- 키워드 클라우드: span + 인라인 font-size (외부 라이브러리 없음)
<!-- MANUAL ADDITIONS END -->
