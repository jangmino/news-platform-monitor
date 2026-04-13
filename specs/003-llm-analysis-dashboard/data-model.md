# Data Model: Gemini LLM 분석 + 웹 대시보드

## 파일 구조

```
data/
├── raw/
│   └── rss/
│       └── press_data.json          # 입력 (spec-002 결과물, 읽기 전용)
└── analyzed/
    └── press_analysis.json          # 출력 (이번 spec에서 생성)
```

---

## press_analysis.json 스키마

```json
{
  "generated_at": "2026-04-12T10:00:00+09:00",
  "total_count": 120,
  "analyzed_count": 110,
  "articles": [ /* AnalyzedArticle 배열 */ ],
  "policy_recommendations": [ /* PolicyRecommendation 배열 */ ]
}
```

### AnalyzedArticle

기존 Article 필드(spec-001/002) + 분석 결과 필드 추가.

| 필드 | 타입 | 출처 | 설명 |
|------|------|------|------|
| `title` | str | press_data.json | 보도자료 제목 |
| `date` | str (ISO) | press_data.json | 게시일 |
| `link` | str | press_data.json | 원문 URL (중복 분석 방지 키) |
| `content` | str | press_data.json | 본문 텍스트 |
| `dept` | str | press_data.json | 담당 부처명 |
| `category` | str | press_data.json | RSS 카테고리 |
| `platforms` | list[str] | Gemini 분석 | 언급된 플랫폼명 (config.yaml 기준) |
| `policy_domains` | list[str] | Gemini 분석 | 정책영역 멀티라벨 (config.yaml 기준) |
| `risk_score` | int (0-100) | Gemini 분석 | 리스크 점수 |
| `keywords` | list[str] | Gemini 분석 | 핵심 키워드 (최대 5개) |
| `summary` | str | Gemini 분석 | 이슈 요약 (3문장 이내) |
| `sentiment` | str | Gemini 분석 | "긍정" / "부정" / "중립" |
| `confidence` | float (0-1) | Gemini 분석 | 분석 신뢰도 |
| `status` | str | 파이프라인 | "analyzed" / "failed" / "skipped" / "parse_error" |
| `raw_response` | str \| null | Gemini 응답 | parse_error 시 원본 응답 보존, 정상 시 null |

### PolicyRecommendation

| 필드 | 타입 | 설명 |
|------|------|------|
| `title` | str | 정책 제언 제목 (1줄) |
| `description` | str | 정책 제언 상세 설명 (2-4문장) |

---

## Gemini API 프롬프트 스키마

### 개별 기사 분석 (structured output)

**입력**: `title` + `content` (앞 2000자로 절단)

**요청 출력 형식** (JSON 모드):
```json
{
  "platforms": ["플랫폼명1", "플랫폼명2"],
  "policy_domains": ["정책영역1"],
  "risk_score": 75,
  "keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"],
  "summary": "3문장 이내 요약",
  "sentiment": "부정",
  "confidence": 0.85
}
```

### 전체 종합 제언 (structured output)

**입력**: 분석 완료 기사의 summary + keywords 집계 텍스트

**요청 출력 형식** (JSON 모드):
```json
{
  "policy_recommendations": [
    {"title": "제언 제목 1", "description": "제언 설명 1"},
    {"title": "제언 제목 2", "description": "제언 설명 2"},
    {"title": "제언 제목 3", "description": "제언 설명 3"}
  ]
}
```

---

## 대시보드 데이터 흐름

```
[Python: analyze-press]
        │
        ├─► data/analyzed/press_analysis.json       (canonical)
        │
        └─► dashboard/public/data/press_analysis.json  (shutil.copy2)
                    │
            [React: bun run dev]
            fetch('/data/press_analysis.json')       (Vite 정적 파일)
                    │
            useAnalysisData() hook
                    │
            dataUtils.ts (집계 함수)
                    │
        ┌───────────┼───────────┬───────────┐
        ▼           ▼           ▼           ▼
    섹션 1       섹션 2       섹션 3       섹션 4
  요약 카드     TrendChart   KeywordCloud  플랫폼 카드
  RiskHeatmap  BubbleChart  IssueTimeline 정책 제언 패널
  (HTML table)  (Recharts)  (shadcn Table) (shadcn Card)
```

### 상태 관리 (App.tsx)

```typescript
const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);

// RiskHeatmap 셀 클릭 → selectedPlatform 업데이트
// Section4Platforms가 selectedPlatform으로 카드 필터링
```

---

## status 값 정의

| 값 | 설명 |
|----|------|
| `analyzed` | Gemini API 분석 성공, 모든 필드 채워짐 |
| `failed` | API 호출 실패 (네트워크 오류, 할당량 초과 등) |
| `skipped` | content 50자 미만으로 분석 제외 |
| `parse_error` | API 응답이 기대 스키마와 불일치, `raw_response`에 원본 보존 |
