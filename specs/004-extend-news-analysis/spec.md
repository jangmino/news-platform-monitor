# Feature Specification: LLM 분석 및 대시보드 뉴스 데이터 확장

**Feature Branch**: `004-extend-news-analysis`
**Created**: 2026-04-16
**Status**: Draft
**Input**: 기존에 보도자료에 한정했던 LLM 분석 및 대시보드 시각화를 뉴스 데이터까지 포함하여 확장한다.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 뉴스 기사 LLM 분석 실행 (Priority: P1)

KISDI 연구원이 분석 명령을 실행하면, `data/raw/news/news_data.json`에 저장된 뉴스 기사 각각에 대해 Gemini API가 보도자료와 동일한 7개 분석 필드(플랫폼 추출, 정책영역 분류, 리스크 점수, 키워드, 이슈 요약, 감성 레이블, 신뢰도 점수)를 생성하여 `data/analyzed/news_analysis.json`에 저장한다. 이미 분석된 항목은 재분석하지 않는다.

**Why this priority**: 대시보드 통합 표시와 통합 정책 제언 생성 모두 뉴스 분석 결과 파일이 선행되어야 가능하다. 분석 파이프라인이 먼저 동작해야 한다.

**Independent Test**: 뉴스 기사 10건에 대해 `python -m src analyze-news`를 실행하고, `data/analyzed/news_analysis.json`에 각 항목의 7개 분석 필드가 채워진 JSON이 저장되었는지 확인한다.

**Acceptance Scenarios**:

1. **Given** `news_data.json`에 뉴스 기사가 존재하고 GEMINI_API_KEY가 설정된 상태, **When** `python -m src analyze-news`를 실행하면, **Then** 각 항목에 7개 분석 필드가 채워진 `news_analysis.json`이 생성된다
2. **Given** 이전에 분석된 `news_analysis.json`이 존재하는 상태, **When** 분석 명령을 재실행하면, **Then** 이미 분석된 항목(동일 `originallink` 기준)은 API를 재호출하지 않고 기존 결과를 유지한다
3. **Given** 뉴스 기사의 title과 description 합산이 30자 미만인 항목, **When** 분석 대상 목록을 구성하면, **Then** 해당 항목은 분석 대상에서 제외되고 `skipped` 상태로 기록된다

---

### User Story 2 - 대시보드에서 보도자료·뉴스 통합 탐색 (Priority: P1)

KISDI 연구원이 대시보드를 열면, 보도자료와 뉴스 기사 분석 결과가 통합 표시된다. 상단 데이터 소스 필터(전체 / 보도자료 / 뉴스)를 통해 데이터를 선택적으로 탐색할 수 있으며, 각 이슈 카드에는 출처 구분 뱃지(보도자료/뉴스)가 표시된다.

**Why this priority**: 연구원이 두 데이터소스를 함께 보거나 비교할 수 있어야 통합 분석의 가치가 발생한다. 뉴스 분석이 완료된 즉시 대시보드에 반영되어야 한다.

**Independent Test**: `press_analysis.json`과 `news_analysis.json`이 모두 존재하는 상태에서 대시보드를 실행하고, "전체" 필터 시 두 파일의 기사가 합산 표시되는지, "뉴스" 필터 시 뉴스만 표시되는지 확인한다.

**Acceptance Scenarios**:

1. **Given** `press_analysis.json`과 `news_analysis.json`이 모두 존재하는 상태, **When** 대시보드를 열면, **Then** 두 파일의 기사가 합산되어 요약 카드(수집 건수, 분석 완료 건수, 평균 리스크 점수)에 반영된다
2. **Given** 대시보드 상단 필터에서 "뉴스"를 선택하면, **Then** 모든 섹션(리스크 히트맵, 트렌드 차트, 키워드 클라우드, 이슈 타임라인, 플랫폼 카드)이 뉴스 기사만을 기준으로 갱신된다
3. **Given** `news_analysis.json`만 존재하고 `press_analysis.json`이 없는 상태, **When** 대시보드를 실행하면, **Then** 뉴스 데이터만으로 모든 섹션이 정상 렌더링되고 오류가 발생하지 않는다
4. **Given** 섹션 4의 이슈 카드를 조회하면, **When** 카드를 보면, **Then** 각 카드에 "보도자료" 또는 "뉴스" 출처 구분 뱃지가 표시된다

---

### User Story 3 - 통합 정책 제언 생성 (Priority: P2)

KISDI 연구원이 분석 명령 완료 후 제언 생성을 요청하면, 보도자료와 뉴스 기사 분석 결과를 모두 종합하여 Gemini API가 AI 정책 제언 3개를 생성한다. 제언은 `data/analyzed/combined_recommendations.json`에 별도 저장되며, 대시보드 섹션 4 제언 패널에 반영된다.

**Why this priority**: 개별 데이터소스 제언보다 두 소스를 종합한 제언이 더 포괄적인 인사이트를 제공한다. 기존 보도자료 제언(`press_analysis.json`의 `policy_recommendations`)에는 영향을 주지 않는다.

**Independent Test**: 두 분석 파일이 모두 존재하는 상태에서 `python -m src generate-recommendations`를 실행하고, `combined_recommendations.json`에 `title`과 `description`을 가진 항목 3개가 존재하는지 확인한다.

**Acceptance Scenarios**:

1. **Given** `press_analysis.json`과 `news_analysis.json`이 모두 존재하는 상태, **When** 제언 생성이 수행되면, **Then** 두 파일의 분석 결과를 종합한 컨텍스트를 기반으로 제언 3개가 생성되어 `combined_recommendations.json`에 저장된다
2. **Given** 어느 한 파일만 존재하는 상태, **When** 제언 생성이 수행되면, **Then** 존재하는 파일의 분석 결과만으로 제언 3개가 생성된다
3. **Given** 동일한 분석 결과 건수로 재실행하면, **Then** 제언은 재생성하지 않고 기존 값을 유지한다 (건수 변경 시에만 재생성)

---

### User Story 4 - 뉴스 전용 언론사 시각화 (Priority: P3)

KISDI 연구원이 대시보드 필터를 "뉴스"로 설정하면, 섹션 1에 언론사별 기사 수 파이차트가 추가 표시된다. 섹션 4 이슈 카드에도 언론사명이 포함된다.

**Why this priority**: 기본 통합 시각화가 동작한 후 추가되는 뉴스 데이터 특화 편의 기능이다.

**Independent Test**: 대시보드를 "뉴스" 필터로 설정하고 섹션 1에 언론사별 기사 수 파이차트가 렌더링되는지 확인한다.

**Acceptance Scenarios**:

1. **Given** 필터가 "뉴스"인 상태, **When** 섹션 1을 조회하면, **Then** 언론사별 기사 수 파이차트가 요약 카드 행 하단에 추가 표시된다
2. **Given** 필터가 "전체" 또는 "보도자료"인 상태, **When** 섹션 1을 조회하면, **Then** 언론사별 파이차트는 표시되지 않는다

---

### Edge Cases

- `news_data.json`이 존재하지 않는 상태에서 `analyze-news`를 실행하면 "뉴스 데이터가 없습니다. 먼저 수집을 실행하세요." 안내를 출력하고 종료한다
- 대시보드에서 두 분석 파일이 모두 없을 때 "분석 데이터가 없습니다. 분석을 먼저 실행하세요." 빈 상태 UI를 표시한다
- 뉴스 기사 `description` 필드에 포함된 HTML 태그(`<b>`, `</b>` 등)는 분석 전 제거한다
- 대시보드 필터가 "보도자료"인데 `press_analysis.json`이 없으면 빈 상태 UI를 오류 없이 표시한다
- 뉴스 기사의 `originallink`가 없는 항목은 `link`(네이버 뉴스 URL)를 중복 판별 키로 대체 사용한다
- Gemini API 호출 실패 시 뉴스 항목도 `status: "failed"`로 기록하고 나머지 항목은 계속 분석한다

## Requirements *(mandatory)*

### Functional Requirements

**뉴스 분석 파이프라인**

- **FR-001**: 시스템은 `data/raw/news/news_data.json`을 입력으로 받아 각 항목에 대해 Gemini API를 호출하고, 결과를 `data/analyzed/news_analysis.json`에 저장해야 한다
- **FR-002**: 뉴스 항목 분석 시 `title` + `description`을 분석 입력으로 사용하며, 합산 텍스트가 30자 미만이면 `status: "skipped"`로 기록한다
- **FR-003**: 뉴스 분석 파이프라인은 보도자료 분석과 동일한 7개 출력 필드(`platforms`, `policy_domains`, `risk_score`, `keywords`, `summary`, `sentiment`, `confidence`)를 생성해야 한다
- **FR-004**: 이미 분석된 뉴스 항목(동일 `originallink` 값)은 Gemini API를 재호출하지 않아야 한다 (증분 분석)
- **FR-005**: 뉴스 분석 파이프라인은 `python -m src analyze-news` 명령으로 독립 실행 가능해야 한다
- **FR-006**: `analyze-news` 명령 완료 시 `data/analyzed/news_analysis.json`을 `dashboard/public/data/news_analysis.json`으로 자동 복사해야 한다
- **FR-007**: 뉴스 항목 분석도 Gemini API 호출 간 최소 1초 딜레이를 적용해야 한다
- **FR-008**: 뉴스 분석 결과 저장 시 atomic write(임시 파일 → rename)를 사용해야 한다
- **FR-009**: 뉴스 기사의 `description`에 포함된 HTML 태그는 분석 전에 제거해야 한다
- **FR-010**: `generate-recommendations` 명령은 `press_analysis.json`과 `news_analysis.json`의 분석 완료 항목 `summary`·`keywords`를 종합하여 정책 제언 3개를 생성하고 `data/analyzed/combined_recommendations.json`에 저장해야 한다
- **FR-011**: `generate-recommendations` 완료 시 `combined_recommendations.json`을 `dashboard/public/data/combined_recommendations.json`으로 자동 복사해야 한다

**웹 대시보드 확장**

- **FR-012**: 대시보드 상단에 데이터 소스 필터(전체 / 보도자료 / 뉴스)를 추가해야 하며, 필터 선택 시 모든 섹션의 데이터가 해당 소스로 갱신된다
- **FR-013**: 대시보드는 `press_analysis.json`과 `news_analysis.json`을 모두 로드하며, 각 파일이 없을 경우 해당 소스를 빈 배열로 처리한다 (파일 부재 시 오류 없이 동작)
- **FR-014**: 섹션 4의 이슈 카드 각각에 출처 구분 뱃지("보도자료" / "뉴스")를 표시해야 한다
- **FR-015**: 대시보드 섹션 4의 AI 정책 제언 패널은 `combined_recommendations.json`이 존재하면 해당 파일을, 없으면 `press_analysis.json`의 `policy_recommendations`를 표시한다
- **FR-016**: 필터가 "뉴스"인 상태에서 섹션 1에 언론사(`originallink` 도메인 기준)별 기사 수 파이차트를 추가 표시해야 한다
- **FR-017**: 두 분석 파일은 `dashboard/public/data/` 경로에서 정적 파일로 접근하며, 대시보드는 별도 백엔드 없이 동작해야 한다

### Key Entities

- **NewsAnalysis (뉴스 분석 결과 파일)**: `news_analysis.json` 최상위 구조. `generated_at`, `total_count`, `analyzed_count`, `articles` (list) 포함. `policy_recommendations`는 포함하지 않음 (통합 제언 파일로 분리)
- **AnalyzedNewsArticle**: 뉴스 원본 필드(`title`, `description`, `originallink`, `link`, `pubDate`, `source_name`) + 분석 결과 필드(`platforms`, `policy_domains`, `risk_score`, `keywords`, `summary`, `sentiment`, `confidence`, `status`, `raw_response`) + `source_type: "news"` (대시보드 출처 구분용)
- **AnalyzedPressArticle**: 기존 보도자료 분석 구조에 `source_type: "press"` 필드 추가
- **CombinedRecommendations**: `combined_recommendations.json` 구조. `generated_at`, `source_counts` (보도자료/뉴스 기사 수 기록), `policy_recommendations` (3개 항목, 각각 `title` + `description`) 포함

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 뉴스 기사 50건 분석 실행 시 분석 완료율(status: analyzed) 90% 이상이다
- **SC-002**: 이미 분석된 뉴스 데이터에 대해 재실행 시 Gemini API 신규 호출 건수가 0건이다
- **SC-003**: 보도자료와 뉴스가 모두 있는 상태에서 대시보드 필터 전환(전체↔보도자료↔뉴스) 시 각 섹션이 1초 이내에 갱신된다
- **SC-004**: 한 쪽 분석 파일이 없는 상태에서도 대시보드가 오류 없이 실행되고, 존재하는 데이터만 정상 표시된다
- **SC-005**: 통합 정책 제언 3개가 두 데이터소스 기여 건수를 `source_counts` 필드로 추적 가능하다
- **SC-006**: 뉴스 분석 파이프라인과 보도자료 분석 파이프라인이 독립적으로 실행 가능하다 (각각 단독 실행 시 오류 없음)

## Clarifications

### Session 2026-04-16

- Q: 뉴스와 보도자료를 하나의 통합 분석 파일로 합칠 것인가, 별도 파일로 관리할 것인가? → A: 별도 파일 유지(`press_analysis.json`, `news_analysis.json`). 대시보드가 두 파일을 로드하여 클라이언트 사이드에서 필터 시 동적으로 합산·분리 표시
- Q: 기존 `press_analysis.json`의 `policy_recommendations` 필드는 어떻게 처리하는가? → A: 기존 구조 변경 없이 유지. 통합 제언은 `combined_recommendations.json`으로 분리
- Q: 뉴스 기사의 중복 판별 키는? → A: `originallink`를 기본 키로 사용. `originallink`가 없으면 `link`로 대체
- Q: 언론사 식별 방식은? → A: `originallink`의 도메인 파트(예: `news.joins.com`)를 언론사 식별자로 사용. 별도 언론사 사전 불필요

## Assumptions

- `data/raw/news/news_data.json`은 spec-001 파이프라인이 생성하는 파일이며, 각 항목은 `title`, `description`, `originallink`, `link`, `pubDate` 필드를 포함한다
- 뉴스 기사는 `description` 필드(패시지, 최대 300자)만 제공되며 전문 크롤링은 이번 spec 범위 밖이다. 분석 입력 텍스트는 `title + description`으로 제한한다
- 기존 `analyze-press` 명령의 동작과 출력 형식은 이번 spec에서 변경하지 않는다 (하위 호환 유지)
- 대시보드는 두 데이터 파일을 병렬로 fetch하고 클라이언트 사이드에서 병합·필터링한다
- 뉴스 기사의 `pubDate`는 날짜 필드로 사용하며, 보도자료의 `date`와 동일한 ISO 8601 형식으로 이미 정규화되어 있다
- `dashboard/public/data/news_analysis.json`과 `combined_recommendations.json`은 `.gitignore`에 추가한다
- `source_type` 필드는 기존 `press_analysis.json` 재분석 없이 파이프라인 코드 수정만으로 신규 저장 시점부터 포함된다 (기존 파일 마이그레이션 불필요)
