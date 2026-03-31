# Tasks: 플랫폼 산업 자동 모니터링 파이프라인

**Input**: Design documents from `/specs/001-platform-monitor-pipeline/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1~US5)
- Exact file paths included in descriptions

---

## Phase 1: Setup

**Purpose**: 프로젝트 초기화 및 기본 구조 생성

- [x] T001 Create project directory structure per plan.md (`src/`, `src/collectors/`, `src/processors/`, `src/analyzers/`, `src/scorers/`, `src/reporters/`, `src/models/`, `src/utils/`, `data/raw/rss/`, `data/raw/news/`, `data/processed/`, `data/analyzed/`, `data/scored/`, `data/reports/`)
- [x] T002 [P] Create `requirements.txt` with dependencies: feedparser, requests, google-genai, pyyaml, matplotlib, seaborn, pytest
- [x] T003 [P] Create `config.yaml.example` with API 키 플레이스홀더, RSS 소스 URL, 검색 키워드 목록, 리스크 임계값 설정 (quickstart.md 참조)
- [x] T004 [P] Create `.gitignore` with `data/`, `config.yaml`, `venv/`, `__pycache__/`, `*.pyc` entries
- [x] T005 [P] Create all `__init__.py` files for packages: `src/`, `src/collectors/`, `src/processors/`, `src/analyzers/`, `src/scorers/`, `src/reporters/`, `src/models/`, `src/utils/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 모든 User Story에서 공유하는 핵심 인프라

**CRITICAL**: User Story 작업은 이 Phase 완료 후 시작

- [x] T006 Implement config loader in `src/config.py` — YAML 파일 로드 + 환경 변수 오버라이드 (NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, GEMINI_API_KEY) 지원
- [x] T007 [P] Implement Article dataclass in `src/models/article.py` — data-model.md의 Article 엔티티 필드 전체 구현 (id, title, content, url, source_type, source_name, published_at, collected_at, search_keywords, platform_tags, institution_tags, file_info)
- [x] T008 [P] Implement Analysis dataclass in `src/models/analysis.py` — data-model.md의 Analysis 엔티티 필드 전체 구현
- [x] T009 [P] Implement IssueCluster dataclass in `src/models/cluster.py` — data-model.md의 IssueCluster 엔티티 필드 전체 구현
- [x] T010 [P] Implement BriefingReport and TopIssue dataclasses in `src/models/report.py` — data-model.md의 BriefingReport + TopIssue 구조 구현
- [x] T011 [P] Implement JSON file I/O utilities in `src/utils/file_io.py` — JSON 읽기/쓰기, 데이터 디렉토리 경로 관리, dataclass ↔ dict 변환
- [x] T012 [P] Implement text utilities in `src/utils/text_utils.py` — HTML 태그 제거 (`<b>` 등), 텍스트 정규화, 문자열 길이 체크 (100자 미만 필터링)
- [x] T013 Implement CLI entry point in `src/cli.py` — argparse 기반 명령어: collect, preprocess, analyze, score, report, run-all, status. 각 명령은 해당 파이프라인 단계 모듈 호출

**Checkpoint**: 기본 인프라 완료 — User Story 구현 시작 가능

---

## Phase 3: User Story 1 - 기관 보도자료 자동 수집 (Priority: P1) MVP

**Goal**: 7개 기관의 보도자료를 RSS 피드로 자동 수집하여 JSON 저장

**Independent Test**: `python -m src.cli collect --rss` 실행 후 `data/raw/rss/` 에 7개 기관별 JSON 파일 생성 확인

### Implementation for User Story 1

- [x] T014 [US1] Implement RSS collector in `src/collectors/rss_collector.py` — feedparser로 korea.kr RSS 피드 파싱, config.yaml의 rss_sources 설정 사용, 기관별 보도자료 수집, 접속 실패 시 해당 기관 건너뛰기
- [x] T015 [US1] Implement HWPX text extractor in `src/collectors/hwpx_parser.py` — stdlib `zipfile` + `xml.etree.ElementTree`로 HWPX 파일 텍스트 추출, 다운로드 + 파싱, 실패 시 None 반환
- [x] T016 [US1] Integrate HWPX parser into RSS collector — `rss_collector.py`에서 첨부파일 URL 감지 시 hwpx_parser 호출, file_info.parse_status 기록
- [x] T017 [US1] Implement RSS 수집 결과 저장 로직 — Article 객체 생성, URL 기반 중복 체크 (기존 데이터 로드 후 비교), `data/raw/rss/{기관명}_{날짜}.json` 저장
- [x] T018 [US1] Wire RSS collection to CLI — `src/cli.py`의 `collect --rss` 명령에서 `rss_collector` 호출, 수집 건수 콘솔 출력

**Checkpoint**: `python -m src.cli collect --rss` 실행으로 7개 기관 보도자료 수집 가능

---

## Phase 4: User Story 2 - 뉴스 기사 자동 수집 (Priority: P1)

**Goal**: Naver Search API로 정책 키워드 기반 뉴스 수집 + 플랫폼/기관 자동 태깅

**Independent Test**: `python -m src.cli collect --news` 실행 후 `data/raw/news/` 에 키워드별 JSON 파일 생성, 플랫폼/기관 태그 포함 확인

### Implementation for User Story 2

- [x] T019 [US2] Implement Naver news collector in `src/collectors/news_collector.py` — requests로 Naver Search API 호출, config.yaml의 search_keywords 순회, 키워드당 최대 1,000건 페이지네이션 (display=100, start=1~901), sort=date, HTML 태그 제거, API 한도 경고
- [x] T020 [US2] Implement platform/institution tagger in `src/processors/tagger.py` — 플랫폼명 사전 (네이버, 카카오, 쿠팡, 배달의민족, 구글, 유튜브 등 국내·해외), 기관명 사전 (공정거래위원회, 개인정보보호위원회 등), title+description 텍스트에서 매칭 태깅
- [x] T021 [US2] Implement URL-based deduplicator in `src/processors/deduplicator.py` — 키워드 간 중복 기사 URL 기준 제거, 중복 기사의 search_keywords 병합
- [x] T022 [US2] Implement preprocess pipeline in `src/processors/__init__.py` 또는 별도 orchestrator — deduplicator + tagger 순차 실행, `data/processed/articles.json` 저장 (RSS + News 통합, RSS 단독 수집 시에도 실행 가능)
- [x] T023 [US2] Wire news collection and preprocessing to CLI — `collect --news` 명령에서 news_collector 호출, `preprocess` 명령에서 전처리 파이프라인 실행

**Checkpoint**: `python -m src.cli collect --news && python -m src.cli preprocess` 실행으로 뉴스 수집·전처리 완료

---

## Phase 5: User Story 3 - LLM 기반 뉴스 분석 (Priority: P2)

**Goal**: Gemini API로 수집된 기사의 요약, 키워드, 감성, 정책영역 멀티라벨 분류 수행

**Independent Test**: `python -m src.cli analyze` 실행 후 `data/analyzed/analyses.json`에 분석 결과 생성, 각 항목에 요약·키워드·감성·정책태그·신뢰도 포함 확인

### Implementation for User Story 3

- [x] T024 [US3] Implement Gemini analyzer in `src/analyzers/gemini_analyzer.py` — google-genai SDK 초기화 (gemini-2.5-flash-lite 모델), 분석 프롬프트 설계 및 구현: 원문 기반 분석만 수행 명시 (hallucination 방지), 요약 3문장 이내, 키워드 5개 이내, 감성 positive/negative/neutral, 7대 정책영역 enum 목록 제공한 멀티라벨 분류, 신뢰도 0~1, 구조화된 JSON 출력 요청, 응답 파싱, 모델명 기록
- [x] T026 [US3] Implement batch analysis orchestration — `data/processed/articles.json` 로드, 각 기사에 대해 Gemini 호출, 100자 미만 기사 스킵 (status="skipped"), API 실패 시 status="failed" + error_message 기록, 진행률 콘솔 출력
- [x] T027 [US3] Implement analysis result storage — Analysis 객체 생성, `data/analyzed/analyses.json` 저장, 이미 분석된 article_id 스킵 (재실행 안전), `--force` 옵션 시 재분석
- [x] T028 [US3] Wire analyze command to CLI — `analyze` 명령에서 분석 파이프라인 실행, `--force` 옵션 지원

**Checkpoint**: `python -m src.cli analyze` 실행으로 LLM 분석 완료, 원문 링크 보존 확인

---

## Phase 6: User Story 4 - 리스크 스코어링 및 급상승 이슈 탐지 (Priority: P3)

**Goal**: 이슈 클러스터링, 리스크 점수 산출, 급상승 이슈 탐지, 사람 확인 필요 플래그

**Independent Test**: `python -m src.cli score` 실행 후 `data/scored/clusters.json`에 클러스터별 리스크 점수, 급상승 여부, requires_review 플래그 확인

### Implementation for User Story 4

- [x] T029 [US4] Implement keyword-based clusterer in `src/scorers/clusterer.py` — 분석된 기사의 LLM 추출 키워드를 기반으로 그룹화, 키워드 일치/부분 일치로 클러스터 형성, 대표 키워드 선정
- [x] T030 [US4] Implement risk scorer in `src/scorers/risk_scorer.py` — 클러스터별 리스크 점수(0~100) 산출: 기사 수, 규제기관 동반 언급 빈도, 부정 감성 비율 등 가중 합산, config.yaml의 threshold(기본 70) 이상 시 requires_review=true
- [x] T031 [US4] Implement trend detector in `src/scorers/trend_detector.py` — 전주 데이터 대비 언급량 비교 (data/scored/ 이전 파일 참조), 200% 이상 증가 시 is_trending=true, trending_reason 기록, 감성 급변 탐지, 이전 데이터 없는 최초 실행 시 트렌드 탐지 건너뛰기
- [x] T032 [US4] Implement scoring pipeline orchestration — clusterer → risk_scorer → trend_detector 순차 실행, IssueCluster 객체 생성, `data/scored/clusters.json` 저장
- [x] T033 [US4] Wire score command to CLI — `score` 명령에서 스코어링 파이프라인 실행

**Checkpoint**: `python -m src.cli score` 실행으로 리스크 평가 완료, 임계값 이상 이슈에 "사람 확인 필요" 표시 확인

---

## Phase 7: User Story 5 - 주간 브리핑 및 리스크 히트맵 생성 (Priority: P3)

**Goal**: TOP 10 이슈 브리핑 Markdown + 리스크 히트맵 PNG 자동 생성

**Independent Test**: `python -m src.cli report` 실행 후 `data/reports/` 에 briefing .md/.json + heatmap .png 파일 생성, 모든 이슈에 원문 링크 포함 확인

### Implementation for User Story 5

- [x] T034 [US5] Implement briefing generator in `src/reporters/briefing_generator.py` — clusters.json에서 리스크 점수 상위 10개 선정, TopIssue 구조 생성 (이슈 제목, 요약, source_links, policy_questions), Gemini API로 정책 질문 1~2개 자동 도출
- [x] T035 [US5] Implement Markdown report writer — BriefingReport를 Markdown 형식으로 렌더링, 각 이슈에 원문 링크 포함 (Constitution II 준수), `data/reports/briefing_YYYY-MM-DD.md` 저장
- [x] T036 [US5] Implement heatmap generator in `src/reporters/heatmap_generator.py` — matplotlib + seaborn으로 플랫폼 x 정책영역 매트릭스 히트맵 생성, `data/reports/heatmap_YYYY-MM-DD.png` 저장
- [x] T037 [US5] Implement Markdown table for heatmap — briefing .md 파일 내에 플랫폼 x 정책영역 수치 테이블 추가 (PNG 이미지와 병행)
- [x] T038 [US5] Implement report pipeline orchestration + JSON 저장 — BriefingReport 객체 생성, `data/reports/briefing_YYYY-MM-DD.json` 저장
- [x] T039 [US5] Wire report command to CLI — `report` 명령에서 리포트 파이프라인 실행

**Checkpoint**: `python -m src.cli report` 실행으로 브리핑 + 히트맵 생성 완료

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: 전체 파이프라인 통합 및 마무리

- [x] T040 Implement `run-all` command in `src/cli.py` — collect → preprocess → analyze → score → report 전체 파이프라인 순차 실행
- [x] T041 Implement `status` command in `src/cli.py` — 수집 건수, 분석 완료/미완료/실패 건수, 최근 리포트 날짜 등 요약 출력
- [x] T042 [P] Add error handling and logging across all modules — 각 파이프라인 단계에서 실패 시 적절한 에러 메시지 출력, 다음 단계 진행 가능하도록 graceful 처리
- [x] T043 [P] Create README.md with setup instructions — quickstart.md 기반, Windows 환경 설치 가이드 포함
- [x] T044 Validate end-to-end pipeline on sample data — 전체 파이프라인 실행 테스트, quickstart.md 시나리오 검증, 모든 리포트 출력에 원문 링크 포함 확인 (Constitution II 검증)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — 즉시 시작 가능
- **Foundational (Phase 2)**: Setup 완료 필요 — 모든 User Story를 BLOCK
- **US1 보도자료 수집 (Phase 3)**: Foundational 완료 후 시작
- **US2 뉴스 수집 (Phase 4)**: Foundational 완료 후 시작 — US1과 병렬 가능
- **US3 LLM 분석 (Phase 5)**: US1 또는 US2 완료 필요 (분석 대상 데이터 필요)
- **US4 리스크 스코어링 (Phase 6)**: US3 완료 필요
- **US5 브리핑/히트맵 (Phase 7)**: US4 완료 필요
- **Polish (Phase 8)**: 모든 User Story 완료 후

### User Story Dependencies

- **US1 (P1)**: Foundational 이후 독립 — 다른 스토리에 의존 없음
- **US2 (P1)**: Foundational 이후 독립 — US1과 병렬 가능
- **US3 (P2)**: US1 또는 US2의 수집 결과 필요 (processed/articles.json)
- **US4 (P3)**: US3의 분석 결과 필요 (analyzed/analyses.json)
- **US5 (P3)**: US4의 스코어링 결과 필요 (scored/clusters.json)

### Within Each User Story

- Models before services (Phase 2에서 이미 완료)
- Core 구현 → 저장 → CLI 연결 순서
- Story 완료 후 다음 priority로 이동

### Parallel Opportunities

- Phase 1: T002, T003, T004, T005 모두 병렬 가능
- Phase 2: T007~T012 모두 병렬 가능 (T006 config 먼저, T013 CLI는 마지막)
- Phase 3~4: US1과 US2는 병렬 가능 (서로 다른 데이터 소스)

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Phase 1: Setup 완료
2. Phase 2: Foundational 완료
3. Phase 3: US1 보도자료 수집 → 테스트
4. Phase 4: US2 뉴스 수집 + 전처리 → 테스트
5. **STOP and VALIDATE**: 수집 파이프라인 독립 동작 확인

### Incremental Delivery

1. Setup + Foundational → 인프라 준비
2. US1 + US2 → 데이터 수집 MVP
3. US3 → LLM 분석 추가 → 분석 결과 확인
4. US4 → 리스크 평가 추가 → 스코어링 확인
5. US5 → 브리핑/히트맵 추가 → 최종 산출물 확인
6. Polish → 통합 실행, 에러 처리, 문서화

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US1과 US2는 병렬 진행 가능 (서로 독립적인 데이터 소스)
- US3~US5는 순차적 (파이프라인 의존성)
- 각 Checkpoint에서 독립 검증 후 다음 단계 진행
- Constitution II (Source Traceability): 모든 리포트/요약에 원문 링크 필수
- Constitution III (Human-in-the-Loop): risk_score >= 70 시 requires_review 플래그 필수
