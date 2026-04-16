# Data Model: LLM 분석 및 대시보드 뉴스 데이터 확장

## 파일 구조

```
data/
├── raw/
│   ├── rss/
│   │   └── press_data.json          # 입력 (spec-002 결과물, 읽기 전용)
│   └── news/
│       └── news_data.json           # 입력 (spec-001 결과물, 읽기 전용)
└── analyzed/
    ├── press_analysis.json          # 기존 (spec-003, 유지)
    ├── news_analysis.json           # 신규 (이번 spec)
    └── combined_recommendations.json  # 신규 (이번 spec)

dashboard/public/data/
├── press_analysis.json              # 자동 복사 (analyze-press 완료 시)
├── news_analysis.json               # 자동 복사 (analyze-news 완료 시) ← 신규
└── combined_recommendations.json    # 자동 복사 (generate-recommendations 완료 시) ← 신규
```

---

## news_analysis.json 스키마

```json
{
  "generated_at": "2026-04-16T10:00:00+09:00",
  "total_count": 120,
  "analyzed_count": 108,
  "articles": [ /* AnalyzedNewsArticle 배열 */ ]
}
```

### AnalyzedNewsArticle

news_data.json 원본 필드에 분석 결과 필드 추가.

| 필드 | 타입 | 출처 | 설명 |
|------|------|------|------|
| `title` | str | news_data.json | 뉴스 제목 (HTML 태그 제거됨) |
| `description` | str | news_data.json | 뉴스 패시지 (HTML 태그 제거됨) |
| `originallink` | str | news_data.json | 원문 URL (중복 판별 키) |
| `link` | str | news_data.json | 네이버 뉴스 URL |
| `published_at` | str (ISO) | news_data.json | 게시일 (정규화됨) |
| `source_name` | str | news_data.json | 언론사명 또는 "Naver 뉴스" |
| `source_type` | str | 파이프라인 | 항상 `"news"` |
| `query_used` | str | news_data.json | 수집 시 사용된 검색 쿼리 |
| `platform_tags` | list[str] | news_data.json | 수집 시 태깅된 플랫폼명 |
| `institution_tags` | list[str] | news_data.json | 수집 시 태깅된 기관명 |
| `platforms` | list[str] | Gemini 분석 | 언급된 플랫폼명 (config.yaml 기준) |
| `policy_domains` | list[str] | Gemini 분석 | 정책영역 멀티라벨 (config.yaml 기준) |
| `risk_score` | int (0-100) | Gemini 분석 | 리스크 점수 |
| `keywords` | list[str] | Gemini 분석 | 핵심 키워드 (최대 5개) |
| `summary` | str | Gemini 분석 | 이슈 요약 (3문장 이내) |
| `sentiment` | str | Gemini 분석 | "긍정" / "부정" / "중립" |
| `confidence` | float (0-1) | Gemini 분석 | 분석 신뢰도 |
| `status` | str | 파이프라인 | "analyzed" / "failed" / "skipped" / "parse_error" |
| `raw_response` | str \| null | Gemini 응답 | parse_error 시 원본 응답, 정상 시 null |

---

## press_analysis.json 변경 사항 (기존 spec-003 출력)

기존 AnalyzedPressArticle에 `source_type: "press"` 필드가 추가된다.  
신규 분석 항목부터 포함되며, 기존 저장 파일의 마이그레이션은 필요하지 않다.

---

## combined_recommendations.json 스키마

```json
{
  "generated_at": "2026-04-16T10:00:00+09:00",
  "source_counts": {
    "press": 95,
    "news": 108
  },
  "policy_recommendations": [
    { "title": "제언 제목 1", "description": "제언 설명 1" },
    { "title": "제언 제목 2", "description": "제언 설명 2" },
    { "title": "제언 제목 3", "description": "제언 설명 3" }
  ]
}
```

재생성 조건: 현재 `press_analyzed_count` 또는 `news_analyzed_count` 중 하나라도 `source_counts`와 달라진 경우.

---

## Gemini 분석 입력 (뉴스 기사)

**입력 텍스트**: `title + "\n" + description` (HTML 태그 제거 후, 최대 600자로 절단)

**프롬프트 구조**: `press_analyzer.py`의 `_PROMPT`와 동일한 출력 스키마, 단 입력 섹션명을 "기사 제목/요약"으로 변경

---

## 대시보드 타입 변경 (`dashboard/src/types/analysis.ts`)

### 신규 타입

```typescript
export type SourceFilter = "all" | "press" | "news";

export interface NewsAnalysis {
  generated_at: string;
  total_count: number;
  analyzed_count: number;
  articles: AnalyzedArticle[];
  // policy_recommendations 없음
}

export interface CombinedRecommendations {
  generated_at: string;
  source_counts: { press: number; news: number };
  policy_recommendations: PolicyRecommendation[];
}

export interface MediaOutletCount {
  domain: string;   // originallink 2단계 도메인
  count: number;
}
```

### 기존 타입 변경

```typescript
// AnalyzedArticle: source_type을 optional에서 required로 변경
source_type: "press" | "news";  // 기존: source_type?: string
```

---

## 대시보드 상태 흐름

```
useCombinedData()
    ├── fetch('/data/press_analysis.json')   → pressArticles: AnalyzedArticle[]
    ├── fetch('/data/news_analysis.json')    → newsArticles: AnalyzedArticle[]
    └── fetch('/data/combined_recommendations.json') → combinedRecs: PolicyRecommendation[]

App.tsx
    ├── selectedSource: SourceFilter = "all"
    ├── filteredArticles = useMemo([pressArticles, newsArticles, selectedSource])
    │   - "all":   [...pressArticles, ...newsArticles]
    │   - "press": pressArticles
    │   - "news":  newsArticles
    └── 모든 섹션에 filteredArticles 전달

Section1Overview.tsx
    ├── 기존 요약 카드 (filteredArticles 기반)
    ├── RiskHeatmap (filteredArticles 기반)
    └── [selectedSource === "news" 시만] MediaOutletPieChart

Section4Platforms.tsx
    ├── 플랫폼 카드 (filteredArticles 기반)
    │   └── 각 카드: source_type별 뱃지 표시
    └── 제언 패널
        ├── combinedRecs 있음 → combinedRecs 표시
        └── combinedRecs 없음 → pressAnalysis.policy_recommendations 표시
```

---

## 언론사 파이차트 데이터 계산

```
originallink 도메인 추출:
  "https://news.joins.com/article/123" → "joins.com"
  "https://www.hankyung.com/news/..." → "hankyung.com"

집계:
  상위 9개 도메인 + 나머지 "기타"로 묶어 10개 슬라이스 표시
```
