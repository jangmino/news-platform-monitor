# Tasks: Gemini LLM 분석 + 웹 대시보드

## Phase 1: Python 분석 파이프라인 ✅

- [x] `data/analyzed/` 디렉토리 추가 (`.gitignore`에 `data/` 포함됨)
- [x] `src/analyzers/press_analyzer.py` 작성
  - [x] `press_data.json` 로드
  - [x] 기존 `press_analysis.json` 캐시 로드 (증분 분석)
  - [x] 개별 기사 분석: Gemini API 호출, JSON 응답 파싱
  - [x] `status` 처리: `analyzed` / `failed` / `skipped` / `parse_error`
  - [x] API 호출 간 1초 딜레이
  - [x] `data/analyzed/press_analysis.json` atomic write
  - [x] `dashboard/public/data/press_analysis.json` 복사
- [x] `src/analyzers/recommendation_generator.py` 작성
  - [x] 분석 완료 기사 집계 → 종합 컨텍스트 생성
  - [x] Gemini API로 정책 제언 3개 생성
  - [x] 재생성 조건 확인 (`analyzed_count` 변경 여부)
- [x] `src/cli.py`에 `analyze-press` 커맨드 + `--force` 옵션 추가
- [x] `.gitignore`에 `dashboard/node_modules/`, `dashboard/dist/`, `dashboard/public/data/press_analysis.json` 추가

## Phase 2: 대시보드 프로젝트 초기화 ✅

- [x] `dashboard/` 프로젝트 파일 수동 생성
  - `package.json`, `vite.config.ts`, `tsconfig*.json`
  - `tailwind.config.js`, `postcss.config.js`, `components.json`
  - `index.html`, `src/main.tsx`, `src/index.css`
- [x] `dashboard/public/data/` 디렉토리 + `.gitkeep` 생성

## Phase 3: 타입 + 데이터 레이어 ✅

- [x] `dashboard/src/types/analysis.ts`
- [x] `dashboard/src/hooks/useAnalysisData.ts`
- [x] `dashboard/src/lib/utils.ts` (shadcn cn 유틸)
- [x] `dashboard/src/lib/dataUtils.ts`
  - [x] `buildHeatmapMatrix()`
  - [x] `buildDailyTrend()`
  - [x] `buildKeywordFrequency()`
  - [x] `buildBubbleClusters()`
  - [x] `buildPlatformCards()`
  - [x] `getHighRiskIssues()`
  - [x] `riskToTailwindBg()`, `riskToTextColor()`, `DOMAIN_COLORS`

## Phase 4: 차트 컴포넌트 ✅

- [x] `dashboard/src/charts/RiskHeatmap.tsx` — HTML table + Tailwind 색상, 셀 클릭 콜백
- [x] `dashboard/src/charts/TrendChart.tsx` — Recharts `LineChart`
- [x] `dashboard/src/charts/BubbleChart.tsx` — Recharts `ScatterChart` (domain별 Scatter 분리)
- [x] `dashboard/src/charts/KeywordCloud.tsx` — `span` + 인라인 font-size
- [x] `dashboard/src/charts/IssueTimeline.tsx` — 테이블, 원문 링크

## Phase 5: shadcn/ui + 섹션 + App ✅

- [x] `dashboard/src/components/ui/card.tsx`
- [x] `dashboard/src/components/ui/badge.tsx`
- [x] `dashboard/src/components/Section1Overview.tsx` — 요약 카드 4개 + RiskHeatmap
- [x] `dashboard/src/components/Section2Trends.tsx` — TrendChart + BubbleChart
- [x] `dashboard/src/components/Section3Keywords.tsx` — KeywordCloud + IssueTimeline
- [x] `dashboard/src/components/Section4Platforms.tsx` — 플랫폼 카드 그리드 + AI 정책 제언 패널
- [x] `dashboard/src/App.tsx` — useAnalysisData, selectedPlatform, 4개 섹션 조합

## Phase 6: 검증 (사용자 실행 필요)

- [ ] `cd dashboard && bun install` 실행
- [ ] 보도자료 10건으로 `python -m src analyze-press` E2E 실행
- [ ] 증분 분석 검증 (재실행 시 API 호출 0건)
- [ ] `bun run dev` 후 `localhost:5173` 4개 섹션 렌더링 확인
- [ ] 히트맵 셀 클릭 → 섹션 4 필터링 동작 확인
- [ ] `press_analysis.json` 없을 때 빈 상태 UI 확인
- [ ] `bun run build` TypeScript 컴파일 오류 0건
