# Research: LLM 분석 및 대시보드 뉴스 데이터 확장

## 기존 코드베이스 분석

### Python 분석 파이프라인

**`src/analyzers/press_analyzer.py`** — 핵심 참조 파일

- Decision: `news_analyzer.py`는 `press_analyzer.py`의 구조를 그대로 따른다
- Rationale: 로직 흐름(증분 분석 → Gemini 호출 → atomic write → dashboard 복사)이 동일하며, 입력 필드와 최소 길이 기준만 달라진다
- Key differences:
  - 입력: `news_data.json`, 텍스트 = `title + description` (최대 600자)
  - 중복 키: `originallink` (없으면 `link` 대체)
  - 최소 길이: 30자 (`_MIN_CONTENT_LENGTH = 30`)
  - 출력: `news_analysis.json` (`policy_recommendations` 필드 없음)
  - dashboard 복사 대상: `news_analysis.json`

**`src/models/article.py`**

- `Article` 모델에 이미 `source_type`, `originallink`, `description` 필드가 존재한다
- `press_analyzer.py`는 현재 `source_type` 필드를 출력에 포함하지 않는다
- Decision: `press_analyzer.py`를 수정하여 `source_type: "press"` 필드를 결과에 추가한다 (기존 분석 파일 재실행 불필요 — 신규 분석분부터 포함)

**`src/analyzers/recommendation_generator.py`**

- Decision: 기존 `generate_recommendations()` 함수는 변경하지 않는다 (하위 호환)
- 새 함수 `generate_combined_recommendations(press_analysis, news_analysis, config)` 추가
  - 두 소스의 분석 완료 기사를 합산하여 컨텍스트 구성
  - `source_counts: {"press": N, "news": M}` 필드 포함한 결과를 `combined_recommendations.json`에 저장

**`src/cli.py`**

- Decision: 두 서브커맨드 추가: `analyze-news`, `generate-recommendations`
- `analyze-news`: `run_news_analysis()` + 완료 후 dashboard 복사
- `generate-recommendations`: 두 분석 파일 로드 → `generate_combined_recommendations()` → 저장 + dashboard 복사

### 뉴스 데이터 파일 구조

`news_collector.py`가 저장하는 `news_data.json`의 각 항목 필드:
- `title`, `description`, `originallink`, `link`, `pubDate` (Naver API 원본)
- `source_name`, `source_type: "news"`, `query_used`, `platform_tags`, `institution_tags`
- `published_at` (ISO 정규화), `collected_at`

### 대시보드 구조

**`dashboard/src/types/analysis.ts`**

- `AnalyzedArticle`에 이미 `source_type?: string` 필드 존재
- Decision: `source_type`을 optional에서 required로 변경, `"press" | "news"` 유니온 타입으로 강화
- 새 타입 추가:
  - `NewsAnalysis` (PressAnalysis와 유사, `policy_recommendations` 없음)
  - `CombinedRecommendations` (`source_counts`, `policy_recommendations` 포함)
  - `SourceFilter = "all" | "press" | "news"`
  - `MediaOutletCount = { domain: string; count: number }`

**`dashboard/src/hooks/useAnalysisData.ts`**

- Decision: 현재 파일을 `useCombinedData.ts`로 확장 대체
  - `Promise.allSettled`로 두 파일 병렬 fetch
  - 각 파일 부재(404) 시 빈 배열로 처리 (오류 아님)
  - `combined_recommendations.json`도 병렬 로드
  - 반환: `{ pressArticles, newsArticles, combinedRecs, isLoading, error }`

**`dashboard/src/App.tsx`**

- Decision: `selectedSource: SourceFilter` 상태 추가
- 소스 필터 UI: 탭 또는 버튼 그룹(전체 / 보도자료 / 뉴스)을 대시보드 최상단에 배치
- `filteredArticles` 파생: `selectedSource`에 따라 `pressArticles + newsArticles` 합산 또는 단일 배열 선택
- `filteredArticles`를 모든 섹션 컴포넌트에 전달 (기존 `data.articles` 대체)

**섹션별 변경**

| 파일 | 변경 내용 |
|------|---------|
| `Section4Platforms.tsx` | 이슈 카드에 출처 뱃지("보도자료"/"뉴스") 추가, 제언 패널이 `combinedRecs`를 우선 사용 |
| `Section1Overview.tsx` | `selectedSource === "news"` 시 언론사별 파이차트(Recharts PieChart) 렌더링 |
| `lib/dataUtils.ts` | `filteredArticles`를 받는 함수로 시그니처 변경 (기존 `PressAnalysis` → `AnalyzedArticle[]`) |

## 재생성 조건 (통합 제언)

- `combined_recommendations.json`의 `source_counts`가 현재 (`press_analyzed_count`, `news_analyzed_count`)와 일치하면 재생성 건너뜀
- 두 값 중 하나라도 달라지면 재생성

## 언론사 파이차트 구현

- `originallink` 도메인 추출: `new URL(originallink).hostname` → 2단계 도메인(예: `news.joins.com` → `joins.com`) 사용
- Recharts `PieChart` + `Pie` + `Tooltip` + `Legend`로 구현 (이미 Recharts 의존성 존재)
- 상위 10개 언론사만 표시, 나머지는 "기타"로 합산

## 출처 뱃지 구현

- shadcn `Badge` 컴포넌트 재사용 (이미 `dashboard/src/components/ui/badge.tsx` 존재)
- "보도자료": 파란색 variant, "뉴스": 초록색 variant
