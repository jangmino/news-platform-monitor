# Implementation Plan: LLM 분석 및 대시보드 뉴스 데이터 확장

**Branch**: `004-extend-news-analysis` | **Date**: 2026-04-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/004-extend-news-analysis/spec.md`

## Summary

보도자료 전용이었던 Gemini LLM 분석 파이프라인과 React 대시보드를 뉴스 데이터(`news_data.json`)까지 포함하도록 확장한다. Python 쪽은 `press_analyzer.py`를 템플릿으로 `news_analyzer.py`를 추가하고, 두 소스를 합산하는 `combined_recommendations.json`을 생성하는 커맨드를 추가한다. 대시보드는 두 분석 파일을 병렬 로드하고, 소스 필터(전체/보도자료/뉴스)로 모든 섹션을 동적 갱신한다.

## Technical Context

**Language/Version**: Python 3.10+ (백엔드), TypeScript / React 18 (대시보드)
**Primary Dependencies**: google-genai (기존), Recharts (기존), shadcn/ui Badge (기존)
**Storage**: 로컬 파일 시스템 (JSON) — 기존 방식 유지
**Testing**: 수동 실행 검증 (기존 프로젝트 방침)
**Target Platform**: Windows 10/11 (KISDI 랩탑), 로컬 실행
**Project Type**: CLI 파이프라인 + 로컬 웹 대시보드
**Performance Goals**: 대시보드 필터 전환 1초 이내 (클라이언트 사이드 필터링이므로 사실상 즉시)
**Constraints**: 서버 없음 — 정적 파일 기반. 기존 파이프라인 하위 호환 필수

## Constitution Check

| 원칙 | 상태 | 근거 |
|------|------|------|
| I. Pipeline-First | ✅ | `analyze-news`가 수집 → 분석 단계에 추가되며, 기존 흐름과 독립 |
| II. Source Traceability | ✅ | `originallink`를 중복 키 및 출처로 보존, `source_type` 뱃지로 시각화 |
| III. Human-in-the-Loop | ✅ | 뉴스도 동일한 `confidence` 점수와 `risk_score` 제공 |
| IV. Local-First | ✅ | 서버 추가 없음. 기존 파일 기반 방식 유지 |
| V. Simplicity | ✅ | 새 파일 3개(`news_analyzer.py`, 타입 확장, hook 확장)로 구현. 신규 의존성 없음 |
| VI. Policy-Domain | ✅ | config.yaml의 동일한 policy_domains 목록 사용 |

**→ 모든 Gate 통과**

## Project Structure

### Documentation (this feature)

```text
specs/004-extend-news-analysis/
├── plan.md              # 이 파일
├── research.md          # Phase 0 출력
├── data-model.md        # Phase 1 출력
├── quickstart.md        # Phase 1 출력
└── tasks.md             # /speckit.tasks 커맨드 출력 (미생성)
```

### Source Code (변경 대상)

```text
src/
├── analyzers/
│   ├── press_analyzer.py      # 수정: source_type:"press" 필드 추가
│   ├── news_analyzer.py       # 신규: 뉴스 전용 Gemini 분석기
│   └── recommendation_generator.py  # 수정: generate_combined_recommendations() 추가
└── cli.py                     # 수정: analyze-news, generate-recommendations 커맨드 추가

dashboard/src/
├── types/
│   └── analysis.ts            # 수정: SourceFilter, NewsAnalysis, CombinedRecommendations 추가
├── hooks/
│   └── useAnalysisData.ts     # 수정 → useCombinedData: 두 파일 병렬 로드
├── lib/
│   └── dataUtils.ts           # 수정: 함수 시그니처를 AnalyzedArticle[] 기반으로 변경
├── components/
│   ├── Section1Overview.tsx   # 수정: 언론사 파이차트 조건부 렌더링
│   └── Section4Platforms.tsx  # 수정: 출처 뱃지, 통합 제언 패널
└── App.tsx                    # 수정: selectedSource 상태, 소스 필터 UI, filteredArticles
```

## 변경 상세

### Phase A: Python 백엔드

#### A-1. `src/analyzers/news_analyzer.py` (신규)

`press_analyzer.py` 기반으로 다음만 변경:

```python
_MIN_CONTENT_LENGTH = 30  # title+description 합산 기준 (press: 50)

# 입력 파일
input_path = raw_news_dir() / "news_data.json"
output_path = analyzed_dir() / "news_analysis.json"

# 중복 판별 키: originallink (없으면 link 대체)
dedup_key = article.get("originallink") or article.get("link", "")

# 분석 입력 텍스트 구성 (HTML 태그 제거 포함)
import re
def _clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()

title = _clean_html(article.get("title", ""))
description = _clean_html(article.get("description", ""))
input_text = (title + "\n" + description)[:600]

# 결과에 source_type 추가
result_article = {**article, **analysis, "source_type": "news"}

# 출력에 policy_recommendations 없음
output: dict = {
    "generated_at": ...,
    "total_count": ...,
    "analyzed_count": ...,
    "articles": analyzed_articles,
    # policy_recommendations 없음
}

# dashboard 복사 대상
dashboard_dst = project_root / "dashboard" / "public" / "data" / "news_analysis.json"
```

프롬프트는 `press_analyzer.py`의 `_PROMPT`와 동일하되 섹션명만 변경:
```
## 기사 제목
{title}

## 기사 요약
{content}   ← title+description 합산 텍스트
```

#### A-2. `src/analyzers/press_analyzer.py` (수정)

단일 변경: 결과 article dict에 `"source_type": "press"` 추가.

```python
# _analyze_single 반환값에 추가
validated["source_type"] = "press"

# 또는 result_article 구성 시
result_article = {**article, **analysis, "source_type": "press"}
```

#### A-3. `src/analyzers/recommendation_generator.py` (수정)

기존 `generate_recommendations()` 함수는 변경하지 않는다.

신규 함수 추가:

```python
def generate_combined_recommendations(
    press_analysis: dict,
    news_analysis: dict,
    config: dict | None = None,
) -> dict:
    """보도자료 + 뉴스 분석 결과를 종합하여 통합 정책 제언을 생성한다.
    
    Returns:
        combined_recommendations dict (저장 전 반환)
    """
    press_articles = press_analysis.get("articles", [])
    news_articles = news_analysis.get("articles", [])
    all_articles = press_articles + news_articles
    
    press_count = sum(1 for a in press_articles if a.get("status") == "analyzed")
    news_count = sum(1 for a in news_articles if a.get("status") == "analyzed")
    source_counts = {"press": press_count, "news": news_count}
    
    # 재생성 조건 확인 (combined_recommendations.json 로드)
    # press_count + news_count가 모두 동일하면 재생성 안 함
    ...
    
    context = _build_context(all_articles)
    # Gemini 호출 → 기존 _parse_recommendations 재사용
    recs = _parse_recommendations(response.text)
    
    return {
        "generated_at": datetime.now().isoformat(),
        "source_counts": source_counts,
        "policy_recommendations": recs,
    }
```

#### A-4. `src/cli.py` (수정)

두 서브커맨드 추가:

```python
def cmd_analyze_news(args):
    """뉴스 전용 LLM 분석."""
    from src.analyzers.news_analyzer import run_news_analysis
    print("=== 뉴스 LLM 분석 ===")
    run_news_analysis(force=args.force)

def cmd_generate_recommendations(args):
    """보도자료 + 뉴스 통합 정책 제언 생성."""
    from src.analyzers.recommendation_generator import generate_combined_recommendations
    from src.utils.file_io import analyzed_dir, load_json
    import json, os, tempfile, shutil
    from pathlib import Path
    
    press_path = analyzed_dir() / "press_analysis.json"
    news_path = analyzed_dir() / "news_analysis.json"
    
    press_analysis = json.loads(press_path.read_text(encoding="utf-8")) if press_path.exists() else {}
    news_analysis = json.loads(news_path.read_text(encoding="utf-8")) if news_path.exists() else {}
    
    result = generate_combined_recommendations(press_analysis, news_analysis)
    
    output_path = analyzed_dir() / "combined_recommendations.json"
    # atomic write → dashboard 복사
    ...
```

### Phase B: 대시보드

#### B-1. `dashboard/src/types/analysis.ts` (수정)

```typescript
// 기존 수정
export type SourceFilter = "all" | "press" | "news";

export interface AnalyzedArticle {
  // ... 기존 필드 ...
  source_type: "press" | "news";  // optional → required
  // 뉴스 기사 추가 필드 (press는 undefined)
  originallink?: string;
  description?: string;
  published_at?: string;
}

// 신규 추가
export interface NewsAnalysis {
  generated_at: string;
  total_count: number;
  analyzed_count: number;
  articles: AnalyzedArticle[];
}

export interface CombinedRecommendations {
  generated_at: string;
  source_counts: { press: number; news: number };
  policy_recommendations: PolicyRecommendation[];
}

export interface MediaOutletCount {
  domain: string;
  count: number;
}
```

#### B-2. `dashboard/src/hooks/useAnalysisData.ts` (수정)

파일명 유지, 내용 전면 교체:

```typescript
export interface CombinedDataResult {
  pressArticles: AnalyzedArticle[];
  newsArticles: AnalyzedArticle[];
  combinedRecs: PolicyRecommendation[];
  pressRecs: PolicyRecommendation[];   // press_analysis의 기존 제언 (fallback용)
  isLoading: boolean;
  error: string | null;
}

export function useAnalysisData(): CombinedDataResult {
  // Promise.allSettled로 3개 파일 병렬 fetch
  // 404 → 빈 배열 (오류 아님)
  // pressArticles에 source_type:"press" 보정 (기존 파일 호환)
  // newsArticles에 source_type:"news" 보정
}
```

#### B-3. `dashboard/src/lib/dataUtils.ts` (수정)

모든 집계 함수가 `PressAnalysis` 대신 `AnalyzedArticle[]`를 받도록 시그니처 변경:

```typescript
// 변경 전
export function buildHeatmapData(data: PressAnalysis): HeatmapCell[]
// 변경 후
export function buildHeatmapData(articles: AnalyzedArticle[]): HeatmapCell[]
```

#### B-4. `dashboard/src/App.tsx` (수정)

```typescript
const { pressArticles, newsArticles, combinedRecs, pressRecs, isLoading, error } = useAnalysisData();
const [selectedSource, setSelectedSource] = useState<SourceFilter>("all");

const filteredArticles = useMemo(() => {
  if (selectedSource === "press") return pressArticles;
  if (selectedSource === "news") return newsArticles;
  return [...pressArticles, ...newsArticles];
}, [pressArticles, newsArticles, selectedSource]);

const activeRecs = combinedRecs.length > 0 ? combinedRecs : pressRecs;
```

소스 필터 UI (대시보드 헤더 하단):
```tsx
<div className="flex gap-2 mb-4">
  {(["all", "press", "news"] as SourceFilter[]).map((src) => (
    <button
      key={src}
      onClick={() => setSelectedSource(src)}
      className={selectedSource === src ? "bg-blue-600 text-white ..." : "..."}
    >
      {{ all: "전체", press: "보도자료", news: "뉴스" }[src]}
    </button>
  ))}
</div>
```

#### B-5. `dashboard/src/components/Section1Overview.tsx` (수정)

```tsx
// 기존 요약 카드 및 RiskHeatmap: filteredArticles 사용 (변경)
// 언론사 파이차트: news 필터 시에만 렌더링
{selectedSource === "news" && (
  <MediaOutletPieChart articles={filteredArticles} />
)}
```

`MediaOutletPieChart` 신규 컴포넌트 (`Section1Overview.tsx` 내부 또는 `charts/` 분리):
- `originallink` 도메인 추출 → 집계 → Recharts PieChart

#### B-6. `dashboard/src/components/Section4Platforms.tsx` (수정)

```tsx
// 플랫폼 카드에 출처 뱃지 추가
<Badge variant={article.source_type === "press" ? "default" : "secondary"}>
  {article.source_type === "press" ? "보도자료" : "뉴스"}
</Badge>

// 제언 패널: activeRecs prop으로 전달받아 표시
```

## Complexity Tracking

*Constitution Check 위반 없음. 이 섹션은 비워둠.*
