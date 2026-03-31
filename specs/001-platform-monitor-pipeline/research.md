# Research: 플랫폼 산업 자동 모니터링 파이프라인

**Date**: 2026-03-31
**Feature**: 001-platform-monitor-pipeline

## 1. RSS 피드 파싱 (feedparser)

- **Decision**: `feedparser` 라이브러리 사용
- **Rationale**: RSS 0.9x/1.0/2.0, Atom 등 모든 표준 피드 포맷 지원. korea.kr RSS 피드와 호환 확인됨. 경량 패키지로 Constitution V 원칙(Simplicity) 부합
- **Alternatives considered**:
  - `requests` + `xml.etree.ElementTree` 직접 파싱: 가능하나 날짜 파싱, 인코딩 처리 등 feedparser가 이미 해결한 문제를 다시 구현해야 함
- **Install**: `pip install feedparser`
- **Usage pattern**:
  ```python
  import feedparser
  d = feedparser.parse("https://www.korea.kr/rss/policy.do?dept_id=xxx")
  for entry in d.entries:
      title, link, published, summary = entry.title, entry.link, entry.published, entry.summary
  ```

## 2. HWPX 파일 텍스트 추출

- **Decision**: Python 표준 라이브러리(`zipfile` + `xml.etree.ElementTree`)로 직접 추출
- **Rationale**: HWPX는 ZIP 컨테이너 안에 XML 파일(OWPML, KS X 6101 표준)을 담고 있는 포맷. 텍스트만 추출하면 되므로 외부 라이브러리 없이 가능. Constitution V 원칙(Minimal Dependencies) 부합
- **Alternatives considered**:
  - `python-hwpx`: 전용 라이브러리지만 추가 의존성 발생
  - `pyhwp`: HWP v5 바이너리 포맷 전용, HWPX와 다름
  - `gethwp`: 경량이나 유지보수 불확실
- **Fallback**: 파싱 실패 시 RSS 본문 텍스트 사용 (Edge Case 대응)

## 3. Naver Search API

- **Decision**: `requests` 라이브러리로 REST API 직접 호출
- **Rationale**: 별도 SDK 없이 HTTP GET 요청으로 충분. 인증은 헤더에 Client ID/Secret 포함
- **Alternatives considered**: Naver 공식 SDK — 존재하지 않음 (REST API만 제공)
- **Key constraints**:
  - 일일 호출 한도: 25,000회
  - 한 번에 최대 100건, start 최대 1,000 → 키워드당 최대 1,000건
  - 정렬: `sort=date` (최신순)
- **Authentication**: `X-Naver-Client-Id`, `X-Naver-Client-Secret` 헤더
  - 발급: https://developers.naver.com → 애플리케이션 등록 → "검색" API 사용 설정

## 4. Google Gemini API

- **Decision**: `google-genai` SDK 사용, 모델은 `gemini-2.5-flash-lite` (경량)
- **Rationale**: 공식 SDK로 안정적. Flash-Lite 모델은 최저 비용으로 대량 기사 분석에 최적. Constitution V 원칙(비용 절감) 부합
- **Alternatives considered**:
  - `google-generativeai` (레거시): 2024-11-30 지원 종료
  - OpenAI API: 프로젝트 요구사항에서 Gemini 지정
- **Install**: `pip install google-genai`
- **Usage pattern**:
  ```python
  from google import genai
  client = genai.Client(api_key="YOUR_API_KEY")
  response = client.models.generate_content(
      model="gemini-2.5-flash-lite",
      contents="분석 프롬프트"
  )
  ```
- **Authentication**: Google AI Studio에서 API 키 발급

## 5. 히트맵 시각화

- **Decision**: `matplotlib` + `seaborn` 사용
- **Rationale**: Python 데이터 시각화 표준. 히트맵 생성에 최적화된 `seaborn.heatmap()` 제공. PNG 이미지 저장 용이
- **Alternatives considered**:
  - `plotly`: 인터랙티브하나 HTML 의존, 오버스펙
  - 텍스트 기반만: 시각적 효과 부족
- **Install**: `pip install matplotlib seaborn`

## 6. 키워드 기반 클러스터링

- **Decision**: LLM 추출 키워드의 문자열 일치 기반 그룹화
- **Rationale**: Clarification에서 결정됨. 키워드 일치/부분 일치로 기사를 그룹화하는 단순한 접근. 임베딩이나 LLM 추가 호출 불필요
- **Alternatives considered**:
  - TF-IDF + 코사인 유사도: 추가 복잡성
  - LLM 직접 클러스터링: API 비용 증가
  - 임베딩 벡터: 벡터 DB 필요, Constitution IV/V 위반

## 7. 데이터 저장 포맷

- **Decision**: JSON 파일 기반, 파이프라인 단계별 별도 디렉토리
- **Rationale**: Constitution V 원칙. 로컬 파일 시스템만 사용. 각 단계 결과를 독립 파일로 저장하여 재실행·디버깅 가능
- **Structure**:
  ```
  data/
  ├── raw/              # 수집 원본 (RSS, Naver API 응답)
  │   ├── rss/          # 기관별 보도자료
  │   └── news/         # Naver 뉴스 검색 결과
  ├── processed/        # 전처리 완료 (중복 제거, 통합)
  ├── analyzed/         # LLM 분석 결과
  ├── scored/           # 리스크 스코어링 결과
  └── reports/          # 브리핑 리포트, 히트맵 이미지
  ```

## 8. 설정 파일 구조

- **Decision**: YAML 설정 파일 (`config.yaml`)
- **Rationale**: JSON보다 가독성 좋고, 주석 지원. 키워드 목록, API 키, RSS URL 등을 한 곳에서 관리
- **Dependencies**: `pyyaml` 패키지
