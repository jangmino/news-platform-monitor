# Feature Specification: press_data.py RSS 수집 코드 통합

**Feature Branch**: `003-integrate-press-data`
**Created**: 2026-04-05
**Status**: Draft
**Input**: 기존에 구현된 RSS 피드 수집/파싱 코드를 news-platform-monitor 레포에 통합한다. press_data.py를 현재 레포의 구조와 코딩 스타일에 맞게 통합하는 것이 목표다.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 보도자료 상세 본문 완전 수집 (Priority: P1)

KISDI 연구원이 RSS 수집을 실행하면, RSS 요약문(summary)만이 아닌 실제 보도자료 웹 페이지의 전체 본문이 수집된다. 페이지 접근이 불가능하거나 본문 추출에 실패하면 RSS 요약문으로 자동 대체된다.

**Why this priority**: 현재 RSS summary는 전체 내용의 일부만 포함한다. 분석·요약 품질을 높이려면 전체 본문이 필요하며, 이는 분석 파이프라인 전체의 품질에 직접 영향을 준다.

**Independent Test**: 수집 실행 후 저장된 기사 본문 길이가 RSS summary보다 유의미하게 길어야 하며, 각 기사에 원문 링크가 보존되어 있어야 한다.

**Acceptance Scenarios**:

1. **Given** RSS 피드로 수집한 보도자료 항목이 있고, **When** 수집 처리가 완료되면, **Then** 각 항목의 본문은 해당 보도자료 상세 페이지에서 추출된 전체 텍스트를 포함한다
2. **Given** 보도자료 상세 페이지 접근이 실패하거나 본문 추출이 불가능한 경우, **When** 수집 처리가 완료되면, **Then** RSS 요약문이 본문으로 사용되고 원문 링크는 보존된다
3. **Given** 보도자료 페이지 유형이 다른 경우(pressReleaseView, policyNewsView 등), **When** 본문 추출을 수행하면, **Then** 각 페이지 유형에 적합한 선택자로 본문이 올바르게 추출된다

---

### User Story 2 - 다양한 첨부파일 형식 텍스트 추출 (Priority: P2)

KISDI 연구원이 RSS 수집을 실행하면, 보도자료에 첨부된 HWPX 파일 외에 PDF, ODT 파일의 텍스트도 자동으로 추출되어 본문에 포함된다. 파일 형식에 따라 우선순위(HWPX → PDF → ODT)를 적용하여 가장 적합한 파일에서 텍스트를 추출한다.

**Why this priority**: 정부 기관 보도자료에는 HWPX 외에도 PDF, ODT 형식의 첨부파일이 다수 존재한다. 이를 지원하면 수집되는 본문 텍스트의 완전성이 크게 향상된다.

**Independent Test**: PDF 또는 ODT 첨부파일이 있는 보도자료 항목에 대해 수집을 실행하고, 해당 파일의 텍스트가 본문에 포함되는지 확인한다.

**Acceptance Scenarios**:

1. **Given** 보도자료에 PDF 첨부파일이 있고 HWPX가 없는 경우, **When** 수집이 완료되면, **Then** PDF에서 추출한 텍스트가 본문으로 저장된다
2. **Given** 보도자료에 여러 형식(HWPX, PDF, ODT)의 첨부파일이 모두 있는 경우, **When** 수집이 완료되면, **Then** HWPX 파일의 텍스트가 우선 사용된다
3. **Given** 첨부파일 다운로드 또는 파싱이 실패한 경우, **When** 수집이 완료되면, **Then** 해당 항목은 웹 본문 또는 RSS 요약문으로 대체되고 파일 상태가 "failed"로 기록된다

---

### User Story 3 - 실제 작동하는 RSS URL 및 기관명 자동 식별 (Priority: P2)

KISDI 연구원이 시스템을 처음 설정하면, 검증된 RSS URL과 각 피드에서 자동 추출된 기관명으로 7개 기관의 보도자료가 수집된다. 설정 파일의 RSS URL을 실제 작동하는 부서별 엔드포인트(dept_xxx.xml 형식)로 업데이트하고, 피드 타이틀에서 기관명을 자동 추출한다.

**Why this priority**: 현재 config.yaml.example의 RSS URL 형식이 press_data.py에서 검증된 형식과 다르다. 잘못된 URL은 수집 실패로 이어지며, 기관명 자동 추출은 데이터 정확성을 높인다.

**Independent Test**: 시스템 실행 후 7개 기관 모두에서 보도자료가 수집되고, 각 기사의 source_name이 RSS 피드 타이틀에서 추출된 기관명인지 확인한다.

**Acceptance Scenarios**:

1. **Given** 업데이트된 RSS URL로 수집 명령을 실행하면, **When** 피드 파싱이 완료되면, **Then** 7개 기관 모두에서 최신 보도자료가 수집된다
2. **Given** RSS 피드 타이틀이 "대한민국 정책브리핑 - [기관명]" 형식인 경우, **When** 수집이 완료되면, **Then** 각 기사의 source_name에 접두어가 제거된 기관명만 저장된다
3. **Given** 피드 타이틀에서 기관명 추출이 불가능한 경우, **When** 수집이 완료되면, **Then** config.yaml에 지정된 카테고리 키 이름이 source_name으로 사용된다

---

### Edge Cases

- 웹 페이지 크롤링 중 타임아웃 또는 HTTP 오류 발생 시 RSS 요약문으로 자동 대체한다
- 첨부파일 링크가 상대 경로인 경우 `https://www.korea.kr` 도메인을 자동으로 붙여 완전한 URL로 변환한다
- 보도자료 페이지 구조가 예상과 다른 경우(선택자 미일치), 본문 텍스트 비율이 가장 높은 div를 fallback으로 사용한다
- 동일 보도자료에 첨부파일과 웹 본문이 모두 추출 가능한 경우, 첨부파일 텍스트를 우선 사용한다
- PDF/ODT 파싱 라이브러리가 설치되지 않은 환경에서는 해당 형식을 건너뛰고 다음 우선순위 형식을 시도한다

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 시스템은 RSS 수집 시 각 보도자료의 상세 페이지를 크롤링하여 전체 본문을 추출해야 한다
- **FR-002**: 웹 크롤링 본문 추출기는 korea.kr 보도자료 페이지(pressReleaseView, policyNewsView)에 최적화된 선택자를 우선 적용하고, 실패 시 범용 fallback을 사용해야 한다
- **FR-003**: 크롤링 실패 또는 본문 길이 50자 미만 시 RSS summary를 본문으로 자동 대체해야 한다
- **FR-004**: 시스템은 HWPX, PDF, ODT 형식의 첨부파일에서 텍스트를 추출할 수 있어야 한다 (우선순위: HWPX > PDF > ODT)
- **FR-005**: 첨부파일 링크는 페이지 HTML 파싱을 통해 발견해야 하며(fileId=, download, attachment 포함 href), 상대 경로는 절대 URL로 변환해야 한다
- **FR-006**: config.yaml.example의 RSS URL을 dept_xxx.xml 형식의 검증된 엔드포인트로 업데이트해야 한다
- **FR-007**: RSS 피드 타이틀에서 "대한민국 정책브리핑" 접두어를 제거하여 기관명을 자동 추출하고, 추출 실패 시 config 키 이름을 사용해야 한다
- **FR-008**: HTTP 요청 시 브라우저 User-Agent 헤더를 사용하여 차단 가능성을 최소화해야 한다
- **FR-009**: 새로 추가되는 의존성(PDF, ODT 파싱 라이브러리)은 requirements.txt에 반영되어야 한다
- **FR-010**: 기존 Article 데이터 모델, FileInfo 구조, JSON 저장 방식을 유지해야 한다 (하위 호환성 보장)

### Key Entities

- **WebContent**: 보도자료 상세 페이지에서 추출한 웹 본문. 선택자 매칭 결과 또는 fallback div 텍스트. Article의 content 필드에 저장
- **AttachmentFile**: 보도자료 페이지에서 발견된 첨부파일. 파일명, URL, 파일 형식(hwpx/pdf/odt), 파싱 상태 포함. 기존 FileInfo 엔티티 확장

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 수집된 보도자료 본문의 평균 길이가 통합 전 대비 3배 이상 증가한다 (RSS summary 대비 상세 페이지 본문)
- **SC-002**: PDF 또는 ODT 첨부파일이 있는 보도자료에서 해당 파일 텍스트 추출 성공률 80% 이상이다
- **SC-003**: 7개 기관 RSS ���집 성공률 100% (업데이트된 URL 기준)
- **SC-004**: 기존 수집·분석 파이프라인(전처리, LLM 분석, 리스크 스코어링, 리포트)이 통합 후에도 정상 동작한다 (하위 호환성)
- **SC-005**: source_name 필드에 "대한민국 정책브리핑" 접두어가 포함된 기사가 0건이다

## Clarifications

### Session 2026-04-05

- Q: 웹 크롤링 추가로 수집 속도가 느려지는 문제는? → A: press_data.py의 1.2초 딜레이 방식 유지
- Q: 신규 의존성(PyMuPDF, odfpy) 설치 실패 환경 처리? → A: ImportError 시 해당 형식 건너뜀, 기존 동작에 영향 없음

## Assumptions

- press_data.py에서 사용한 RSS URL (dept_xxx.xml 형식)이 현재도 유효하다
- korea.kr 보도자료 페이지 HTML 구조(pressReleaseView, div.view-cont 등)가 크게 변경되지 않았다
- PyMuPDF(pymupdf)와 odfpy 라이브러리가 Windows 10/11에서 정상 설치된다
- 기존 FileInfo 구조로 PDF/ODT 정보를 수용할 수 있다 (name, url, parse_status 필드 그대로 사용)
- 웹 크롤링 추가로 인한 수집 소요 시간 증가는 허용 범위 내이다 (기관당 최대 50건 × 약 2초 = 기관당 약 1~2분)
