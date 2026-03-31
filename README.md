# 플랫폼 산업 자동 모니터링 시스템

KISDI 디지털플랫폼 정책포럼을 위한 뉴스·보도자료 자동 수집 및 LLM 기반 분석 시스템.

## 주요 기능

- 7개 정부 기관 보도자료 자동 수집 (RSS 피드)
- Naver 뉴스 기사 자동 수집 (정책 키워드 기반)
- Google Gemini API 기반 분석 (요약, 감성, 정책영역 분류)
- 리스크 스코어링 및 급상승 이슈 탐지
- 주간 브리핑 리포트 및 리스크 히트맵 자동 생성

## 설치

```bash
# Python 3.10 이상 필요
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

## 설정

```bash
cp config.yaml.example config.yaml
```

`config.yaml`에서 API 키를 설정하세요:

- **Naver API**: https://developers.naver.com 에서 애플리케이션 등록 후 Client ID/Secret 입력
- **Gemini API**: https://aistudio.google.com 에서 API 키 발급 후 입력

환경 변수로도 설정 가능:
```bash
export NAVER_CLIENT_ID="..."
export NAVER_CLIENT_SECRET="..."
export GEMINI_API_KEY="..."
```

## 사용법

```bash
# 개별 단계 실행
python -m src.cli collect          # 데이터 수집 (RSS + 뉴스)
python -m src.cli collect --rss    # RSS 보도자료만
python -m src.cli collect --news   # Naver 뉴스만
python -m src.cli preprocess       # 전처리 (중복 제거, 태깅)
python -m src.cli analyze          # LLM 분석
python -m src.cli score            # 리스크 스코어링
python -m src.cli report           # 브리핑 리포트 생성

# 전체 파이프라인 실행
python -m src.cli run-all

# 상태 확인
python -m src.cli status
```

## 결과물

실행 후 `data/reports/` 디렉토리에서 확인:

- `briefing_YYYY-MM-DD.md` — 주간 브리핑 (Markdown)
- `briefing_YYYY-MM-DD.json` — 브리핑 데이터 (JSON)
- `heatmap_YYYY-MM-DD.png` — 리스크 히트맵 이미지
