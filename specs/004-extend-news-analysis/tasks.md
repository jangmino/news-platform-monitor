# Tasks: LLM 분석 및 대시보드 뉴스 데이터 확장

**Input**: Design documents from `specs/004-extend-news-analysis/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 신규 파일 생성에 필요한 경로 및 환경 확인

- [X] T001 `dashboard/public/data/` 디렉토리에 `news_analysis.json`, `combined_recommendations.json` 플레이스홀더 파일(`{}`) 생성 — 대시보드 개발 중 fetch 404 방지

**Checkpoint**: 개발 환경 준비 완료

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Python과 대시보드 양쪽에서 공유하는 타입/유틸리티 기반 변경 — 이후 모든 User Story가 의존

**⚠️ CRITICAL**: 이 Phase가 완료되어야 US1(Python)과 US2(대시보드) 작업이 독립 병렬 진행 가능

- [X] T002 `dashboard/src/types/analysis.ts` 수정 — `AnalyzedArticle.source_type`을 `optional string`에서 `"press" | "news"` required로 변경, `SourceFilter`, `NewsAnalysis`, `CombinedRecommendations`, `MediaOutletCount` 타입 추가

- [X] T003 `dashboard/src/lib/dataUtils.ts` 수정 — `filterByDateRange`, `buildDailyTrend` 함수의 날짜 필드 처리 보완: `a.date`가 없으면 `a.published_at`을 fallback으로 사용 (뉴스 기사는 `published_at` 필드 사용, `AnalyzedArticle`에 `published_at?: string` 필드 추가 필요)

**Checkpoint**: Foundation ready — US1(Python 분석)과 US2(대시보드 연동) 병렬 시작 가능

---

## Phase 3: User Story 1 — 뉴스 기사 LLM 분석 실행 (Priority: P1) 🎯 MVP

**Goal**: `analyze-news` 커맨드로 뉴스 기사를 Gemini API로 분석하고 `news_analysis.json` 생성

**Independent Test**: `python -m src analyze-news` 실행 후 `data/analyzed/news_analysis.json`에 7개 분석 필드가 채워진 기사가 존재하고, `dashboard/public/data/news_analysis.json`에 자동 복사되었는지 확인

### Implementation for User Story 1

- [X] T004 [P] [US1] `src/analyzers/news_analyzer.py` 신규 작성 — `press_analyzer.py` 구조 기반으로 다음 변경 적용:
  - 입력: `raw_news_dir() / "news_data.json"`, 출력: `analyzed_dir() / "news_analysis.json"`
  - `_MIN_CONTENT_LENGTH = 30` (title+description 합산 기준)
  - 중복 키: `article.get("originallink") or article.get("link", "")`
  - 텍스트 준비: `re.sub(r"<[^>]+>", "", title + "\n" + description)[:600]` (HTML 태그 제거)
  - 결과에 `source_type: "news"` 추가
  - 출력 구조에 `policy_recommendations` 필드 없음
  - dashboard 복사 대상: `dashboard/public/data/news_analysis.json`
  - 공개 함수: `run_news_analysis(config=None, force=False) -> dict`

- [X] T005 [P] [US1] `src/analyzers/press_analyzer.py` 수정 — `_analyze_single()` 반환값과 `result_article` 구성 시 `"source_type": "press"` 필드 추가

- [X] T006 [US1] `src/cli.py` 수정 — `analyze-news` 서브커맨드 추가:
  ```python
  def cmd_analyze_news(args):
      from src.analyzers.news_analyzer import run_news_analysis
      print("=== 뉴스 LLM 분석 ===")
      run_news_analysis(force=args.force)
  ```
  `--force` 플래그 지원, `argparse` 등록 포함

**Checkpoint**: `python -m src analyze-news` 단독 실행 가능, `news_analysis.json` 생성 확인

---

## Phase 4: User Story 2 — 대시보드 보도자료·뉴스 통합 탐색 (Priority: P1)

**Goal**: 대시보드 소스 필터(전체/보도자료/뉴스)로 두 데이터소스를 통합·분리 탐색, 이슈 카드에 출처 뱃지 표시

**Independent Test**: `press_analysis.json`과 `news_analysis.json`이 모두 존재하는 상태에서 `bun run dev` 실행 후 소스 필터 전환 시 모든 섹션 데이터가 갱신되고, 섹션 4 카드에 "보도자료"/"뉴스" 뱃지가 표시되는지 확인

### Implementation for User Story 2

- [X] T007 [US2] `dashboard/src/hooks/useAnalysisData.ts` 전면 교체 — `Promise.allSettled`로 세 파일 병렬 로드:
  ```typescript
  // 반환 인터페이스
  interface CombinedDataResult {
    pressArticles: AnalyzedArticle[];    // press_analysis.json articles
    newsArticles: AnalyzedArticle[];     // news_analysis.json articles
    combinedRecs: PolicyRecommendation[]; // combined_recommendations.json
    pressRecs: PolicyRecommendation[];   // press_analysis.json policy_recommendations (fallback)
    isLoading: boolean;
    error: string | null;
  }
  ```
  - 각 파일 404/부재 시 빈 배열 처리 (오류 아님)
  - `pressArticles` 각 항목에 `source_type: "press"` 보정 (기존 저장 파일 호환)
  - `newsArticles` 각 항목에 `source_type: "news"` 보정

- [X] T008 [US2] `dashboard/src/App.tsx` 수정 — `selectedSource` 상태 + 소스 필터 UI + `filteredArticles` 파생:
  ```typescript
  const { pressArticles, newsArticles, combinedRecs, pressRecs, isLoading, error } = useAnalysisData();
  const [selectedSource, setSelectedSource] = useState<SourceFilter>("all");
  
  const filteredArticles = useMemo(() => {
    const base = selectedSource === "press" ? pressArticles
                : selectedSource === "news" ? newsArticles
                : [...pressArticles, ...newsArticles];
    return filterByDateRange(base, dateRange);
  }, [pressArticles, newsArticles, selectedSource, dateRange]);
  
  const activeRecs = combinedRecs.length > 0 ? combinedRecs : pressRecs;
  const totalCount = pressArticles.length + newsArticles.length;
  const analyzedCount = filteredArticles.filter(a => a.status === "analyzed").length;
  const isEmpty = totalCount === 0;
  const generatedAt = [press_generated_at, news_generated_at].filter(Boolean).sort().at(-1) ?? "";
  ```
  - 헤더에 소스 필터 버튼 그룹(전체/보도자료/뉴스) 추가 — 날짜 필터 왼쪽
  - 모든 섹션에 `articles={filteredArticles}` 전달
  - `Section1Overview`와 `Section4Platforms`의 `recommendations` prop을 `activeRecs`로 교체
  - `EmptyState`의 안내 커맨드에 `analyze-news` 추가

- [X] T009 [P] [US2] `dashboard/src/components/Section1Overview.tsx` 수정 — props에서 `articles: AnalyzedArticle[]`를 직접 받는 방식으로 이미 구현되어 있는지 확인 후 필요 시 `data.articles` 직접 참조 제거, `selectedSource` prop 수용 준비 (US4에서 사용)

- [X] T010 [P] [US2] `dashboard/src/components/Section2Trends.tsx` 수정 — `articles: AnalyzedArticle[]` prop을 이미 받고 있는지 확인. `buildDailyTrend`에서 날짜 필드 처리가 T003에서 수정된 버전 사용 여부 확인

- [X] T011 [P] [US2] `dashboard/src/components/Section3Keywords.tsx` 수정 — `articles: AnalyzedArticle[]` prop 방식 확인 및 T003 날짜 수정 반영 확인

- [X] T012 [US2] `dashboard/src/components/Section4Platforms.tsx` 수정 — 플랫폼 카드 렌더링 부분에 출처 뱃지 추가:
  ```tsx
  import { Badge } from "@/components/ui/badge";
  
  // 각 이슈 카드 내부 (article 단위 렌더링이 있는 경우) 또는
  // PlatformCard 집계 데이터 출력 시 source 혼합 표시 대신,
  // 섹션 4의 고위험 이슈 타임라인(IssueTimeline) 행에 뱃지 추가:
  <Badge variant={article.source_type === "press" ? "default" : "secondary"}>
    {article.source_type === "press" ? "보도자료" : "뉴스"}
  </Badge>
  ```
  - `IssueTimeline.tsx`도 `source_type` 뱃지 표시 필요 여부 확인 후 적용

**Checkpoint**: 소스 필터 전환 시 전체 섹션 갱신, 출처 뱃지 표시 확인

---

## Phase 5: User Story 3 — 통합 정책 제언 생성 (Priority: P2)

**Goal**: `generate-recommendations` 커맨드로 두 소스를 종합한 정책 제언 3개 생성, 대시보드 제언 패널에 반영

**Independent Test**: `python -m src generate-recommendations` 실행 후 `combined_recommendations.json`에 `source_counts`와 `policy_recommendations` 3개가 존재하고, 대시보드 섹션 4 제언 패널이 해당 내용을 표시하는지 확인

### Implementation for User Story 3

- [X] T013 [P] [US3] `src/analyzers/recommendation_generator.py` 수정 — `generate_combined_recommendations()` 함수 추가:
  ```python
  def generate_combined_recommendations(
      press_analysis: dict,
      news_analysis: dict,
      config: dict | None = None,
  ) -> dict:
      """두 소스를 종합한 정책 제언을 생성하고 반환한다."""
  ```
  - 두 파일의 분석 완료 기사를 합산하여 `_build_context()` 호출
  - 재생성 조건: `combined_recommendations.json`의 `source_counts`와 현재 analyzed_count가 다를 때
  - 반환 구조: `{"generated_at": ..., "source_counts": {"press": N, "news": M}, "policy_recommendations": [...]}`

- [X] T014 [US3] `src/cli.py` 수정 — `generate-recommendations` 서브커맨드 추가:
  ```python
  def cmd_generate_recommendations(args):
      """보도자료 + 뉴스 통합 정책 제언 생성."""
  ```
  - `press_analysis.json`, `news_analysis.json` 로드 (파일 없으면 `{}`)
  - `generate_combined_recommendations()` 호출
  - 결과를 `combined_recommendations.json`에 atomic write
  - `dashboard/public/data/combined_recommendations.json`으로 복사

- [X] T015 [US3] `dashboard/src/components/Section4Platforms.tsx` 수정 — 제언 패널 props 교체:
  - 기존 `recommendations: PolicyRecommendation[]` prop은 유지
  - `App.tsx`가 `activeRecs`(combined 우선, fallback press)를 전달하는 방식으로 이미 처리되므로 이 컴포넌트 자체는 변경 불필요할 수 있음 — 확인 후 필요 시 prop 이름만 정리

**Checkpoint**: `generate-recommendations` 단독 실행 → `combined_recommendations.json` 생성 → 대시보드 새로고침 시 통합 제언 표시

---

## Phase 6: User Story 4 — 뉴스 전용 언론사 시각화 (Priority: P3)

**Goal**: 소스 필터가 "뉴스"일 때 섹션 1에 언론사별 기사 수 파이차트 추가 표시

**Independent Test**: 대시보드 소스 필터를 "뉴스"로 설정 후 섹션 1 하단에 언론사별 파이차트가 렌더링되고, 필터를 "전체"/"보도자료"로 전환 시 사라지는지 확인

### Implementation for User Story 4

- [X] T016 [P] [US4] `dashboard/src/lib/dataUtils.ts` 수정 — `buildMediaOutletStats()` 함수 추가:
  ```typescript
  export function buildMediaOutletStats(
    articles: AnalyzedArticle[],
    topN = 9
  ): MediaOutletCount[] {
    // originallink에서 2단계 도메인 추출
    // 예: "https://news.joins.com/article/123" → "joins.com"
    // 상위 topN개 + 나머지 "기타"로 묶어 반환
  }
  ```

- [X] T017 [US4] `dashboard/src/components/Section1Overview.tsx` 수정 — `selectedSource` prop 추가 및 언론사 파이차트 조건부 렌더링:
  ```tsx
  // Section1Overview props에 selectedSource: SourceFilter 추가
  {selectedSource === "news" && newsArticles.length > 0 && (
    <MediaOutletPieChart articles={filteredArticles} />
  )}
  ```
  - `MediaOutletPieChart` 컴포넌트를 같은 파일 내부 또는 `charts/MediaOutletPieChart.tsx`로 구현
  - Recharts `PieChart` + `Pie` + `Cell` + `Tooltip` + `Legend` 사용
  - `buildMediaOutletStats()` 데이터를 입력으로 사용
  - `App.tsx`에서 `selectedSource` prop 전달 추가

**Checkpoint**: 뉴스 필터 → 언론사 파이차트 표시, 전체/보도자료 필터 → 파이차트 숨김

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 중복 코드 정리 및 통합 검증

- [X] T018 [P] `src/utils/file_io.py` 수정 — `atomic_write(data: dict, path: Path)` 공통 함수 추출 (`press_analyzer.py`와 `news_analyzer.py`가 공유):
  ```python
  def atomic_write(data: dict, path: Path) -> None:
      """tmpfile에 JSON을 쓰고 rename으로 원자적 저장."""
  ```
  - `press_analyzer.py`의 `_atomic_write` 로직 이동 후 두 analyzer에서 import

- [X] T019 [P] `src/utils/file_io.py` 수정 — `copy_to_dashboard(src: Path, filename: str)` 공통 함수 추출 (`press_analyzer.py`와 `news_analyzer.py`가 공유하는 dashboard 복사 로직)

- [ ] T020 `quickstart.md` 기준 수동 통합 검증: `analyze-news` → `analyze-press` → `generate-recommendations` → `bun run dev` 순서로 실행하여 대시보드 소스 필터, 출처 뱃지, 통합 제언, 언론사 파이차트 모두 정상 동작 확인

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational: types + dataUtils)
    ↓                              ↓
Phase 3 (US1: Python 분석)    Phase 4 (US2: 대시보드 통합)
    ↓                              ↓
Phase 5 (US3: 통합 제언)
    ↓
Phase 6 (US4: 언론사 차트)
    ↓
Phase 7 (Polish)
```

### User Story Dependencies

- **US1 (P1)**: Phase 2 완료 후 시작. US2와 독립 병렬 가능
- **US2 (P1)**: Phase 2 완료 후 시작. US1과 독립 병렬 가능. T007→T008 순서 필수
- **US3 (P2)**: US1(T004) 완료 후 시작. T013→T014→T015 순서 필수
- **US4 (P3)**: US2(T008) 완료 후 시작. T016→T017 순서 필수

### Within Each User Story

| Story | 내부 순서 |
|-------|----------|
| US1 | T004, T005 병렬 → T006 |
| US2 | T007 → T008 → T009, T010, T011 병렬 → T012 |
| US3 | T013 → T014 → T015 확인 |
| US4 | T016 → T017 |
| Polish | T018, T019 병렬 → T020 |

---

## Parallel Opportunities

### Phase 2

```
T002 (types 변경)  ||  T003 (dataUtils 날짜 처리)
```

### Phase 3 (US1)

```
T004 (news_analyzer.py)  ||  T005 (press_analyzer.py source_type)
→ T006 (cli.py analyze-news)
```

### Phase 4 (US2)

```
T007 (useAnalysisData 교체)
→ T008 (App.tsx)
→ T009 (Section1) || T010 (Section2) || T011 (Section3)
→ T012 (Section4 badge)
```

### Phase 7 (Polish)

```
T018 (atomic_write 추출)  ||  T019 (copy_to_dashboard 추출)
→ T020 (통합 검증)
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2만 완료)

1. Phase 1 Setup → Phase 2 Foundational
2. Phase 3 (US1: analyze-news 커맨드) — Python 분석
3. Phase 4 (US2: 대시보드 통합 + 소스 필터 + 출처 뱃지)
4. **STOP and VALIDATE**: 두 데이터소스가 통합 표시되는지 확인
5. 기본 기능 완성

### Incremental Delivery

1. Setup + Foundational → 기반 완성
2. US1 + US2 → 핵심 기능 (뉴스 분석 + 통합 탐색)
3. US3 → 통합 정책 제언 추가
4. US4 → 언론사 시각화 추가
5. Polish → 코드 정리 및 최종 검증

---

## Notes

- Python 신규 의존성 없음 (`google-genai` 기존 사용)
- 대시보드 신규 의존성 없음 (Recharts, shadcn/ui Badge 기존 사용)
- T004/T005는 서로 다른 파일 → 병렬 가능
- `dataUtils.ts`의 함수들은 이미 `AnalyzedArticle[]`를 받으므로 시그니처 변경 불필요
- 뉴스 기사의 날짜 필드 처리(T003)는 `filterByDateRange`와 `buildDailyTrend` 양쪽 모두 수정 필요
- `press_analyzer.py`의 `source_type` 추가(T005)는 기존 파일 재분석 없이 신규 분석분부터 적용
