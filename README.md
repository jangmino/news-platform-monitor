# 플랫폼 산업 자동 모니터링 시스템

KISDI 디지털플랫폼 정책포럼을 위한 뉴스·보도자료 자동 수집 및 LLM 기반 분석 시스템.

## 주요 기능

- 7개 정부 기관 보도자료 자동 수집 (RSS 피드)
- Naver 뉴스 기사 자동 수집 (정책 키워드 기반)
- Google Gemini API 기반 분석 (요약, 감성, 정책영역 분류, 리스크 점수)
- 보도자료/뉴스 통합 정책 제언 자동 생성
- 웹 대시보드를 통한 시각화 (플랫폼·키워드·시계열 필터링)

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
- **Gemini API**: 아래 가이드 참고
  - 운영 담당자(KISDI): [docs/gemini-api-setup.md](docs/gemini-api-setup.md) — 본인 키 발급 및 설정 절차
  - 개발자: [docs/dev-gemini-api-guide.md](docs/dev-gemini-api-guide.md) — 전달받은 개발용 키 사용 방법

환경 변수로도 설정 가능:
```bash
export NAVER_CLIENT_ID="..."
export NAVER_CLIENT_SECRET="..."
export GEMINI_API_KEY="..."
```

## 사용법

```bash
# 개별 단계 실행
python -m src.cli collect                    # 데이터 수집 (RSS + 뉴스)
python -m src.cli collect --rss              # RSS 보도자료만
python -m src.cli collect --news             # Naver 뉴스만
python -m src.cli preprocess                 # 전처리 (뉴스 중복 제거 + 태깅)
python -m src.cli analyze-press              # 보도자료 LLM 분석 + 정책 제언
python -m src.cli analyze-news               # 뉴스 LLM 분석
python -m src.cli generate-recommendations   # 통합 정책 제언 생성

# 전체 파이프라인 실행
python -m src.cli run-all

# 상태 확인
python -m src.cli status
```

## 결과물

실행 후 `data/analyzed/` 디렉토리에서 확인:

- `press_analysis.json` — 보도자료 분석 결과 (요약, 감성, 리스크, 정책 제언)
- `news_analysis.json` — 뉴스 분석 결과
- `combined_recommendations.json` — 보도자료+뉴스 통합 정책 제언

위 파일은 `dashboard/public/data/` 에 자동 복사되어 대시보드에서 시각화됩니다.

```bash
cd dashboard && npm install && npm run dev   # http://localhost:5173
```
