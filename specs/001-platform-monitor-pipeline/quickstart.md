# Quickstart: 플랫폼 산업 자동 모니터링 시스템

## 사전 요구사항

- Python 3.10 이상
- 인터넷 접속
- Naver 개발자 API 키 (Client ID / Secret)
- Google Gemini API 키

## 1. 설치

```bash
# 저장소 클론
git clone <repo-url>
cd news-platform-monitor

# 가상환경 생성 및 활성화
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

## 2. 설정

`config.yaml` 파일을 프로젝트 루트에 생성:

```yaml
# API 인증 정보
api:
  naver:
    client_id: "YOUR_NAVER_CLIENT_ID"
    client_secret: "YOUR_NAVER_CLIENT_SECRET"
  gemini:
    api_key: "YOUR_GEMINI_API_KEY"
    model: "gemini-2.5-flash-lite"

# RSS 피드 소스 (정책브리핑 korea.kr)
rss_sources:
  공정거래: "https://www.korea.kr/rss/policy.do?dept_id=138"
  소비자보호: "https://www.korea.kr/rss/policy.do?dept_id=145"
  개인정보: "https://www.korea.kr/rss/policy.do?dept_id=N04"
  노동: "https://www.korea.kr/rss/policy.do?dept_id=115"
  콘텐츠/저작권: "https://www.korea.kr/rss/policy.do?dept_id=113"
  안전: "https://www.korea.kr/rss/policy.do?dept_id=116"
  AI/자동화: "https://www.korea.kr/rss/policy.do?dept_id=122"

# 뉴스 검색 키워드
search_keywords:
  - "플랫폼 규제"
  - "공정거래"
  - "개인정보"
  - "플랫폼 노동"
  - "저작권"
  - "AI 규제"
  - "온라인 플랫폼법"
  - "배달앱 수수료"
  - "플랫폼 독과점"

# 리스크 평가 설정
risk:
  threshold: 70
  trending_ratio: 2.0
```

또는 환경 변수로 API 키를 관리:

```bash
export NAVER_CLIENT_ID="YOUR_NAVER_CLIENT_ID"
export NAVER_CLIENT_SECRET="YOUR_NAVER_CLIENT_SECRET"
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

## 3. 실행

각 파이프라인 단계를 독립적으로 실행:

```bash
# 1단계: 데이터 수집
python -m src.cli collect          # 보도자료 + 뉴스 전체 수집
python -m src.cli collect --rss    # 보도자료만 수집
python -m src.cli collect --news   # 뉴스만 수집

# 2단계: 전처리 (중복 제거, 태깅)
python -m src.cli preprocess

# 3단계: LLM 분석 (요약, 감성, 정책 분류)
python -m src.cli analyze

# 4단계: 리스크 평가
python -m src.cli score

# 5단계: 브리핑 리포트 생성
python -m src.cli report

# 전체 파이프라인 한 번에 실행
python -m src.cli run-all
```

## 4. 결과 확인

```
data/
├── reports/
│   ├── briefing_2026-03-31.md      # 주간 브리핑 (Markdown)
│   ├── briefing_2026-03-31.json    # 브리핑 데이터 (JSON)
│   └── heatmap_2026-03-31.png      # 리스크 히트맵 이미지
├── scored/
│   └── clusters.json               # 이슈 클러스터 + 리스크 점수
├── analyzed/
│   └── analyses.json               # LLM 분석 결과
└── processed/
    └── articles.json               # 전처리 완료 기사 통합
```

## 5. 검증

```bash
# 수집 데이터 확인
python -m src.cli status           # 수집 건수, 분석 상태 요약

# 특정 단계 재실행 (이전 결과 덮어쓰기)
python -m src.cli analyze --force  # 미분석 항목 재분석
```
