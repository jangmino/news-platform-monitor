# Implementation Plan: Gemini LLM 분석 + 웹 대시보드

## 기술 스택

| 영역 | 스택 |
|------|------|
| 분석 파이프라인 | Python 3.10+, 기존 프로젝트 구조 유지 |
| 대시보드 런타임 | Bun |
| 대시보드 빌드 | Vite + React + TypeScript |
| UI 컴포넌트 | shadcn/ui (Radix UI 기반) |
| 차트 | Recharts |
| 스타일 | Tailwind CSS (shadcn/ui 전제) |

---

## 데이터 브리지 설계

파이프라인과 대시보드는 완전히 분리된 프로세스이며, **JSON 파일**로만 연결된다.

```
[Python pipeline]                    [React dashboard]
analyze-press 실행
    │
    ├─► data/analyzed/press_analysis.json    (canonical, 파이프라인 소유)
    │
    └─► dashboard/public/data/press_analysis.json  (복사본, 대시보드용)
                                          │
                                   bun run dev
                                   Vite가 /data/*.json 을 정적으로 제공
                                          │
                                   fetch('/data/press_analysis.json')
```

- Python `analyze-press` 완료 시점에 `dashboard/public/data/` 에 자동 복사
- React 앱은 `fetch('/data/press_analysis.json')` 로 읽기 전용 접근
- 별도 백엔드 서버(FastAPI 등) 불필요

---

## 구현 순서

### Phase 1: Python 분석 파이프라인

**1. `src/analyzers/press_analyzer.py` 작성**
- `PressAnalyzer` 클래스 (기존 `gemini_analyzer.py` 활용)
- `analyze_article(article)` → Gemini API 호출, 결과 파싱
- 증분 분석: `link` 기준으로 기존 `press_analysis.json` 캐시 확인
- `status` 처리: `analyzed` / `failed` / `skipped` / `parse_error`
- API 호출 간 1초 딜레이

**2. `src/analyzers/recommendation_generator.py` 작성**
- 분석 완료 기사 요약 집계 → Gemini 종합 제언 3개 생성
- 재생성 조건: `analyzed_count`가 이전 생성 시점과 다를 때만

**3. `src/cli.py`에 `analyze-press` 커맨드 추가**
- `data/raw/rss/press_data.json` 로드 → 분석 실행 → 제언 생성
- 완료 시 `data/analyzed/press_analysis.json` atomic write
- 완료 시 `dashboard/public/data/press_analysis.json` 복사

---

### Phase 2: React 대시보드 프로젝트 초기화

**4. `dashboard/` 초기화**
```bash
cd news-platform-monitor
bun create vite dashboard --template react-ts
cd dashboard && bun install
bunx --bun shadcn@latest init       # shadcn/ui 초기화 (Tailwind 포함)
bun add recharts
bun add -d @types/recharts
```

**5. `dashboard/public/data/` 디렉토리 생성**
- `.gitkeep` 추가 (press_analysis.json은 .gitignore)

**6. 타입 정의 `dashboard/src/types/analysis.ts`**
```typescript
export interface AnalyzedArticle {
  title: string;
  date: string;
  link: string;
  content: string;
  dept: string;
  category: string;
  platforms: string[];
  policy_domains: string[];
  risk_score: number;       // 0-100
  keywords: string[];       // 최대 5개
  summary: string;
  sentiment: '긍정' | '부정' | '중립';
  confidence: number;       // 0-1
  status: 'analyzed' | 'failed' | 'skipped' | 'parse_error';
  raw_response: string | null;
}

export interface PolicyRecommendation {
  title: string;
  description: string;
}

export interface PressAnalysis {
  generated_at: string;
  total_count: number;
  analyzed_count: number;
  articles: AnalyzedArticle[];
  policy_recommendations: PolicyRecommendation[];
}
```

---

### Phase 3: 데이터 레이어

**7. `dashboard/src/hooks/useAnalysisData.ts`**
- `fetch('/data/press_analysis.json')` 호출
- 로딩/에러/빈 데이터 상태 처리
- 반환: `{ data, isLoading, error }`

**8. `dashboard/src/lib/dataUtils.ts`** — 집계 함수들
- `buildHeatmapMatrix(articles)` → 플랫폼 × 정책영역 평균 risk_score 2D 배열
- `buildDailyTrend(articles)` → `{ date, count }[]`
- `buildKeywordFrequency(articles)` → `{ keyword, count }[]`
- `buildBubbleClusters(articles)` → 키워드별 클러스터 (date, avgRisk, count, domain)
- `buildPlatformCards(articles)` → 플랫폼별 집계 (articleCount, maxRisk, topKeywords, sampleSummary)
- `getHighRiskIssues(articles, threshold)` → risk_score ≥ threshold, 내림차순 정렬

---

### Phase 4: 차트 컴포넌트

**9. `dashboard/src/charts/RiskHeatmap.tsx`**
- Recharts `ResponsiveContainer` + 커스텀 SVG 셀 렌더링
- 또는 HTML `<table>` + Tailwind 배경색 (색상 강도 = risk_score)
- 셀 클릭 → `onPlatformSelect(platform)` 콜백

> **비고**: Recharts는 히트맵을 네이티브 지원하지 않는다. `ScatterChart`를 축 기반으로 사용하거나, 순수 HTML 테이블 + Tailwind로 구현한다. 후자가 렌더링이 명확하고 클릭 이벤트 처리도 단순하다. → **HTML 테이블 + Tailwind 색상 강도** 방식 채택.

**10. `dashboard/src/charts/TrendChart.tsx`**
- Recharts `LineChart` + `XAxis(date)` + `YAxis(count)`

**11. `dashboard/src/charts/BubbleChart.tsx`**
- Recharts `ScatterChart`: x=날짜(시간축), y=평균 risk_score, size=기사 수, fill=정책영역 색상

**12. `dashboard/src/charts/KeywordCloud.tsx`**
- Recharts 미사용 — 순수 React/Tailwind
- `span` + `font-size` 인라인 스타일 (빈도 → 12px~36px 선형 매핑)

**13. `dashboard/src/charts/IssueTimeline.tsx`**
- shadcn/ui `Table` 컴포넌트
- 컬럼: 날짜 | 제목 | 리스크 점수 | 감성 | 정책영역
- risk_score 기준 내림차순, 상위 20건

---

### Phase 5: 섹션 레이아웃 + 앱 조합

**14. 섹션 컴포넌트 4개**
- `Section1Overview.tsx`: 요약 카드 4개(shadcn `Card`) + `RiskHeatmap`
- `Section2Trends.tsx`: `TrendChart` + `BubbleChart`
- `Section3Keywords.tsx`: `KeywordCloud` + `IssueTimeline`
- `Section4Platforms.tsx`: 플랫폼 카드 그리드 + AI 정책 제언 패널

**15. `dashboard/src/App.tsx`**
- `useAnalysisData()` 훅으로 데이터 로드
- `selectedPlatform` 상태 관리 (`RiskHeatmap` 셀 클릭 → `Section4` 필터링)
- 빈 데이터 / 로딩 / 에러 상태 UI

---

## 프로젝트 파일 구조 (전체)

```
news-platform-monitor/
├── src/                              # Python 파이프라인 (기존)
│   ├── analyzers/
│   │   ├── gemini_analyzer.py        # 기존
│   │   ├── press_analyzer.py         # 신규
│   │   └── recommendation_generator.py  # 신규
│   └── cli.py                        # 수정
├── data/
│   ├── raw/rss/press_data.json       # 기존
│   └── analyzed/
│       └── press_analysis.json       # 신규 (canonical)
├── dashboard/                        # React 대시보드 (신규)
│   ├── public/
│   │   └── data/
│   │       └── press_analysis.json   # Python이 복사 (gitignore)
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                   # shadcn/ui 자동 생성
│   │   │   ├── Section1Overview.tsx
│   │   │   ├── Section2Trends.tsx
│   │   │   ├── Section3Keywords.tsx
│   │   │   └── Section4Platforms.tsx
│   │   ├── charts/
│   │   │   ├── RiskHeatmap.tsx
│   │   │   ├── TrendChart.tsx
│   │   │   ├── BubbleChart.tsx
│   │   │   ├── KeywordCloud.tsx
│   │   │   └── IssueTimeline.tsx
│   │   ├── hooks/
│   │   │   └── useAnalysisData.ts
│   │   ├── types/
│   │   │   └── analysis.ts
│   │   ├── lib/
│   │   │   └── dataUtils.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── components.json               # shadcn/ui 설정
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
└── requirements.txt                  # Python 의존성 (변경 없음)
```

---

## 기술 결정사항

| 항목 | 결정 | 이유 |
|------|------|------|
| 대시보드 런타임 | Bun | 빠른 install/dev, Vite와 완벽 호환 |
| UI 컴포넌트 | shadcn/ui | 커스터마이즈 가능한 Radix 기반, Tailwind 통합 |
| 차트 라이브러리 | Recharts | React 친화적 SVG 기반, TypeScript 지원, 번들 크기 적정 |
| 히트맵 구현 | HTML table + Tailwind 색상 강도 | Recharts 네이티브 히트맵 없음, 구현 단순성 우선 |
| 키워드 클라우드 | span + 인라인 font-size | 한글 폰트 이슈 없음, 외부 라이브러리 불필요 |
| 데이터 연결 | Python → `dashboard/public/data/` 복사 | 백엔드 서버 불필요, 완전한 파이프라인-대시보드 분리 |
| 이슈 클러스터링 | 키워드 공유 기반 단순 그룹핑 | 고도화는 추후 spec |
| Python atomic write | tmpfile → rename | 복사 중 React fetch 충돌 방지 |
| 상태관리 | React useState (App.tsx) | 필터 상태 1개 (`selectedPlatform`), Context 불필요 |
