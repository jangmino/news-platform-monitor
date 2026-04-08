# Tasks: press_data.py RSS 수집 코드 통합

**Input**: Design documents from `/specs/002-integrate-press-data/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Organization**: 3개 User Story + Setup 순서로 구성. rss_collector.py가 세 스토리의 통합점이므로 순차 적용.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 다른 파일, 의존성 없음 — 병렬 실행 가능
- **[Story]**: 해당 User Story 레이블 (US1/US2/US3)

---

## Phase 1: Setup (의존성 및 설정)

**Purpose**: 코드 작성 전 환경 준비. Phase 3~5의 전제 조건.

- [x] T001 requirements.txt에 beautifulsoup4, pymupdf, odfpy 추가 (`requirements.txt`)
- [x] T002 [P] config.yaml.example의 rss_sources를 dept_xxx.xml 형식으로 교체 (`config.yaml.example`)

**Checkpoint**: `pip install -r requirements.txt` 성공 확인

---

## Phase 2: Foundational (공통 인프라)

> 이번 통합은 기존 데이터 모델(Article, FileInfo)과 파이프라인을 변경하지 않는다.
> 신규 모듈 2개(web_scraper.py, doc_extractor.py)가 독립적으로 구현 가능하므로 별도 Foundation 단계 없이 Phase 3부터 시작한다.

---

## Phase 3: User Story 1 — 보도자료 상세 본문 완전 수집 (Priority: P1) 🎯 MVP

**Goal**: RSS summary 대신 상세 페이지 전체 본문을 수집. 크롤링 실패 시 RSS summary로 자동 fallback.

**Independent Test**:
```bash
python -m src.cli collect --rss
# 수집 후 확인:
python -c "
import json; from pathlib import Path
for f in Path('data/raw/rss').glob('*.json'):
    d = json.loads(f.read_text('utf-8'))
    if d: print(f.stem, '평균', sum(len(a['content']) for a in d)//len(d), '자')
"
# 기대: 각 기관 평균 500자 이상 (기존 RSS summary 대비 3배+)
```

### Implementation for User Story 1

- [x] T003 [US1] `src/collectors/web_scraper.py` 신규 생성 — `extract_web_text(soup, url)` 및 `crawl_page(url) -> tuple[str, list[dict]]` 구현 (korea.kr selector 우선순위, fallback 포함)
- [x] T004 [US1] `src/collectors/rss_collector.py` 수정 — `_try_extract_hwpx` 제거 후 `_try_extract_content(article)` 으로 교체: `crawl_page` 호출 → web_text 우선 사용, 첨부파일 링크 HTML에서 탐지, 기존 `hwpx_parser.extract_hwpx_text` 으로 HWPX 추출

**Checkpoint**: `python -m src.cli collect --rss` 실행 시 본문이 RSS summary보다 길어야 함

---

## Phase 4: User Story 2 — 다양한 첨부파일 형식 텍스트 추출 (Priority: P2)

**Goal**: HWPX 외에 PDF, ODT 첨부파일 텍스트도 자동 추출. 형식 우선순위: HWPX > PDF > ODT. 라이브러리 미설치 시 graceful degradation.

**Independent Test**:
```bash
# PDF/ODT 첨부파일이 있는 기관(예: 공정거래위원회) 수집 후
python -c "
import json; from pathlib import Path
data = json.loads(Path('data/raw/rss/공정거래.json').read_text('utf-8'))
pdf_items = [a for a in data if a.get('file_info') and a['file_info']['name'].endswith('.pdf')]
print('PDF 추출 성공:', sum(1 for a in pdf_items if a['file_info']['parse_status']=='success'))
"
```

### Implementation for User Story 2

- [x] T005 [P] [US2] `src/collectors/doc_extractor.py` 신규 생성 — `extract_doc_text(url, file_name) -> tuple[str|None, str]` 구현: .hwpx→hwpx_parser 위임, .pdf→pymupdf(ImportError graceful), .odt→odfpy(ImportError graceful), .hwp→unsupported
- [x] T006 [US2] `src/collectors/rss_collector.py` 수정 — `_try_extract_content` 내부의 hwpx_parser 직접 호출을 `doc_extractor.extract_doc_text`로 교체. 우선순위 순서로 file_list 순회 (.hwpx→.pdf→.odt)

**Checkpoint**: PDF 첨부파일 있는 항목에서 `file_info.parse_status == "success"` 확인

---

## Phase 5: User Story 3 — RSS URL 업데이트 및 기관명 자동 식별 (Priority: P2)

**Goal**: 검증된 RSS URL로 7개 기관 수집 성공, `feed.feed.title`에서 기관명 자동 추출.

**Independent Test**:
```bash
python -m src.cli collect --rss
# 기대:
# 1. 7개 기관 모두 "신규 N건" 출력 (0건이면 URL 오류)
# 2. data/raw/rss/*.json의 source_name 필드에 "대한민국 정책브리핑" 미포함
python -c "
import json; from pathlib import Path
for f in Path('data/raw/rss').glob('*.json'):
    d = json.loads(f.read_text('utf-8'))
    names = {a['source_name'] for a in d}
    bad = [n for n in names if '정책브리핑' in n]
    if bad: print('WARNING:', f.stem, bad)
    else: print('OK:', f.stem, names)
"
```

### Implementation for User Story 3

- [x] T007 [US3] `src/collectors/rss_collector.py` 수정 — `collect_rss()` 내에서 `dept_name = feed.feed.title.replace("대한민국 정책브리핑", "").strip()` 추출 로직 추가. `_parse_feed_entry(entry, source_name, dept_name)` 시그니처 확장 후 `article.source_name = dept_name` 적용 (추출 실패 시 `source_name` fallback)

**Checkpoint**: 모든 기관에서 수집 성공 + source_name에 "정책브리핑" 접두어 없음

---

## Phase 6: Polish & Cross-Cutting

**Purpose**: 일관성, 안전성 마무리

- [x] T008 [P] `src/collectors/web_scraper.py` 및 `src/collectors/doc_extractor.py`에 User-Agent 헤더 적용 확인 (research.md Decision 6 — Chrome 122 UA, Session 방식)
- [ ] T009 전체 파이프라인 회귀 검증 — `python -m src.cli run-all` 실행하여 전처리→분석→평가→리포트까지 오류 없이 완료 확인 (SC-004 하위 호환성)

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
  └── T001 requirements.txt ──────────────────────────┐
  └── T002 config.yaml.example [P]                    │
                                                       ▼
Phase 3 (US1): T003 web_scraper.py → T004 rss_collector (US1)
                                          │
                                          ▼
Phase 4 (US2): T005 doc_extractor.py [P] → T006 rss_collector (US2)
                                          │
                                          ▼
Phase 5 (US3):              T007 rss_collector (US3)
                                          │
                                          ▼
Phase 6 (Polish): T008 [P]  T009
```

### User Story Dependencies

- **US1 (P1)**: T001 완료 후 즉시 시작 가능. 다른 스토리에 의존 없음
- **US2 (P2)**: T001 완료 후 시작 가능. T005는 T003과 병렬 가능. T006은 T004(US1 완료) 후 작업
- **US3 (P2)**: T002 이미 완료. T007은 rss_collector.py에서 독립적인 변경이나 T004, T006 이후 적용 권장 (충돌 방지)

### 핵심 순차 의존성 (rss_collector.py)

```
T004 (US1 web crawling) → T006 (US2 doc extractor 통합) → T007 (US3 dept_name)
```

rss_collector.py를 세 번 순서대로 수정. 각 변경 후 `collect --rss` 로 검증.

---

## Parallel Opportunities

### T003과 T005는 완전 병렬 가능

```
# 동시 작업 가능 (서로 다른 파일)
T003: src/collectors/web_scraper.py
T005: src/collectors/doc_extractor.py
```

### T001과 T002도 병렬 가능

```
T001: requirements.txt
T002: config.yaml.example
```

---

## Implementation Strategy

### MVP (User Story 1만 완성)

1. T001 — requirements.txt 업데이트
2. T003 — web_scraper.py 구현
3. T004 — rss_collector.py US1 변경
4. **STOP & VALIDATE**: `collect --rss` 실행, 본문 길이 3배+ 확인
5. MVP 완성 — 이미 분석 품질 크게 향상

### 전체 완성 (순서)

| 단계 | 태스크 | 예상 소요 |
|------|-------|---------|
| 1 | T001, T002 (병렬) | 10분 |
| 2 | T003, T005 (병렬) | 30~40분 |
| 3 | T004 | 20분 |
| 4 | T006 | 15분 |
| 5 | T007 | 10분 |
| 6 | T008, T009 | 15분 |

---

## Notes

- rss_collector.py는 3개 스토리 모두의 통합점 → 각 스토리 완료 후 즉시 `collect --rss` 로 검증
- doc_extractor.py는 ImportError를 조용히 처리 (pymupdf/odfpy 미설치 환경 대비)
- 기존 `hwpx_parser.py`는 건드리지 않음 (doc_extractor.py에서 위임 방식으로 재사용)
- Article, FileInfo 데이터 모델 변경 없음 — JSON 스키마 하위 호환 유지
