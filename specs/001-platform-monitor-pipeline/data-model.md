# Data Model: 플랫폼 산업 자동 모니터링 파이프라인

**Date**: 2026-03-31
**Feature**: 001-platform-monitor-pipeline

## Entities

### Article (기사/보도자료)

수집된 개별 뉴스 기사 또는 보도자료.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| id | string | 고유 식별자 (URL의 해시값) | Y |
| title | string | 기사/보도자료 제목 | Y |
| content | string | 본문 텍스트 (hwpx 추출 포함) | Y |
| url | string | 원문 URL (중복 판별 기준) | Y |
| source_type | enum | "rss" \| "naver_api" | Y |
| source_name | string | 출처 기관명 (e.g., "공정거래위원회") | Y |
| published_at | datetime | 기사 게시일 | Y |
| collected_at | datetime | 수집 시각 | Y |
| search_keywords | list[string] | 수집 시 사용된 검색 키워드 목록 | N |
| platform_tags | list[string] | 본문에서 탐지된 플랫폼명 | N |
| institution_tags | list[string] | 본문에서 탐지된 기관명 | N |
| file_info | object \| null | 첨부파일 정보 (name, url, parse_status) | N |

**Uniqueness**: `url` 필드 기준
**Storage**: `data/raw/rss/*.json`, `data/raw/news/*.json`
**Merged storage**: `data/processed/articles.json` (중복 제거 후 통합)

---

### Analysis (분석 결과)

기사에 대한 LLM 분석 결과. Article과 1:1 관계.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| article_id | string | 연관된 Article의 id | Y |
| summary | string | 한국어 요약 (3문장 이내) | Y |
| keywords | list[string] | 핵심 키워드 (최대 5개) | Y |
| sentiment | enum | "positive" \| "negative" \| "neutral" | Y |
| sentiment_confidence | float | 감성 분석 신뢰도 (0.0~1.0) | Y |
| policy_domains | list[string] | 정책영역 멀티라벨 태그 | Y |
| policy_confidence | float | 정책 분류 신뢰도 (0.0~1.0) | Y |
| analyzed_at | datetime | 분석 시각 | Y |
| model_used | string | 사용된 LLM 모델명 | Y |
| status | enum | "completed" \| "failed" \| "skipped" | Y |
| error_message | string \| null | 분석 실패 시 오류 메시지 | N |

**Policy domains (enum)**: `공정거래`, `소비자보호`, `개인정보`, `노동`, `콘텐츠/저작권`, `안전`, `AI/자동화`
**Storage**: `data/analyzed/analyses.json`

---

### IssueCluster (이슈 클러스터)

LLM 추출 키워드 기반으로 유사 기사를 그룹화한 이슈 단위.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| cluster_id | string | 고유 식별자 | Y |
| representative_keywords | list[string] | 클러스터 대표 키워드 | Y |
| article_ids | list[string] | 소속 기사 ID 목록 | Y |
| article_count | int | 소속 기사 수 | Y |
| risk_score | float | 리스크 점수 (0~100) | Y |
| is_trending | bool | 급상승 이슈 여부 | Y |
| trending_reason | string \| null | 급상승 판별 근거 | N |
| requires_review | bool | 사람 확인 필요 여부 | Y |
| dominant_sentiment | enum | 클러스터 내 지배적 감성 | Y |
| policy_domains | list[string] | 클러스터 관련 정책영역 | Y |
| platform_tags | list[string] | 클러스터 관련 플랫폼명 | Y |
| created_at | datetime | 클러스터 생성 시각 | Y |

**Trending criteria**:
- 언급량 전주 대비 200% 이상 증가
- 규제기관 동반 언급
- 감성 급변 (긍정→부정 전환)

**Review trigger**: `risk_score >= 70`
**Storage**: `data/scored/clusters.json`

---

### BriefingReport (브리핑 리포트)

주간 단위 자동 생성 리포트.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| report_id | string | 고유 식별자 | Y |
| generated_at | datetime | 리포트 생성 시각 | Y |
| period_start | date | 리포트 대상 기간 시작 | Y |
| period_end | date | 리포트 대상 기간 끝 | Y |
| top_issues | list[TopIssue] | TOP 10 이슈 목록 | Y |
| heatmap_data | dict | 플랫폼 x 정책영역 매트릭스 | Y |
| heatmap_image_path | string | 히트맵 PNG 파일 경로 | Y |

**TopIssue structure**:
| Field | Type | Description |
|-------|------|-------------|
| rank | int | 순위 (1~10) |
| cluster_id | string | 관련 IssueCluster ID |
| title | string | 이슈 제목 |
| summary | string | 이슈 요약 |
| source_links | list[string] | 근거 원문 링크 목록 |
| policy_questions | list[string] | 자동 도출된 정책 질문 (1~2개) |
| risk_score | float | 리스크 점수 |
| requires_review | bool | 사람 확인 필요 여부 |

**Storage**: `data/reports/briefing_YYYY-MM-DD.json` + `data/reports/briefing_YYYY-MM-DD.md` + `data/reports/heatmap_YYYY-MM-DD.png`

## Relationships

```
Article (1) ←→ (1) Analysis
Article (N) ←→ (1) IssueCluster
IssueCluster (N) ←→ (1) BriefingReport.top_issues
```

## Data Flow

```
[수집] Article (raw/)
   ↓
[전처리] Article (processed/) — URL 기반 중복 제거, 플랫폼/기관 태깅
   ↓
[분석] Analysis (analyzed/) — LLM 요약, 키워드, 감성, 정책 분류
   ↓
[평가] IssueCluster (scored/) — 키워드 기반 클러스터링, 리스크 스코어링
   ↓
[리포트] BriefingReport (reports/) — TOP 10, 히트맵, 정책 질문
```
