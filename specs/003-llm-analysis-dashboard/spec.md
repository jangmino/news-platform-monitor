# Feature Specification: Gemini LLM 분석 + 웹 대시보드 시각화

**Feature Branch**: `003-llm-analysis-dashboard`
**Created**: 2026-04-12
**Status**: Draft
**Input**: 기존 파이프라인의 보도자료 JSON을 Gemini API로 분석하고, 그 결과를 웹 대시보드로 시각화한다.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 보도자료 LLM 분석 실행 (Priority: P1)

KISDI 연구원이 분석 명령을 실행하면, `data/raw/rss/press_data.json`에 저장된 보도자료 각각에 대해 Gemini API가 플랫폼 추출, 정책영역 분류, 리스크 점수, 키워드, 이슈 요약, 감성 레이블, 신뢰도 점수를 생성하여 JSON 파일로 저장한다. 이미 분석된 항목은 재분석하지 않는다.

**Why this priority**: 대시보드가 읽는 분석 결과 JSON이 없으면 시각화가 불가능하다. 분석 파이프라인이 먼저 동작해야 한다.

**Independent Test**: 보도자료 10건에 대해 분석을 실행하고, `data/analyzed/press_analysis.json`에 각 항목의 모든 분석 필드(platforms, policy_domains, risk_score, keywords, summary, sentiment, confidence)가 채워진 JSON이 저장되었는지 확인한다.

**Acceptance Scenarios**:

1. **Given** `press_data.json`에 보도자료가 존재하고 GEMINI_API_KEY가 설정된 상태, **When** 분석 명령(`python -m src analyze-press`)을 실행하면, **Then** 각 항목에 7개 분석 필드가 채워진 `press_analysis.json`이 생성된다
2. **Given** 이전에 분석된 `press_analysis.json`이 존재하는 상태, **When** 분석 명령을 재실행하면, **Then** 이미 분석된 항목(동일 link 기준)은 API를 재호출하지 않고 기존 결과를 유지한다
3. **Given** 보도자료 본문이 50자 미만인 항목, **When** 분석 대상 목록을 구성하면, **Then** 해당 항목은 분석 대상에서 제외되고 `skipped` 상태로 기록된다

---

### User Story 2 - 전체 AI 정책 제언 생성 (Priority: P2)

KISDI 연구원이 분석 명령 완료 후 제언 생성을 요청하면, 전체 보도자료 분석 결과를 종합하여 Gemini API가 AI 정책 제언 3개(제목 + 설명)를 생성하고 별도 JSON 필드로 저장한다.

**Why this priority**: 개별 기사 분석과 별개로, 연구원이 포럼에서 즉시 활용 가능한 정책 인사이트를 제공한다.

**Independent Test**: 분석 완료된 데이터를 기준으로 제언 생성을 실행하고, `press_analysis.json`의 `policy_recommendations` 배열에 `title`과 `description`을 가진 항목 3개가 존재하는지 확인한다.

**Acceptance Scenarios**:

1. **Given** 분석 완료된 `press_analysis.json`이 존재하는 상태, **When** 제언 생성이 수행되면, **Then** 전체 분석 결과를 요약한 컨텍스트를 기반으로 제언 3개(각각 `title`, `description` 포함)가 생성된다
2. **Given** 생성된 제언이 이미 존재하는 상태, **When** 재실행하면, **Then** 제언은 재생성하지 않고 기존 값을 유지한다 (분석 결과 건수가 변경된 경우 제외)

---

### User Story 3 - 웹 대시보드로 분석 결과 탐색 (Priority: P2)

KISDI 연구원이 대시보드 서버를 실행하면, 브라우저에서 4개 섹션으로 구성된 대시보드가 열리고, 분석 결과를 인터랙티브 차트로 탐색할 수 있다. 대시보드는 분석 파이프라인과 독립적으로 실행되며, `press_analysis.json`을 읽기만 한다.

**Why this priority**: 연구원이 분석 결과를 한눈에 파악하고 포럼 자료로 활용하려면 시각화가 필수이다.

**Independent Test**: `python -m src dashboard` 실행 후 `http://localhost:8050`에 접속하여 4개 섹션(데이터 개요, 트렌드, 키워드·타임라인, 플랫폼 카드)이 모두 렌더링되고, 리스크 히트맵에 데이터가 표시되는지 확인한다.

**Acceptance Scenarios**:

1. **Given** `press_analysis.json`이 존재하는 상태, **When** 대시보드 서버를 실행하면, **Then** `http://localhost:8050`에서 4개 섹션이 모두 렌더링된 페이지에 접속할 수 있다
2. **Given** 대시보드가 실행 중인 상태, **When** `press_analysis.json`이 업데이트되면, **Then** 페이지를 새로고침하면 최신 데이터가 반영된다 (자동 폴링 불필요, 새로고침으로 충분)
3. **Given** `press_analysis.json`이 존재하지 않는 상태, **When** 대시보드를 실행하면, **Then** "데이터가 없습니다. 분석을 먼저 실행하세요." 안내 메시지가 표시되고 오류 없이 실행된다

---

### User Story 4 - 섹션별 인터랙션 (Priority: P3)

KISDI 연구원이 대시보드에서 특정 플랫폼이나 정책영역을 클릭하면, 해당 조건에 맞는 이슈 카드나 타임라인 항목이 필터링되어 표시된다.

**Why this priority**: 기본 시각화가 동작한 이후에 추가되는 인터랙션 편의 기능이다.

**Independent Test**: 리스크 히트맵에서 "네이버 × 공정거래" 셀을 클릭하면, 섹션 4의 이슈 카드가 해당 조건으로 필터링되는지 확인한다.

**Acceptance Scenarios**:

1. **Given** 리스크 히트맵이 표시된 상태, **When** 특정 셀(플랫폼 × 정책영역)을 클릭하면, **Then** 섹션 4의 플랫폼별 이슈 카드가 해당 플랫폼 기준으로 필터링된다
2. **Given** 필터가 적용된 상태, **When** 히트맵의 같은 셀을 다시 클릭하면, **Then** 필터가 해제되고 전체 카드가 다시 표시된다

---

### Edge Cases

- Gemini API 호출 실패(네트워크 오류, 할당량 초과) 시 해당 항목은 `status: "failed"`로 기록하고 나머지 항목은 계속 분석한다
- API 응답이 기대한 JSON 스키마와 다를 경우 해당 항목을 `status: "parse_error"`로 기록하고 원본 응답을 `raw_response` 필드에 보존한다
- 보도자료에서 플랫폼이 언급되지 않은 경우 `platforms: []` (빈 배열)로 저장하고, 히트맵에서는 "기타" 행으로 집계한다
- 분석 결과 JSON이 존재하지만 `articles` 배열이 비어 있는 경우, 대시보드는 빈 상태 UI를 표시한다
- 대시보드와 분석 파이프라인이 동시에 같은 JSON 파일을 읽고 쓰는 경우를 피하기 위해, 분석은 임시 파일에 쓰고 완료 후 원본을 교체하는 atomic write를 사용한다

## Requirements *(mandatory)*

### Functional Requirements

**분석 파이프라인**

- **FR-001**: 시스템은 `data/raw/rss/press_data.json`을 입력으로 받아 각 항목에 대해 Gemini API를 호출하고, 결과를 `data/analyzed/press_analysis.json`에 저장해야 한다
- **FR-002**: 개별 항목 분석 출력은 `platforms` (list[str]), `policy_domains` (list[str]), `risk_score` (int 0-100), `keywords` (list[str], 5개), `summary` (str), `sentiment` (str: 긍정/부정/중립), `confidence` (float 0-1), `status` (str: analyzed/failed/skipped/parse_error) 필드를 포함해야 한다
- **FR-003**: 전체 종합 분석 출력으로 `policy_recommendations` 배열에 3개의 정책 제언(각각 `title`, `description` 포함)을 저장해야 한다
- **FR-004**: 이미 분석된 항목(동일 `link` 값)은 Gemini API를 재호출하지 않아야 한다 (증분 분석)
- **FR-005**: 본문(`content`) 길이가 50자 미만인 항목은 분석 대상에서 제외하고 `status: "skipped"`로 기록해야 한다
- **FR-006**: Gemini API 호출 간 최소 1초 딜레이를 적용하여 할당량 초과를 방지해야 한다
- **FR-007**: 분석 결과 저장 시 atomic write(임시 파일 → rename)를 사용해야 한다
- **FR-008**: 분석 파이프라인은 `python -m src analyze-press` 명령으로 독립 실행 가능해야 한다
- **FR-009**: `platforms` 추출 시 `config.yaml`의 `platforms.domestic` 및 `platforms.foreign` 목록을 기준으로 한다
- **FR-010**: `policy_domains` 분류 시 `config.yaml`의 `policy_domains` 목록을 기준으로 하며, 멀티라벨 가능이다

**웹 대시보드**

- **FR-011**: 대시보드는 `press_analysis.json`을 읽기 전용으로 사용하며, 파이프라인과 완전히 분리된 프로세스로 실행되어야 한다
- **FR-012**: 대시보드는 `dashboard/` 디렉토리에서 `bun run dev`(개발) 또는 `bun run build`(빌드) 명령으로 실행한다. 기본 개발 포트는 5173이다
- **FR-013**: `analyze-press` 명령 완료 시 `data/analyzed/press_analysis.json`을 `dashboard/public/data/press_analysis.json`으로 자동 복사해야 한다 (대시보드가 정적 파일로 접근하기 위함)
- **FR-014**: 섹션 1은 수집 건수, 분석 완료 건수, 평균 리스크 점수, 고위험 이슈 수(임계값 이상)를 표시하는 요약 카드와, 플랫폼 × 정책영역 리스크 히트맵(셀 값: 평균 risk_score)을 포함해야 한다
- **FR-015**: 섹션 2는 일별 기사 수 라인 차트(이슈 트렌드)와, 이슈 클러스터 버블차트(x: 날짜, y: risk_score, 크기: 기사 수, 색상: 정책영역)를 포함해야 한다
- **FR-016**: 섹션 3은 키워드 빈도 기반 태그 클라우드와, 고위험 이슈 타임라인(날짜 + 제목 + risk_score + sentiment)을 포함해야 한다. 타임라인은 risk_score 내림차순으로 정렬한다
- **FR-017**: 섹션 4는 플랫폼별 이슈 요약 카드(플랫폼명, 관련 기사 수, 최고 risk_score, 대표 키워드, 요약 발췌)와, AI 정책 제언 패널(`policy_recommendations`의 3개 항목)을 포함해야 한다
- **FR-018**: 리스크 히트맵 셀 클릭 시 섹션 4의 플랫폼 카드가 해당 플랫폼으로 필터링되어야 한다
- **FR-019**: `press_analysis.json`이 없거나 비어 있을 때 대시보드는 오류 없이 빈 상태 UI를 표시해야 한다
- **FR-020**: 대시보드는 Bun + Vite + React + TypeScript + shadcn/ui + Recharts로 구현하며, 별도 백엔드 서버는 사용하지 않는다. 히트맵은 HTML 테이블 + Tailwind로, 키워드 클라우드는 React span + 인라인 스타일로 구현한다

### Key Entities

- **PressAnalysis (분석 결과 파일)**: `press_analysis.json` 최상위 구조. `generated_at` (ISO 날짜), `total_count` (int), `analyzed_count` (int), `articles` (list), `policy_recommendations` (list) 포함
- **AnalyzedArticle**: 기존 Article 필드에 분석 결과 필드(`platforms`, `policy_domains`, `risk_score`, `keywords`, `summary`, `sentiment`, `confidence`, `status`)가 추가된 구조
- **PolicyRecommendation (정책 제언)**: `title` (str), `description` (str) 필드를 가진 구조. `policy_recommendations` 배열의 원소

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 보도자료 50건 분석 실행 시 분석 완료율(status: analyzed) 90% 이상이다
- **SC-002**: 이미 분석된 데이터에 대해 재실행 시 Gemini API 신규 호출 건수가 0건이다 (증분 분석 검증)
- **SC-003**: 대시보드 실행 후 초기 페이지 로드 시간이 5초 이내이다 (데이터 100건 기준)
- **SC-004**: `config.yaml`의 플랫폼 및 정책영역 목록이 변경되어도 코드 수정 없이 분석 및 대시보드에 반영된다
- **SC-005**: 분석 파이프라인과 대시보드가 독립적으로 실행 가능하다 (각각 단독 실행 시 오류 없음)
- **SC-006**: 리스크 히트맵이 config.yaml의 전체 플랫폼 × 전체 정책영역 조합을 표시한다 (데이터 없는 셀은 0 또는 회색)

## Clarifications

### Session 2026-04-12

- Q: 이슈 클러스터링은 어떻게 하는가? → A: 이번 spec에서는 키워드 기반 단순 그룹핑(동일 키워드 공유 기사 묶음). 고도화는 추후 spec에서 별도 정의
- Q: 대시보드 인증(로그인)은 필요한가? → A: 불필요. 로컬 실행 전제
- Q: Naver 뉴스 데이터는 언제 추가되는가? → A: 현재 spec에서는 보도자료(`press_data.json`)만 사용. Naver 데이터 통합은 추후 spec에서 확장
- Q: 대시보드 UI 프레임워크는? → A: Bun + Vite + React + TypeScript + shadcn/ui + Recharts. Python과 완전히 분리된 별도 프로젝트(`dashboard/` 디렉토리)
- Q: 정책 제언 재생성 기준은? → A: 분석 완료 기사 건수가 이전 생성 시점 대비 달라진 경우에만 재생성

## Assumptions

- `press_data.json`의 각 항목은 `title`, `content`, `link`, `date`, `dept` 필드를 포함한다 (spec-002 결과물 기준)
- Gemini API 모델은 `config.yaml`의 `api.gemini.model` 값(`gemini-2.5-flash-lite`)을 사용한다
- 리스크 임계값은 `config.yaml`의 `risk.threshold` 값(기본 70)을 사용한다
- 대시보드는 로컬 환경(Windows 10/11 랩탑)에서 단일 사용자가 사용한다
- Bun이 Windows 환경에 설치되어 있다 (https://bun.sh 설치 필요)
- 분석 결과 JSON 파일 경로는 `data/analyzed/press_analysis.json`(canonical)과 `dashboard/public/data/press_analysis.json`(대시보드용 복사본)으로 고정한다
- `dashboard/public/data/press_analysis.json`은 `.gitignore`에 추가한다
- 이슈 타임라인의 "고위험"은 `risk_score >= config.yaml의 risk.threshold` 기준이다
