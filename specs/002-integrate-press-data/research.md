# Research: press_data.py RSS 수집 코드 통합

**Branch**: `002-integrate-press-data` | **Date**: 2026-04-05

## 조사 배경

press_data.py가 이미 작동하는 구현체이므로 기술 선택의 대부분은 이미 검증되어 있다. 연구의 초점은 (1) 기존 레포 구조와의 통합 방식, (2) 신규 패키지 선택 확인, (3) Windows 호환성 이슈 방지에 있다.

---

## Decision 1: HTML 파싱 라이브러리

**Decision**: `beautifulsoup4` (bs4) 사용, `lxml` 파서 대신 `html.parser` 기본 사용

**Rationale**:
- press_data.py에서 이미 검증됨
- `html.parser`는 Python stdlib 포함 — 추가 의존성 없음
- korea.kr 페이지는 표준 HTML이므로 lxml의 성능 이점 불필요
- Windows에서 lxml 바이너리 설치 이슈 회피

**Alternatives considered**:
- `lxml` — 더 빠르지만 Windows에서 바이너리 설치 필요, 해당 없음
- `html5lib` — 느리고 추가 패키지 필요, 해당 없음

---

## Decision 2: PDF 텍스트 추출 라이브러리

**Decision**: `pymupdf` 패키지 (import 시 `fitz`) 사용

**Rationale**:
- press_data.py에서 `fitz`로 검증됨 (`import fitz`)
- `pymupdf` 패키지명으로 pip install, Windows/macOS 모두 바이너리 제공
- 텍스트 추출 정확도 높음 (한국어 포함)
- 메모리 효율적 (스트리밍 처리 가능)

**Alternatives considered**:
- `pypdf2`/`pypdf` — 한국어 텍스트 추출 불안정, 사용 지양
- `pdfplumber` — 정확하지만 pymupdf보다 무거움
- `pdfminer.six` — 저수준 API, 코드량 많음

---

## Decision 3: ODT 텍스트 추출 라이브러리

**Decision**: `odfpy` 패키지 사용

**Rationale**:
- press_data.py에서 `from odf import text, teletype; from odf.opendocument import load`로 검증됨
- ODF 표준 구현체, 경량 패키지
- Windows 순수 Python 설치 가능 (바이너리 의존성 없음)

**Alternatives considered**:
- `python-docx` — DOCX 전용, ODT 미지원
- `libreoffice` CLI — 외부 프로그램 의존, 설치 복잡

---

## Decision 4: `web_scraper.py` 모듈 분리 여부

**Decision**: 별도 `src/collectors/web_scraper.py` 모듈로 분리

**Rationale**:
- `rss_collector.py`는 RSS 피드 파싱 책임만 가져야 함 (단일 책임 원칙)
- `web_scraper.py`는 HTTP 크롤링 + HTML 파싱 책임을 독립적으로 테스트 가능
- press_data.py의 `extract_web_text()`, `crawl_comprehensive_details()`가 자연스럽게 하나의 모듈로 묶임

**Alternatives considered**:
- `rss_collector.py`에 직접 통합 — 파일이 커지고 테스트 어려움
- `utils/` 에 배치 — collectors 작업이므로 `collectors/`가 적합

---

## Decision 5: `doc_extractor.py` vs `hwpx_parser.py` 확장

**Decision**: `doc_extractor.py` 신규 모듈 추가, `hwpx_parser.py` 유지

**Rationale**:
- `hwpx_parser.py`를 수정하면 기존 import path가 깨질 수 있음 (하위 호환성 위반)
- `doc_extractor.py`가 HWPX는 `hwpx_parser`에 위임하고 PDF/ODT를 직접 처리
- 새 모듈명이 역할을 더 명확히 표현 ("문서 추출기")
- `rss_collector.py`에서 import를 `doc_extractor`로 교체

**Alternatives considered**:
- `hwpx_parser.py` 직접 확장 — 하위 호환성 문제, 이름이 역할과 맞지 않음

---

## Decision 6: HTTP 요청 User-Agent 처리 방식

**Decision**: `requests.Session` 에 User-Agent 헤더를 설정하여 모듈 내에서 공유

**Rationale**:
- press_data.py의 `HEADERS` 딕셔너리 방식 대신 Session 재사용으로 성능 개선
- 코드 중복 없이 모든 요청에 일관된 헤더 적용
- 기존 `hwpx_parser.py`는 Session 미사용이므로 `doc_extractor.py`와 `web_scraper.py`에서 Session 사용

**User-Agent 값**: Chrome 122 UA (press_data.py에서 검증된 값)

---

## Decision 7: RSS URL 교체 범위

**Decision**: `config.yaml.example`의 `rss_sources` 값만 교체. 키(카테고리명) 유지

**Rationale**:
- 키(카테고리명)는 `source_name`의 fallback으로 사용됨 → 유지 필요
- 기존 `policy.do?dept_id=` 형식 URL이 실제로 동작하지 않는 경우를 대비해 `dept_xxx.xml` 형식으로 교체
- press_data.py에서 검증된 7개 URL 그대로 사용

**URL 매핑**:
| 카테고리 | 기존 URL | 신규 URL |
|---------|---------|---------|
| 공정거래 | `policy.do?dept_id=138` | `dept_ftc.xml` |
| 소비자보호 | `policy.do?dept_id=145` | `dept_mfds.xml` |
| 개인정보 | `policy.do?dept_id=N04` | `dept_pipc.xml` |
| 노동 | `policy.do?dept_id=115` | `dept_moel.xml` |
| 콘텐츠/저작권 | `policy.do?dept_id=113` | `dept_mcst.xml` |
| 안전 | `policy.do?dept_id=116` | `dept_mois.xml` |
| AI/자동화 | `policy.do?dept_id=122` | `dept_msit.xml` |

---

## Decision 8: ImportError graceful degradation

**Decision**: `doc_extractor.py`에서 pymupdf, odfpy를 try/except로 임포트, 라이브러리 없으면 해당 형식 건너뜀

**Rationale**:
- spec Assumption: 설치 실패 환경에서도 기존 동작 유지 필요
- `try: import fitz; _PDF_AVAILABLE = True except ImportError: _PDF_AVAILABLE = False` 패턴
- odfpy도 동일 패턴

**Impact**: requirements.txt에는 명시되어 있으나, 설치 실패 시에도 HWPX 추출은 정상 동작

---

## 결론

모든 기술 선택이 확정됨. NEEDS CLARIFICATION 없음. Phase 1 설계 진행 가능.

**신규 파일 목록**:
- `src/collectors/web_scraper.py`
- `src/collectors/doc_extractor.py`

**수정 파일 목록**:
- `src/collectors/rss_collector.py`
- `config.yaml.example`
- `requirements.txt`
