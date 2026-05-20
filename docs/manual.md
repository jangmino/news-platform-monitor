# 플랫폼 산업 모니터링 시스템 운영 매뉴얼

**작성일:** 2026-04-27
**대상 환경:** Windows 10/11 노트북, Python 3.10
**대상 독자:** KISDI 시스템 운영 담당자 (인수인계용)

---

## 목차

1. [시스템 개요](#1-시스템-개요)
2. [설치](#2-설치)
3. [API 키 발급](#3-api-키-발급)
4. [환경 설정 (config.yaml)](#4-환경-설정-configyaml)
5. [파이프라인 실행 (수집 → 분석)](#5-파이프라인-실행-수집--분석)
6. [대시보드 실행 및 사용](#6-대시보드-실행-및-사용)
7. [설정 커스터마이징](#7-설정-커스터마이징)
8. [일상 운영 / 트러블슈팅](#8-일상-운영--트러블슈팅)
9. [부록 A. 디렉토리 구조](#부록-a-디렉토리-구조)
10. [부록 B. CLI 명령어 빠른 참조](#부록-b-cli-명령어-빠른-참조)
11. [부록 C. 데이터 파일 스키마 요약](#부록-c-데이터-파일-스키마-요약)

---

## 1. 시스템 개요

### 1.1 시스템이 하는 일

**플랫폼 산업 모니터링 시스템**은 국내·외 디지털 플랫폼(네이버·카카오·쿠팡·구글·메타 등)을 둘러싼 정책·규제·여론 동향을 자동으로 수집·분석하여 정책 담당자에게 제공하는 도구입니다.

매일/매주 시스템을 실행하면 다음과 같은 일이 자동으로 수행됩니다.

1. 정부 부처(공정위·개보위·과기부 등) **보도자료 RSS 피드 수집**
2. **네이버 뉴스 API**로 7개 정책 영역(공정거래·소비자보호·개인정보·노동·콘텐츠/저작권·안전·AI/자동화)별 키워드 검색·수집
3. 중복 제거 + 정책영역·플랫폼·기관 자동 태깅 (전처리)
4. **Google Gemini AI**가 각 기사를 읽고 요약·감성·리스크 점수(0–100) 산출
5. 분석 결과를 바탕으로 **AI 정책 제언** 자동 생성
6. **웹 대시보드**로 결과 시각화 (히트맵, 트렌드, 키워드 클라우드, 플랫폼별 카드 등)

### 1.2 데이터 흐름

```
┌──────────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ 1. 수집       │ →  │ 2. 전처리 │ →  │ 3. 분석   │ →  │ 4. 제언   │ →  │ 5. 대시보드│
│ collect      │    │ preprocess│    │ analyze   │    │ generate  │    │ npm run   │
│              │    │           │    │ -press    │    │ -recom    │    │ dev       │
│ RSS+뉴스 API  │    │ 중복제거    │    │ Gemini    │    │ Gemini    │    │ 브라우저  │
│              │    │ 자동태깅   │    │ LLM       │    │ LLM       │    │ 시각화    │
└──────────────┘     └──────────┘     └──────────┘     └──────────┘     └──────────┘
       ↓                    ↓                ↓                ↓                  ↑
   data/raw/          data/processed/  data/analyzed/   data/analyzed/    dashboard/public/
   *.json             articles.json    *_analysis.json  combined_*.json   data/*.json
```

> 위 5단계 전체를 한 번에 실행하는 명령어는 `python -m src.cli run-all` 입니다 (5장 참조).

### 1.3 주요 산출물 위치

| 위치 | 내용 |
|------|------|
| `data/raw/rss/` | RSS 보도자료 원본 (수집 단위로 JSON) |
| `data/raw/news/` | 네이버 뉴스 검색 원본 |
| `data/processed/articles.json` | 중복 제거·태깅 완료된 통합 기사 목록 |
| `data/analyzed/press_analysis.json` | 보도자료 LLM 분석 결과 |
| `data/analyzed/news_analysis.json` | 뉴스 LLM 분석 결과 |
| `data/analyzed/combined_recommendations.json` | 통합 정책 제언 |
| `dashboard/public/data/*.json` | 위 분석 JSON의 대시보드용 사본 (자동 복사) |

### 1.4 시스템 구성 요소

| 구성 요소 | 기술 | 역할 |
|-----------|------|------|
| 백엔드 파이프라인 | Python 3.10 | 수집·전처리·LLM 분석·제언 생성 |
| 외부 API ① | 네이버 검색 API | 뉴스 수집 (일 25,000회 무료) |
| 외부 API ② | Google Gemini API | 기사 요약·리스크 평가·정책 제언 |
| 프론트엔드 | Node.js + React | 대시보드 시각화 (로컬 브라우저) |

> 본 시스템은 **개인 노트북에서 로컬 실행**을 전제로 합니다. 별도 서버나 클라우드는 필요하지 않습니다.

---

## 2. 설치

이 장은 Windows 10/11 노트북에 시스템을 처음 설치하는 절차입니다. **최초 1회만** 수행합니다.

### 2.1 설치 전 체크리스트

- [ ] Windows 10 (1809 이상) 또는 Windows 11
- [ ] 디스크 여유 공간 2 GB 이상
- [ ] 인터넷 접속 가능
- [ ] 관리자 권한 (소프트웨어 설치 시 필요)

---

### 2.2 Python 3.10 설치

> 본 시스템은 **Python 3.10**을 기준으로 작성되어 있습니다. 3.11/3.12에서도 대체로 동작하나, 인수인계 환경 일치를 위해 **3.10을 권장**합니다.

#### 단계

1. 브라우저에서 다음 주소로 이동합니다.
   **https://www.python.org/downloads/windows/**

2. 페이지를 아래로 스크롤하여 "Python 3.10.x" 항목을 찾습니다 (예: 3.10.11).

3. **"Windows installer (64-bit)"** 링크(`.exe`)를 클릭하여 다운로드합니다.

4. 다운로드한 `python-3.10.x-amd64.exe` 를 더블클릭하여 설치를 시작합니다.

5. 설치 첫 화면에서 **반드시 다음 두 항목을 체크**합니다.
   - ☑ **Add python.exe to PATH** (가장 중요)
   - ☑ Install for all users (선택)

6. **"Install Now"** 클릭 → 설치가 완료될 때까지 대기.

7. 설치 완료 후 **명령 프롬프트**(시작 메뉴 → "cmd" 입력 → Enter)를 새로 열고 다음을 입력합니다.

   ```bat
   python --version
   ```

   `Python 3.10.x` 가 출력되면 정상입니다.

> **`python` 명령이 인식되지 않는 경우:** 설치 시 "Add to PATH"를 체크하지 않은 것입니다. Python을 다시 설치하거나, 시작 메뉴에서 "환경 변수" 검색 → 시스템 환경 변수 → Path 에 `C:\Users\<사용자>\AppData\Local\Programs\Python\Python310\` 와 `...\Python310\Scripts\` 두 경로를 추가합니다.

> [스크린샷: Python 설치 첫 화면 — "Add python.exe to PATH" 체크박스 강조]

---

### 2.3 Node.js LTS 설치

대시보드 실행에 필요합니다.

#### 단계

1. **https://nodejs.org** 접속.
2. **"LTS"** 라고 표시된 좌측 큰 버튼(`.msi` 설치 파일)을 클릭하여 다운로드합니다 (예: 20.x LTS).
3. 다운로드한 `node-v20.x.x-x64.msi` 를 더블클릭하여 설치합니다. 모든 옵션은 기본값으로 두고 "Next" 를 계속 누릅니다.
4. 설치 완료 후 **명령 프롬프트를 새로 열어** 다음을 확인합니다.

   ```bat
   node -v
   npm -v
   ```

   각각 `v20.x.x`, `10.x.x` 형태로 출력되면 정상입니다.

> 명령 프롬프트는 **반드시 Node.js 설치 후 새로 열어야** PATH 변경이 반영됩니다.

---

### 2.4 프로젝트 폴더 준비

#### Option A — 압축 파일을 받은 경우

1. 인수인계 받은 `news-platform-monitor.zip` 파일을 원하는 위치(예: `C:\Users\<사용자>\Documents\`)에 압축 해제합니다.

2. 압축 해제 결과 폴더 경로 예시:
   `C:\Users\<사용자>\Documents\news-platform-monitor\`

#### Option B — Git으로 받는 경우 (선택)

Git이 설치되어 있다면:

```bat
cd C:\Users\<사용자>\Documents
git clone <저장소 URL> news-platform-monitor
```

---

### 2.5 가상환경 생성 및 패키지 설치

명령 프롬프트를 열고 프로젝트 폴더로 이동합니다.

```bat
cd C:\Users\<사용자>\Documents\news-platform-monitor
```

가상환경(virtual environment)을 생성합니다. 가상환경이란 이 프로젝트에만 적용되는 별도의 Python 패키지 공간으로, 다른 프로그램과의 충돌을 막아줍니다.

```bat
python -m venv venv
```

가상환경을 활성화합니다.

```bat
venv\Scripts\activate.bat
```

성공하면 프롬프트 앞에 `(venv)` 표시가 붙습니다.

```
(venv) C:\Users\...\news-platform-monitor>
```

> **PowerShell을 사용하는 경우**: `venv\Scripts\Activate.ps1` 로 활성화합니다. "스크립트 실행이 차단되었습니다" 오류가 나면 PowerShell을 **관리자 권한**으로 다시 열고 한 번만 다음 명령을 실행합니다.
>
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

이제 의존 패키지를 설치합니다 (인터넷 필요, 1~2분 소요).

```bat
pip install -r requirements.txt
```

설치되는 주요 패키지:
- `feedparser`, `requests`, `beautifulsoup4` — 수집
- `pymupdf`, `odfpy` — 보도자료 첨부 PDF/ODF 파싱
- `google-genai` — Gemini API 클라이언트
- `pyyaml` — 설정 파일 처리

---

### 2.6 대시보드 패키지 설치

같은 명령 프롬프트에서 (또는 새 창에서) 대시보드 폴더로 이동합니다.

```bat
cd dashboard
npm install
```

1~3분 소요됩니다. 진행 중 노란색 경고 문구가 나오는 것은 정상입니다 (오류만 아니면 무시).

설치 후 프로젝트 루트로 돌아옵니다.

```bat
cd ..
```

---

### 2.7 설치 확인 체크리스트

명령 프롬프트에서 다음을 모두 확인합니다.

| 명령 | 기대 출력 |
|------|-----------|
| `python --version` | `Python 3.10.x` |
| `node -v` | `v20.x.x` (또는 18 이상) |
| `npm -v` | `10.x.x` (또는 9 이상) |
| (`venv` 활성 후) `pip list` | feedparser, google-genai, pyyaml 등 표시 |
| `dir dashboard\node_modules` | 수많은 폴더 표시 (없으면 `npm install` 누락) |

모두 정상이면 설치가 완료된 것입니다. 다음으로 API 키를 발급받습니다.

---

## 3. API 키 발급

본 시스템은 **2개의 외부 API**를 사용합니다. 각각 별도의 키 발급이 필요합니다.

| API | 용도 | 비용 |
|-----|------|------|
| **네이버 검색 API** | 뉴스 수집 | 무료 (일 25,000회) |
| **Google Gemini API** | LLM 분석·정책 제언 | 무료 티어 + 초과 시 본인 계정 청구 |

> **중요**: 두 API 키 모두 **운영 담당자 본인 명의로 발급**해야 합니다. 사용량과 비용이 키 발급자 계정에 귀속됩니다.

---

### 3.1 네이버 검색 API 키 발급

#### Step 1 — 네이버 개발자 센터 가입

1. 브라우저에서 **https://developers.naver.com** 접속.
2. 우측 상단 **로그인** → 본인 네이버 계정으로 로그인.
   - 네이버 계정이 없으면 먼저 **https://nid.naver.com** 에서 가입.
3. 로그인 후 한 번도 개발자 센터를 사용한 적이 없다면, "이용 약관 동의" 화면이 나옵니다. 모두 동의하고 **확인**.

#### Step 2 — 애플리케이션 등록

1. 상단 메뉴 **Application → 애플리케이션 등록** 클릭.

   직접 URL: **https://developers.naver.com/apps/#/register**

2. 입력 항목:

   | 항목 | 입력값 |
   |------|--------|
   | 애플리케이션 이름 | `KISDI 플랫폼 모니터링` (자유롭게) |
   | 사용 API | **검색** 항목만 체크 |
   | 비로그인 오픈 API 서비스 환경 | **WEB 설정** 선택 |
   | 웹 서비스 URL | `http://localhost` 입력 |

3. 페이지 하단 **등록하기** 버튼 클릭.

> [스크린샷: 네이버 개발자센터 애플리케이션 등록 화면 — "검색" 체크박스 + "WEB 설정" + URL]

#### Step 3 — Client ID / Client Secret 확인

등록 직후 표시되는 화면 또는 좌측 메뉴 **내 애플리케이션 → (방금 등록한 앱)** 클릭 시 다음이 표시됩니다.

```
Client ID:     XXXXXXXXXXXXXXXXXXXX     (20자리 영숫자)
Client Secret: XXXXXXXXXX               (10자리 영숫자, "보기" 버튼 클릭하여 노출)
```

이 두 값을 **메모장이나 안전한 곳에 임시로 복사**해 둡니다. 4장에서 `config.yaml` 에 입력합니다.

> ⚠️ Client Secret 은 비밀번호와 동일하게 취급해야 합니다. 외부에 노출되면 즉시 재발급(휴지통 → 새 앱 등록)하세요.

#### Step 4 — 일일 호출 한도

- 검색 API는 기본적으로 **하루 25,000회 호출 무료**입니다.
- 본 시스템은 일반 운영 시 1회 실행에 약 200~500회를 사용하므로 한도를 초과할 가능성은 낮습니다.
- 사용량은 **내 애플리케이션 → 일일/월간 사용량** 메뉴에서 확인할 수 있습니다.

---

### 3.2 Google Gemini API 키 발급

#### Step 1 — Google AI Studio 접속

1. 브라우저에서 **https://aistudio.google.com** 접속.
2. **운영에 사용할 Google 계정**으로 로그인합니다.

> 조직(Workspace) 계정은 정책상 일부 기능이 제한될 수 있습니다. 제한이 있으면 개인 Gmail 계정 사용을 권장합니다.

#### Step 2 — API 키 생성

1. 좌측 사이드바 또는 우측 상단의 **"Get API key"** 버튼 클릭.
2. **"Create API key"** 버튼 클릭.
3. 팝업에서 **"Create API key in new project"** 선택 (Google Cloud 프로젝트가 자동 생성됨).
4. 키가 생성되면 화면에 **`AIzaSy...` 로 시작하는 39자 정도의 문자열**이 표시됩니다. 즉시 **복사**하여 안전한 곳에 보관합니다.

> [스크린샷: Google AI Studio "Get API key" → "Create API key" 버튼 위치]

#### Step 3 — 비용 안내

- `gemini-2.5-flash-lite` 모델은 **무료 티어** 한도 내에서 사용 가능합니다.
- 한도(분당/일별 호출량)는 시기에 따라 변동되므로 다음에서 확인:
  **https://ai.google.dev/pricing**
- 무료 한도를 초과해도 결제 수단이 등록되어 있지 않으면 호출이 거부될 뿐 자동 청구되지는 않습니다.

#### Step 4 — 키 보관 원칙

- ✅ `config.yaml`은 git에 커밋되지 않도록 `.gitignore`에 등록되어 있습니다 (변경 금지).
- ✅ API 키를 코드, 주석, 채팅, 이메일 등에 절대 노출하지 마세요.
- ✅ 키 노출이 의심되면 즉시 Google AI Studio에서 키를 **Delete** 후 재발급.
- ✅ 정기적으로(예: 6개월마다) 키를 재발급.

---

### 3.3 발급한 키 정리

이 시점에 **3개의 비밀 문자열**을 보유하고 있어야 합니다.

| 항목 | 형식 예시 | 발급처 |
|------|-----------|--------|
| 네이버 Client ID | `aBcDeFgHiJkLmNoP1234` | developers.naver.com |
| 네이버 Client Secret | `XyZ12345aB` | developers.naver.com |
| Gemini API Key | `AIzaSy...` (약 39자) | aistudio.google.com |

이 세 값을 다음 장에서 `config.yaml` 에 입력합니다.

---

## 4. 환경 설정 (config.yaml)

### 4.1 config.yaml 파일 만들기

명령 프롬프트에서 프로젝트 루트로 이동하여 예시 파일을 복사합니다.

```bat
cd C:\Users\<사용자>\Documents\news-platform-monitor
copy config.yaml.example config.yaml
```

`config.yaml` 파일이 생성됩니다.

### 4.2 텍스트 편집기로 열기

다음 중 편한 방법으로 `config.yaml` 을 엽니다.

- **메모장**: 파일 탐색기에서 `config.yaml` 우클릭 → **연결 프로그램** → **메모장**.
- **VS Code** (추천, 색상 표시 지원): 설치되어 있다면 명령 프롬프트에서 `code config.yaml`.
- **메모장++ (Notepad++)** 등 다른 편집기도 가능.

> ⚠️ MS Word나 한글(HWP)로는 절대 열지 마세요. 인코딩이 깨집니다.

### 4.3 API 키 입력

파일 상단의 `api:` 섹션을 찾아 3.3에서 발급받은 키 세 개를 따옴표 안에 입력합니다.

**수정 전 (예시 파일 그대로):**

```yaml
api:
  naver:
    client_id: "YOUR_NAVER_CLIENT_ID"
    client_secret: "YOUR_NAVER_CLIENT_SECRET"
  gemini:
    api_key: "YOUR_GEMINI_API_KEY"
    model: "gemini-2.5-flash-lite"
```

**수정 후 (실제 키로 교체):**

```yaml
api:
  naver:
    client_id: "aBcDeFgHiJkLmNoP1234"
    client_secret: "XyZ12345aB"
  gemini:
    api_key: "AIzaSy실제발급받은키전체문자열"
    model: "gemini-2.5-flash-lite"
```

저장 후 닫습니다.

> ⚠️ **주의사항**
> - 큰따옴표(`"`)를 지우지 마세요.
> - 들여쓰기는 **공백 2칸** 입니다 (탭 사용 금지).
> - `model` 값(`gemini-2.5-flash-lite`)은 비용 절감을 위한 경량 모델입니다 — **변경하지 마세요**.

### 4.4 (선택) 환경 변수 방식

`config.yaml` 에 키를 직접 적지 않고 Windows 환경 변수로 관리하는 방법입니다. 보안상 더 안전합니다.

PowerShell 에서 한 번만 실행 (영구 적용):

```powershell
[System.Environment]::SetEnvironmentVariable('NAVER_CLIENT_ID', '발급받은_ID', 'User')
[System.Environment]::SetEnvironmentVariable('NAVER_CLIENT_SECRET', '발급받은_Secret', 'User')
[System.Environment]::SetEnvironmentVariable('GEMINI_API_KEY', 'AIzaSy발급받은_키', 'User')
```

설정 후 **명령 프롬프트를 모두 닫고 새로 열어야** 적용됩니다.

> 환경 변수가 설정되어 있으면 `config.yaml` 의 값보다 우선 적용됩니다. 환경 변수 사용 시 `config.yaml` 은 placeholder 그대로 두어도 무방합니다.

### 4.5 동작 확인

가상환경이 활성화된 상태에서 다음 명령으로 두 API 키가 모두 정상 동작하는지 확인합니다.

```bat
venv\Scripts\activate.bat

python -c "from src.config import load_config; c = load_config(); print('Naver ID:', c['api']['naver']['client_id'][:6] + '...'); print('Gemini key:', c['api']['gemini']['api_key'][:6] + '...')"
```

다음과 같이 키 앞 6자가 출력되면 설정이 인식된 것입니다.

```
Naver ID:  aBcDeF...
Gemini key: AIzaSy...
```

이어서 Gemini API에 실제로 호출하여 응답을 받아봅니다.

```bat
python -c "from google import genai; from src.config import load_config; c = load_config(); client = genai.Client(api_key=c['api']['gemini']['api_key']); r = client.models.generate_content(model='gemini-2.5-flash-lite', contents='한 문장으로 인사해줘.'); print(r.text)"
```

한국어 인사말이 출력되면 정상입니다.

오류가 나는 경우:
- `Invalid API key` → 키 문자열을 잘못 복사했거나 따옴표를 빠뜨린 경우. `config.yaml` 다시 확인.
- `Quota exceeded` → 무료 한도 초과. 잠시 후 재시도하거나 결제 활성화.
- `Permission denied` → 조직 계정 정책으로 차단. 개인 Gmail 사용 권장.

---

## 5. 파이프라인 실행 (수집 → 분석)

이 장은 시스템을 운영하면서 **반복적으로 수행하는 일상 작업**입니다.

### 5.1 가상환경 활성화

명령 프롬프트(또는 PowerShell)를 새로 열 때마다 가상환경을 먼저 활성화해야 합니다.

```bat
cd C:\Users\<사용자>\Documents\news-platform-monitor
venv\Scripts\activate.bat
```

(PowerShell의 경우: `venv\Scripts\Activate.ps1`)

프롬프트에 `(venv)` 가 표시되어야 정상입니다.

---

### 5.2 [방법 A] 한 번에 실행 (권장)

전체 파이프라인을 한 줄로 실행:

```bat
python -m src.cli run-all
```

내부적으로 다음 5단계가 순차 실행됩니다.

1. RSS 보도자료 수집
2. 네이버 뉴스 수집
3. 전처리 (중복 제거 + 자동 태깅)
4. 보도자료 LLM 분석
5. 뉴스 LLM 분석
6. 통합 정책 제언 생성

소요 시간은 데이터량과 네트워크 상태에 따라 **5~30분**입니다 (Gemini API 호출이 가장 오래 걸림).

#### 진행 중 화면 예시

```
========== 전체 파이프라인 실행 ==========

=== RSS 보도자료 수집 ===
[공정거래] 25건 수집
[소비자보호] 18건 수집
...
=== Naver 뉴스 수집 ===
[공정거래] '자사우대' 100건
[공정거래] '수수료' 100건
...
=== 전처리 ===
중복 제거 후 542건
=== 보도자료 LLM 분석 ===
[1/87] 분석 중...
[2/87] 분석 중...
...
=== AI 정책 제언 생성 ===
정책 제언 6개 생성
========== 파이프라인 완료 ==========
```

> 중간에 일부 호출이 실패해도(503/429) 시스템이 자동으로 재시도하므로 그대로 두면 됩니다. 화면이 멈춘 듯 보여도 정상이니 **Ctrl+C로 끊지 마세요**.

---

### 5.3 [방법 B] 단계별 개별 실행

문제 진단이나 부분 재실행이 필요할 때 사용합니다.

```bat
python -m src.cli collect --rss            :: 1. RSS 보도자료만 수집
python -m src.cli collect --news           :: 2. 네이버 뉴스만 수집
python -m src.cli preprocess               :: 3. 전처리

python -m src.cli analyze-press            :: 4. 보도자료 LLM 분석 + 정책 제언
python -m src.cli analyze-news             :: 5. 뉴스 LLM 분석

python -m src.cli generate-recommendations :: 6. 통합 정책 제언 생성
```

> 인자 없이 `python -m src.cli collect` 를 실행하면 RSS와 뉴스를 모두 수집합니다.

#### `--force` 옵션

분석 명령은 기본적으로 **이미 분석된 항목은 건너뜁니다** (재호출 비용 절감). 강제로 다시 분석하려면:

```bat
python -m src.cli analyze-press --force
python -m src.cli analyze-news --force
python -m src.cli generate-recommendations --force
```

---

### 5.4 상태 확인

언제든 다음 명령으로 시스템 현황을 확인할 수 있습니다.

```bat
python -m src.cli status
```

출력 예시:

```
=== 시스템 상태 ===
수집  : RSS 878건 (1 파일), 뉴스 1317건 (37 파일)
전처리: 뉴스 247건 (중복 제거 후, 보도자료는 전처리 우회)

[보도자료 분석]
  총 878건 · analyzed 878건
  정책 제언 3개 · 생성 2026-05-20 14:38:03

[뉴스 분석]
  총 247건 · analyzed 247건
  생성 2026-05-20 14:51:22

[통합 정책 제언]
  3개 · 생성 2026-05-20 07:44:09
```

> **참고**: 보도자료(RSS)는 전처리 단계(`processed/articles.json`)를 거치지 않고 `raw/rss/press_data.json`에서 바로 분석됩니다. 따라서 전처리 건수는 뉴스만 집계됩니다.

---

### 5.5 산출물 위치

실행이 완료되면 다음 위치에 결과 파일이 저장됩니다.

| 경로 | 내용 |
|------|------|
| `data\raw\rss\` | 수집된 RSS 보도자료 원본 |
| `data\raw\news\` | 수집된 네이버 뉴스 원본 |
| `data\processed\articles.json` | 통합·중복제거·태깅 완료 |
| `data\analyzed\press_analysis.json` | 보도자료 LLM 분석 결과 |
| `data\analyzed\news_analysis.json` | 뉴스 LLM 분석 결과 |
| `data\analyzed\combined_recommendations.json` | 통합 정책 제언 |
| `dashboard\public\data\` | 위 분석 JSON 3종이 자동 복사됨 |

대시보드는 `dashboard\public\data\` 의 파일을 읽어 화면을 그립니다. 즉, 백엔드 실행 → 대시보드 새로고침 순서로 데이터가 갱신됩니다.

---

## 6. 대시보드 실행 및 사용

### 6.1 대시보드 실행

**새 명령 프롬프트**를 열고 (백엔드와 별도 창 권장) `dashboard` 폴더로 이동합니다.

```bat
cd C:\Users\<사용자>\Documents\news-platform-monitor\dashboard
npm run dev
```

다음과 같은 메시지가 표시되면 성공입니다.

```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

브라우저에서 **http://localhost:5173** 을 열면 대시보드가 표시됩니다.

> 대시보드를 종료하려면 명령 프롬프트에서 **Ctrl + C**를 누릅니다.
> 다음에 다시 실행할 때는 `npm install` 없이 `npm run dev` 만 입력하면 됩니다.

---

### 6.2 데이터 갱신 절차

대시보드는 실행 시점의 JSON 파일을 읽어 표시합니다. 백엔드 파이프라인을 다시 실행한 뒤에는 **브라우저를 새로고침(F5)** 하면 최신 데이터가 반영됩니다.

전체 갱신 흐름:

```
1. 백엔드 명령 창에서  python -m src.cli run-all  실행 (~10~30분)
2. 완료 메시지 확인
3. 브라우저에서 F5 새로고침
4. 대시보드 우측 상단의 "분석 건수" 가 갱신되었는지 확인
```

---

### 6.3 리스크 스코어란

리스크 스코어는 **각 기사가 플랫폼 규제·정책 환경에 미치는 위험 수준**을 0–100점으로 수치화한 값입니다. Gemini AI가 기사 원문을 읽고 다음 기준으로 산출합니다.

| 점수 범위 | AI 산출 기준 | 예시 상황 |
|-----------|------|-----------|
| 0 – 30 | 중립적 정보 제공, 정책 발표 | 새 서비스 출시 보도, 제도 안내 |
| 31 – 60 | 규제 논의, 제도 개선, 조사 착수 | 국회 입법 논의, 공정위 실태조사 |
| 61 – 80 | 과징금·처분·갈등 본격화 | 공정위 과징금 부과, 방통위 시정명령 |
| 81 – 100 | 심각한 법적 제재, 긴급 규제, 소비자 피해 | 검찰 수사, 영업정지, 대규모 피해 |

> **대시보드 표시 기준선은 70점**입니다. AI는 위 4구간(30/60/80) 기준으로 점수를 산출하지만, 대시보드 UI는 별도로 70점을 임계값으로 삼아 빨간 배지·히트맵 강조·랭킹 기준선을 표시합니다.

---

### 6.4 대시보드 화면 구성

대시보드는 4개 섹션으로 구성됩니다.

#### 공통 UI 요소 (화면 상단)

| 요소 | 설명 |
|------|------|
| **날짜 범위 필터** | 두 방식 제공. ① 프리셋 버튼 "전체 / 최근 7일 / 30일 / 90일" — 기준점은 **데이터의 가장 최근 일자** (오늘이 아님). ② 시작일·종료일 직접 입력 — 임의 구간 지정 가능. 모든 섹션이 동시에 갱신됨. 선택 기간에 데이터가 없으면 "전체 기간으로 보기" 버튼이 표시됨 |
| **분석 진행률** | `N/N건 분석` 표시. 두 숫자가 다르면 미분석 항목 존재 (`analyze-press`/`analyze-news` 재실행) |

#### 섹션 1 — 개요 (Overview)

전반 현황 요약 섹션입니다.

- **요약 카드 4개**: 전체 보도자료, 분석 완료, 평균 리스크, 고위험 이슈(70점 이상)
- **정책영역별 기사 수** (막대 차트): 7개 정책영역 분포
- **감성 분포** (도넛 차트): 긍정(초록) / 부정(빨강) / 중립(회색)
- **리스크 히트맵** (플랫폼 × 정책영역): 셀 색상 농도 = 평균 리스크. 행 클릭 시 섹션 4가 해당 플랫폼으로 필터링됨

#### 섹션 2 — 이슈 트렌드

시간 흐름에 따른 이슈 변화 추적.

- **일별 보도자료 수** (선 그래프): 특정 날짜 급증 시 주요 사건 발생 가능성
- **키워드별 리스크 랭킹**: LLM(Gemini)이 기사별로 추출한 키워드를 그룹 키로 묶어, 키워드별 평균 리스크 점수와 출현 빈도를 집계한 결과 (평균 리스크 상위 5개 표시). 빨간 점선이 70점 기준선

> ⚠️ **명명 주의**: 본 차트는 K-means·임베딩 유사도 등 비지도 클러스터링 알고리즘을 적용한 결과가 아니라, **LLM 추출 키워드를 그룹 키로 사용한 단순 집계(group-by)** 입니다. 동일 사건을 다룬 기사들을 묶는 의미 기반 클러스터링은 적용되지 않았으며, 한 기사가 여러 키워드에 동시 카운트될 수 있습니다.

#### 섹션 3 — 키워드 & 이슈 목록

- **키워드 태그 클라우드**: 상위 30개 키워드. 글자 크기 = 빈도, 색상 = 정책영역. **클릭 시 하단 이슈 목록이 해당 키워드로 필터링**됨
- **이슈 목록** (테이블): 날짜·출처(보도자료/뉴스)·제목·리스크·감성·정책영역. 기본 정렬 = 리스크 높은 순. 제목 클릭 시 원문 링크로 이동

#### 섹션 4 — 플랫폼 분석 & AI 정책 제언

- **플랫폼별 감성 분포** (수평 누적 막대): 상위 7개 플랫폼의 부정/중립/긍정 비율
- **플랫폼별 이슈 카드**: 국내(13개)·해외(12개)·기타. 카드별로 리스크 배지(고위험 ≥70 / 주의 50-69 / 관심 <50), 기사 수, 최고 리스크, 키워드 5개, 최고 리스크 기사 요약
- **AI 정책 제언 카드**: Gemini가 생성한 정책 대응 방향. 제목 + 본문(배경·근거·구체 조치)

> AI 정책 제언은 분석 결과를 바탕으로 자동 생성되며, **참고 자료로만 활용하고 반드시 전문가 검토**를 거쳐야 합니다.

---

### 6.5 색상 코드 체계

#### 리스크 수준

| 색상 | 범위 | 의미 |
|------|------|------|
| 빨강 | 70 – 100 | **고위험**: 즉각적인 정책 대응 또는 모니터링 강화 |
| 주황 | 50 – 69 | **주의**: 지속적인 관찰 및 대응 준비 |
| 파랑/회색 | 0 – 49 | **관심**: 현황 파악 수준 모니터링 |

#### 정책 영역

| 색상 | 영역 | 색상 | 영역 |
|------|------|------|------|
| 파랑 | 공정거래 | 핑크 | 콘텐츠/저작권 |
| 초록 | 소비자보호 | 빨강 | 안전 |
| 보라 | 개인정보 | 하늘색 | AI/자동화 |
| 황색 | 노동 | 회색 | 기타 |

#### 감성 / 출처

| 색상 | 감성 |   | 색상 | 출처 |
|------|------|---|------|------|
| 초록 | 긍정 |   | 파랑 배지 | 보도자료 (정부 RSS) |
| 빨강 | 부정 |   | 초록 배지 | 뉴스 (네이버 API) |
| 회색 | 중립 |   |   |   |

---

## 7. 설정 커스터마이징

`config.yaml` 을 편집하면 수집 대상·분석 기준을 자유롭게 조정할 수 있습니다. **편집 후에는 가상환경에서 파이프라인을 다시 실행**해야 변경 사항이 반영됩니다.

> 변경 전에는 항상 `config.yaml` 을 `config.yaml.bak` 등으로 백업해두세요.

---

### 7.1 RSS 피드 추가/교체

`rss_sources:` 섹션에서 정부 부처별 RSS URL을 관리합니다.

```yaml
rss_sources:
  공정거래: "https://www.korea.kr/rss/dept_ftc.xml"
  소비자보호: "https://www.korea.kr/rss/dept_mfds.xml"
  ...
  AI/자동화: "https://www.korea.kr/rss/dept_msit.xml"
```

#### 새 부처 추가 예시 (방통위 추가)

정책브리핑(korea.kr)의 부처별 RSS 주소를 찾아 추가합니다.

```yaml
rss_sources:
  공정거래: "https://www.korea.kr/rss/dept_ftc.xml"
  ...
  방송통신: "https://www.korea.kr/rss/dept_kcc.xml"   # 신규 추가
```

> 키 이름(예: `방송통신`)은 자유롭게 정할 수 있으나, **`policy_domains` 목록과 일치시키면** 분석 시 자동 매핑됩니다 (7.4 참조).

#### 활성/비활성 토글

특정 피드를 일시적으로 비활성화하려면 줄 앞에 `#` 을 추가하여 주석 처리합니다.

```yaml
rss_sources:
  공정거래: "https://www.korea.kr/rss/dept_ftc.xml"
  # 소비자보호: "https://www.korea.kr/rss/dept_mfds.xml"   # 일시 비활성화
```

---

### 7.2 뉴스 검색 키워드 수정

`news_query_categories:` 섹션에서 정책영역별 검색 키워드를 관리합니다. 각 키워드마다 네이버 검색 API를 별도 호출하므로 키워드가 늘어나면 호출량과 분석 비용이 증가합니다.

```yaml
news_query_categories:
  공정거래:
    - "자사우대"
    - "수수료"
    - "독점"
    - "공정거래"
    - "온라인플랫폼공정화법"
    - "플랫폼 규제"
```

#### 키워드 추가 예시

```yaml
news_query_categories:
  공정거래:
    - "자사우대"
    - "수수료"
    - "독점"
    - "공정거래"
    - "온라인플랫폼공정화법"
    - "플랫폼 규제"
    - "끼워팔기"          # 신규 추가
    - "MFN 조항"          # 신규 추가
```

#### 키워드 작성 팁

- **너무 일반적인 단어 지양**: `"AI"` 같이 너무 광범위한 키워드는 무관한 기사가 많이 수집됨. 가능하면 `"생성형 AI 규제"` 등으로 구체화.
- **공백 포함 가능**: `"플랫폼 규제"` 처럼 공백이 들어간 구문도 가능. 따옴표 안에 그대로 입력.
- **개수**: 영역당 5~10개를 권장. 영역당 100건씩 수집되므로 너무 많아지면 노이즈 증가.

---

### 7.3 플랫폼/기관 사전 추가

`platforms:` 와 `institutions:` 섹션은 LLM 분석 시 기사 본문에서 플랫폼·기관명을 인식하는 사전입니다. 신규 플랫폼이 등장하면 추가합니다.

```yaml
platforms:
  domestic:
    - "네이버"
    - "카카오"
    - "쿠팡"
    ...
    - "오늘의집"
    - "당근페이"            # 신규 추가
  foreign:
    - "구글"
    - "메타"
    ...
    - "오픈AI"
    - "앤트로픽"            # 신규 추가

institutions:
  - "공정거래위원회"
  ...
  - "산업통상자원부"
  - "금융위원회"           # 신규 추가
```

> 사전에 등록된 이름은 정확히 일치할 때만 인식됩니다. `"네이버"` 와 `"NAVER"` 둘 다 인식하려면 모두 등록하거나, 한쪽 표기로 통일.

---

### 7.4 정책영역 변경 ⚠️

`policy_domains:` 는 7개 정책 영역을 정의합니다. **이 값을 변경하면 시스템 여러 곳에 영향**을 줍니다.

```yaml
policy_domains:
  - "공정거래"
  - "소비자보호"
  - "개인정보"
  - "노동"
  - "콘텐츠/저작권"
  - "안전"
  - "AI/자동화"
```

#### 영향 범위

정책영역 이름을 추가/변경하려면 **다음 항목을 모두 일관되게 수정**해야 합니다.

| 위치 | 변경 사항 |
|------|----------|
| `policy_domains:` | 영역 목록에 추가 |
| `rss_sources:` | (선택) 해당 영역에 대응하는 RSS 피드 추가 |
| `news_query_categories:` | 해당 영역의 검색 키워드 5~10개 추가 |
| 대시보드 색상 매핑 | `dashboard/src/lib/colors.ts` 등에 새 색상 정의 (개발자 작업 필요) |

#### 권장 운영

영역 추가는 자문 결과 변경 없이 가급적 하지 않는 것을 권장합니다. 변경이 필요하면 개발자와 협의하세요.

---

### 7.5 리스크 임계값 / 트렌딩 비율

`risk:` 섹션에서 고위험·트렌딩 판단 기준을 조정합니다.

```yaml
risk:
  threshold: 70          # 고위험 임계값 (0-100)
  trending_ratio: 2.0    # 트렌딩 키워드 판정 비율
```

| 항목 | 기본값 | 의미 |
|------|--------|------|
| `threshold` | 70 | 이 점수 이상이면 "고위험"으로 분류. 빨간 배지·히트맵 강조 기준 |
| `trending_ratio` | 2.0 | 최근 키워드 빈도가 평소 대비 몇 배 이상이면 트렌딩으로 표시 |

운영 중 고위험 기사가 너무 많거나 적으면 `threshold` 를 60~80 사이로 조정해 보세요. 변경 후 대시보드를 새로고침하면 즉시 반영됩니다 (재분석 불필요).

---

### 7.6 변경 후 적용 절차

`config.yaml` 변경 사항이 시스템에 반영되려면 다음 절차를 따릅니다.

| 변경 항목 | 적용 방법 |
|-----------|----------|
| API 키 | 즉시 반영 (다음 명령 실행 시 적용) |
| RSS 피드 추가/제거 | `python -m src.cli collect --rss` 재실행 |
| 검색 키워드 추가/제거 | `python -m src.cli collect --news` 재실행 |
| 플랫폼/기관 사전 | `python -m src.cli analyze-press --force` (재분석 필요) |
| 리스크 임계값 | 즉시 반영 (대시보드 새로고침으로 충분) |
| 정책영역 | 전체 재실행: `python -m src.cli run-all` |

---

## 8. 일상 운영 / 트러블슈팅

### 8.1 권장 운영 주기

| 빈도 | 작업 | 명령 |
|------|------|------|
| **주 1회** (월요일 오전 권장) | 전체 파이프라인 실행 | `python -m src.cli run-all` |
| 필요 시 | 부분 재분석 | `python -m src.cli analyze-press --force` |
| 월 1회 | API 사용량 확인 | 네이버 개발자센터 / Google AI Studio |
| 분기 1회 | 데이터 백업 | `data\` 폴더 압축 보관 |
| 6개월 1회 | API 키 재발급 (보안) | 3장 절차 반복 |

---

### 8.2 데이터 백업

`data\` 폴더 전체와 `config.yaml` 을 주기적으로 백업합니다.

```bat
:: 예: 2026-04-27 백업
xcopy /E /I data backup\data_2026-04-27
copy config.yaml backup\config_2026-04-27.yaml
```

또는 `data\` 폴더를 우클릭 → **압축(ZIP) 파일로 보내기** 후 안전한 위치에 보관.

> `dashboard\public\data\` 는 자동 생성 사본이므로 별도 백업 불필요합니다.

---

### 8.3 자주 발생하는 오류

| 증상 | 원인 | 해결 방법 |
|------|------|-----------|
| `python: command not found` | Python 미설치 또는 PATH 누락 | 2.2 절차로 재설치, "Add to PATH" 체크 |
| `(venv)` 표시가 안 뜸 | 가상환경 활성화 안 됨 | `venv\Scripts\activate.bat` 실행 |
| `pip install` 실패 (SSL 등) | 사내 프록시 또는 방화벽 | IT 담당자에게 PyPI 접근 허용 요청 |
| `Invalid API key` (Gemini) | 키 오타 또는 따옴표 누락 | `config.yaml` 의 `api_key` 재확인 |
| `Quota exceeded` | Gemini 무료 한도 초과 | 잠시 후 재시도, 또는 결제 활성화 |
| `429 / 503` (Gemini) | 일시적 서버 과부하 | 시스템이 자동 재시도, 그대로 두면 됨 |
| 네이버 API `024` 오류 | Client ID/Secret 불일치 | 개발자센터에서 키 재확인 |
| 네이버 API `010` 오류 | 일일 호출 한도 초과 | 다음날까지 대기 |
| `npm: command not found` | Node.js 미설치 | 2.3 절차로 설치 |
| 대시보드가 빈 화면 | JSON 파일 없음 | `python -m src.cli run-all` 먼저 실행 |
| `port 5173 already in use` | 다른 프로세스가 포트 사용 중 | `npm run dev -- --port 5174` 로 다른 포트 사용 |
| PowerShell 스크립트 차단 | 실행 정책 제한 | 2.5의 `Set-ExecutionPolicy` 명령 실행 |
| 한글이 깨져 표시됨 | 명령 프롬프트 인코딩 | `chcp 65001` 입력 후 재실행 |

---

### 8.4 로그 및 진단

#### 시스템 상태 한눈에 보기

```bat
python -m src.cli status
```

수집·전처리·분석 건수 및 정책 제언 생성 시각이 출력됩니다.

#### 분석 실패 항목 확인

`data\analyzed\press_analysis.json` 또는 `news_analysis.json` 의 `articles[]` 안에서 `"status": "failed"` 인 항목을 검색하면 어떤 기사 분석이 실패했는지 확인할 수 있습니다 (대부분 Gemini 일시 오류로 다음 실행 시 자동 복구). `status` 값은 `analyzed` / `failed` / `skipped` / `parse_error` 중 하나입니다.

#### Gemini API 사용량

**https://aistudio.google.com** → **Get API key** → 키 클릭 → 사용량 확인.

#### 네이버 API 사용량

**https://developers.naver.com/apps** → 내 애플리케이션 → 일일/월간 사용량.

---

### 8.5 인계 시 점검 체크리스트

새로운 담당자에게 시스템을 인계할 때 다음을 확인합니다.

- [ ] Python 3.10 설치 및 `python --version` 동작 확인
- [ ] Node.js LTS 설치 및 `node -v` 동작 확인
- [ ] 프로젝트 폴더 전체 복사 (단, `venv\` 와 `node_modules\` 는 제외 — 새로 생성)
- [ ] `venv` 재생성 + `pip install -r requirements.txt`
- [ ] `dashboard\` 에서 `npm install`
- [ ] **새 담당자 명의로 네이버 API 키 재발급** + `config.yaml` 갱신
- [ ] **새 담당자 명의로 Gemini API 키 재발급** + `config.yaml` 갱신
- [ ] (이전 담당자) 본인 명의 키 모두 폐기
- [ ] `python -m src.cli status` 정상 출력 확인
- [ ] `python -m src.cli run-all` 1회 시범 실행 후 대시보드 표시 확인
- [ ] 본 매뉴얼(`docs\manual.md`)과 `config.yaml` 위치 안내

---

## 부록 A. 디렉토리 구조

```
news-platform-monitor/
├── config.yaml                  # ⚠️ API 키 포함, git 비커밋
├── config.yaml.example          # 예시 파일 (커밋됨)
├── requirements.txt             # Python 의존 패키지 목록
├── README.md
│
├── src/                         # 백엔드 Python 소스
│   ├── __main__.py              # python -m src 진입점
│   ├── cli.py                   # python -m src.cli 진입점
│   ├── config.py                # 설정 로더
│   ├── collectors/              # RSS / Naver 뉴스 수집
│   ├── processors/              # 전처리 (중복제거·태깅)
│   ├── analyzers/               # Gemini 분석·정책 제언
│   ├── models/                  # 데이터 모델
│   └── utils/                   # 공통 유틸
│
├── data/                        # 산출 데이터 (커밋 안 됨)
│   ├── raw/
│   │   ├── rss/                 # RSS 보도자료 원본 JSON (press_data.json)
│   │   └── news/                # 네이버 뉴스 원본 JSON
│   ├── processed/articles.json  # 뉴스 중복제거·태깅 결과 (보도자료는 거치지 않음)
│   └── analyzed/                # LLM 분석 결과
│       ├── press_analysis.json          # 보도자료 분석 + 정책 제언
│       ├── news_analysis.json           # 뉴스 분석
│       └── combined_recommendations.json # 보도자료+뉴스 통합 제언
│
├── dashboard/                   # 프론트엔드 (별도 프로젝트)
│   ├── package.json
│   ├── public/data/             # 분석 JSON 사본 (대시보드가 읽음)
│   └── src/                     # React 소스
│
├── docs/                        # 문서
│   ├── manual.md                # ★ 본 매뉴얼 (인수인계용)
│   ├── dashboard-guide.md       # 대시보드 상세 가이드 (참고용)
│   ├── gemini-api-setup.md      # Gemini API 상세 가이드 (참고용)
│   └── dev-gemini-api-guide.md  # 개발자용 (참고용)
│
└── venv/                        # Python 가상환경 (커밋 안 됨)
```

---

## 부록 B. CLI 명령어 빠른 참조

> 모든 명령은 **가상환경 활성화 + 프로젝트 루트** 에서 실행합니다.

| 명령 | 용도 |
|------|------|
| `python -m src.cli run-all` | 전체 파이프라인 한 번에 실행 (권장) |
| `python -m src.cli collect` | RSS + 네이버 뉴스 모두 수집 |
| `python -m src.cli collect --rss` | RSS 보도자료만 수집 |
| `python -m src.cli collect --news` | 네이버 뉴스만 수집 |
| `python -m src.cli preprocess` | 전처리 (중복 제거 + 태깅) |
| `python -m src.cli analyze-press` | 보도자료 LLM 분석 + 정책 제언 |
| `python -m src.cli analyze-press --force` | 이미 분석된 항목까지 재분석 |
| `python -m src.cli analyze-news` | 뉴스 LLM 분석 |
| `python -m src.cli analyze-news --force` | 뉴스 강제 재분석 |
| `python -m src.cli generate-recommendations` | 통합 정책 제언 생성 |
| `python -m src.cli generate-recommendations --force` | 통합 제언 강제 재생성 |
| `python -m src.cli status` | 수집·분석 현황 요약 |
| `python -m src.cli --help` | 도움말 |

| 대시보드 명령 (dashboard/ 폴더에서) | 용도 |
|------|------|
| `npm install` | 의존 패키지 설치 (최초 1회) |
| `npm run dev` | 개발 서버 실행 (http://localhost:5173) |
| `npm run build` | 정적 빌드 (배포용, 일반 운영 불필요) |

---

## 부록 C. 데이터 파일 스키마 요약

### `data/processed/articles.json`

전처리(중복 제거 + 태깅)가 완료된 **뉴스** 기사 목록. 보도자료는 이 파일을 거치지 않고 `raw/rss/press_data.json` 에서 직접 분석됩니다.

```json
[
  {
    "id": "https://...",
    "title": "기사 제목",
    "content": "본문",
    "url": "https://...",
    "source_type": "news",
    "source_name": "Naver 뉴스",
    "published_at": "Mon, 25 Apr 2026 09:00:00 +0900",
    "collected_at": "...",
    "platform_tags": ["네이버", "쿠팡"],
    "institution_tags": ["공정거래위원회"],
    "query_used": "수집 시 사용된 정책 키워드",
    "category": "공정거래,소비자보호"
  }
]
```

### `data/analyzed/press_analysis.json` / `news_analysis.json`

LLM 분석 결과. 각 기사마다 요약·감성·리스크·키워드 등이 추가됩니다.

```json
{
  "generated_at": "2026-04-25T10:30:00",
  "total_count": 87,
  "analyzed_count": 85,
  "articles": [
    {
      "title": "기사 제목",
      "date": "Mon, 25 Apr 2026 09:00:00 GMT",
      "source_type": "press",
      "status": "analyzed",
      "summary": "AI 요약 (3-5문장)",
      "sentiment": "긍정" | "부정" | "중립",
      "risk_score": 75,
      "keywords": ["자사우대", "과징금", "온라인플랫폼"],
      "policy_domains": ["공정거래"],
      "platforms": ["네이버"],
      "confidence": 0.9
    }
  ],
  "policy_recommendations": [
    { "title": "...", "description": "..." }
  ]
}
```

> `status` 값은 `analyzed` (정상) / `failed` (재시도 필요) / `skipped` (조건 미달) / `parse_error` 중 하나입니다. `policy_recommendations` 필드는 `press_analysis.json`에만 포함됩니다 (보도자료 기반 단독 제언).

### `data/analyzed/combined_recommendations.json`

보도자료 + 뉴스 통합 정책 제언. 분석 건수(`source_counts`)가 직전 실행과 동일하면 LLM 호출을 아끼고 재사용합니다 — 강제 재생성은 `--force` 옵션 사용.

```json
{
  "generated_at": "2026-04-25T10:35:00+00:00",
  "source_counts": { "press": 878, "news": 247 },
  "policy_recommendations": [
    { "title": "...", "description": "..." }
  ]
}
```

### `data/analyzed/combined_recommendations.json`

보도자료 + 뉴스 분석을 종합한 통합 정책 제언.

```json
{
  "generated_at": "2026-04-25T10:35:00Z",
  "source_counts": { "press": 85, "news": 432 },
  "policy_recommendations": [
    {
      "title": "플랫폼 수수료 투명성 강화 방안",
      "body": "배경·근거·구체 조치를 담은 본문 ..."
    }
  ]
}
```

---

**문서 끝.** 변경 사항은 git 이력 또는 문서 상단 작성일을 갱신해 관리하세요.

