# Gemini API 키 발급 및 설정 가이드 (운영용)

이 문서는 본 시스템을 운영할 담당자가 **본인 명의의 Google Gemini API 키를 직접 발급받아 설정**하는 방법을 안내합니다.

> 본 프로젝트는 Google Gemini API를 사용하여 뉴스 분석을 수행합니다. API 호출 비용은 키 발급자의 Google 계정에 청구되므로, 운영 담당자는 반드시 본인 계정의 키를 사용해야 합니다.

---

## 1. 사전 준비

- **Google 계정** (개인 Gmail 또는 조직 Workspace 계정)
- **결제 수단** (선택) — 무료 티어 한도를 초과할 경우 필요
- **인터넷 접속 가능 환경**

---

## 2. API 키 발급 절차

### Step 1. Google AI Studio 접속

브라우저에서 다음 주소로 이동합니다:

**https://aistudio.google.com**

### Step 2. Google 계정 로그인

운영에 사용할 Google 계정으로 로그인합니다.

> 조직 계정(Workspace)을 사용할 경우, 조직 정책에 따라 일부 기능이 제한될 수 있습니다. 제한이 있다면 개인 Gmail 계정 사용을 권장합니다.

### Step 3. API 키 생성

1. 좌측 사이드바 또는 우측 상단의 **"Get API key"** 버튼을 클릭합니다.
2. **"Create API key"** 버튼을 클릭합니다.
3. 새 Google Cloud 프로젝트를 생성하거나, 기존 프로젝트를 선택합니다.
   - 처음 사용하는 경우 **"Create API key in new project"** 선택을 권장합니다.
4. 키가 생성되면 즉시 **복사**하여 안전한 곳에 보관합니다.

> ⚠️ **중요**: API 키는 비밀번호와 동일하게 취급해야 합니다. 외부에 노출되면 즉시 삭제하고 새로 발급받으세요.

### Step 4. 발급된 키 확인

발급된 키는 `AIzaSy...` 로 시작하는 39자 정도의 문자열입니다.

예시 형식: `AI******`

---

## 3. 프로젝트에 키 설정하기

키 설정 방법은 두 가지가 있습니다. 둘 중 한 가지만 선택하면 됩니다.

### 방법 A — `config.yaml` 사용 (권장)

1. 프로젝트 루트에서 예시 파일을 복사합니다:
   ```bash
   cd news-platform-monitor
   cp config.yaml.example config.yaml
   ```

2. `config.yaml` 파일을 편집기로 열고 `api.gemini.api_key` 항목에 발급받은 키를 입력합니다:

   ```yaml
   api:
     gemini:
       api_key: "AIzaSy발급받은_키_전체_문자열"
       model: "gemini-2.5-flash-lite"
   ```

3. 저장 후 종료합니다.

### 방법 B — 환경 변수 사용

`config.yaml`에 키를 직접 적지 않고 환경 변수로 관리하는 방법입니다. 보안상 더 권장됩니다.

**Windows (PowerShell)**:
```powershell
# 현재 세션에만 적용
$env:GEMINI_API_KEY="AIzaSy발급받은_키"

# 영구 적용 (사용자 환경 변수)
[System.Environment]::SetEnvironmentVariable('GEMINI_API_KEY', 'AIzaSy발급받은_키', 'User')
```

**macOS / Linux (bash, zsh)**:
```bash
# 현재 세션에만 적용
export GEMINI_API_KEY="AIzaSy발급받은_키"

# 영구 적용 — ~/.bashrc 또는 ~/.zshrc에 다음 줄 추가
echo 'export GEMINI_API_KEY="AIzaSy발급받은_키"' >> ~/.zshrc
source ~/.zshrc
```

> 환경 변수가 설정되면 `config.yaml`의 `api_key` 값보다 우선 적용됩니다. 따라서 환경 변수 사용 시 `config.yaml`에는 placeholder 값을 그대로 두어도 무방합니다.

---

## 4. 동작 확인

키가 올바르게 설정되었는지 확인합니다.

```bash
python -c "
from google import genai
import yaml, os

# config.yaml 또는 환경 변수에서 키 로드
key = os.environ.get('GEMINI_API_KEY')
if not key:
    with open('config.yaml') as f:
        key = yaml.safe_load(f)['api']['gemini']['api_key']

client = genai.Client(api_key=key)
response = client.models.generate_content(
    model='gemini-2.5-flash-lite',
    contents='안녕하세요. 한 문장으로 답변해주세요.'
)
print(response.text)
"
```

한국어 응답이 출력되면 정상적으로 설정된 것입니다.

오류가 발생할 경우:
- `Invalid API key`: 키 문자열이 잘못 복사되었거나, 키가 비활성화/삭제됨 → 재발급 필요
- `Quota exceeded`: 무료 티어 한도 초과 → 사용량 확인 또는 결제 활성화 필요
- `Permission denied`: 조직 계정 정책으로 차단됨 → 개인 계정 사용 권장

---

## 5. 비용 및 사용량 관리

### 무료 티어

`gemini-2.5-flash-lite` 모델은 Google AI Studio의 **무료 티어**에서 일정량 사용 가능합니다. 한도는 시기에 따라 변동되므로 다음 페이지에서 확인하세요:

**https://ai.google.dev/pricing**

### 사용량 확인

Google AI Studio 대시보드 또는 Google Cloud Console에서 API 호출량을 확인할 수 있습니다:

- AI Studio: https://aistudio.google.com → API keys → 키 클릭 → 사용량 보기
- Google Cloud Console: https://console.cloud.google.com → 해당 프로젝트 → APIs & Services → Generative Language API

### 비용 절감 팁

- 본 시스템은 비용 절감을 위해 경량 모델인 `gemini-2.5-flash-lite`를 사용합니다 — 변경하지 마세요
- 대량 데이터 분석 전에는 소량(10~20건)으로 먼저 동작 확인
- 동일한 기사를 중복 분석하지 않도록 시스템이 자동으로 기존 결과를 재사용 (`--force` 옵션 미사용 시)
- 일일 사용량 알림을 Google Cloud Console에서 설정 권장

---

## 6. 보안 수칙

- ✅ `config.yaml`은 git에 커밋되지 않도록 `.gitignore`에 포함되어 있습니다 (변경 금지)
- ✅ API 키를 코드, 주석, 문서, 채팅, 이메일 등에 노출하지 마세요
- ✅ 키를 다른 사람과 공유하지 마세요 (사용량이 본인 계정에 청구됩니다)
- ✅ 키가 노출된 의심이 들면 즉시 Google AI Studio에서 키를 **Delete** 후 재발급
- ✅ 정기적으로 (예: 6개월마다) 키를 재발급하여 보안 강화

---

## 7. 키 폐기 (필요 시)

업무 종료, 담당자 변경, 키 노출 등의 사유로 키를 폐기하려면:

1. **https://aistudio.google.com** 접속
2. 좌측 **"Get API key"** 메뉴 클릭
3. 폐기할 키 옆의 **휴지통(Delete)** 아이콘 클릭
4. 확인 → 즉시 무효화됨

폐기 후에는 해당 키로 더 이상 API 호출이 불가능합니다.

---

## 참고 자료

- Google AI Studio: https://aistudio.google.com
- Gemini API 공식 문서: https://ai.google.dev/gemini-api/docs
- 가격 정책: https://ai.google.dev/pricing
- Python SDK (`google-genai`): https://googleapis.github.io/python-genai/
