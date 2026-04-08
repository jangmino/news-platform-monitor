# 개발자용 Gemini API 키 사용 안내

> 이 문서는 본 프로젝트에 **개발자로 참여하는 사람**을 대상으로 합니다.
> 운영 담당자(KISDI)는 [gemini-api-setup.md](gemini-api-setup.md) 문서를 참고하여 본인 키를 직접 발급받아 사용하세요.

---

## ⚠️ 중요 — 개발 전용 키

- 본 키는 **지도교수 개인 Google 계정에서 발급된 키**입니다
- **개발 기간 동안만 한시적으로 사용**되며, 인수인계 시 폐기됩니다
- 사용량은 지도교수 계정에 청구되므로 **불필요한 호출을 피해주세요**
- 운영(KISDI)에서는 자체 키를 발급받아 사용할 예정입니다

---

## 1. 키 전달 받기

키는 보안상 다음 채널 중 하나로만 전달됩니다:

- ✅ 비밀번호 매니저 (1Password, Bitwarden 등)의 secure share
- ✅ 암호화 메신저 (Signal 등)
- ✅ 대면 전달

다음 채널로는 **절대** 전달받지 마세요:

- ❌ 일반 이메일, 카카오톡, 일반 Slack 채널
- ❌ GitHub Issue, PR 본문/댓글
- ❌ 메모장에 적어 공유

---

## 2. 프로젝트에 키 설정

전달받은 키를 다음 두 방법 중 하나로 설정합니다.

### 방법 A — `config.yaml` 사용 (간편)

1. 프로젝트 루트로 이동:
   ```bash
   cd news-platform-monitor
   ```

2. 예시 파일을 복사하여 `config.yaml` 생성:
   ```bash
   cp config.yaml.example config.yaml
   ```

3. `config.yaml` 편집기로 열고 `api.gemini.api_key` 부분에 키 입력:
   ```yaml
   api:
     gemini:
       api_key: "전달받은_키"
       model: "gemini-2.5-flash-lite"
   ```

### 방법 B — 환경 변수 사용 (권장)

config.yaml에 키를 적지 않아 더 안전합니다.

**macOS / Linux**:
```bash
export GEMINI_API_KEY="전달받은_키"
```

**Windows (PowerShell)**:
```powershell
$env:GEMINI_API_KEY="전달받은_키"
```

영구 적용 방법은 [gemini-api-setup.md](gemini-api-setup.md)의 환경 변수 섹션을 참고하세요.

---

## 3. 동작 확인

```bash
python -c "
from google import genai
import yaml, os

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

한국어 응답이 출력되면 정상입니다.

---

## 4. 보안 수칙 (필수 준수)

1. **`config.yaml`은 절대 git에 커밋 금지** (`.gitignore`에 이미 포함되어 있음)
2. 키를 **코드, 주석, 문서, 채팅, 이슈, PR**에 절대 노출 금지
3. 노트북 분실/도난 시 즉시 지도교수에게 알릴 것 (즉시 키 재발급 필요)
4. 키를 다른 사람에게 재전달 금지
5. **개발이 끝나면 본인 PC에서 키를 삭제**할 것
   - `config.yaml`의 `api_key` 항목 삭제 또는 placeholder 값으로 변경
   - 환경 변수에서 `GEMINI_API_KEY` 제거

---

## 5. 비용 절감 가이드

본 키는 지도교수 계정에 비용이 청구되므로 다음을 준수해주세요:

### 개발 중 권장 사항

- 새 기능을 테스트할 때는 **샘플 10~20건**으로 먼저 검증
- 전체 데이터(수백~수천 건) 분석은 동작 확인 후 1회만 실행
- `--force` 옵션은 정말 필요할 때만 사용 (이미 분석한 항목 재호출 방지)
- 디버깅 중에는 print 문으로 응답 확인 후, 분석 로직 자체는 mock 응답으로 테스트
- 무한 루프, 잘못된 프롬프트로 대량 호출이 발생하지 않도록 주의

### 사용량 모니터링

본인이 사용량을 직접 확인할 수는 없습니다. 의심스러운 동작이 있거나 대량 호출이 필요한 작업을 시작하기 전에는 **지도교수에게 미리 알려주세요**.

### 예시 — 안전한 작업 흐름

```bash
# 1. 먼저 소량으로 동작 확인
python -m src.cli collect --news    # 뉴스 수집
python -m src.cli preprocess        # 전처리
# processed/articles.json 에서 5~10건만 남기고 삭제
python -m src.cli analyze           # 분석 (소량)

# 결과 확인 후 OK이면 전체 실행
```

---

## 6. 노출 사고 발생 시

만약 실수로 키를 git에 커밋하거나 외부에 노출했다면:

1. **즉시** 지도교수에게 알리기 (Slack/메신저/전화)
2. 노출된 위치 (커밋 hash, 채널 등) 함께 전달
3. 지도교수가 키를 재발급할 동안 작업 중단
4. 새 키 받은 후 다시 설정

당황하거나 숨기지 말고 즉시 알리는 것이 가장 중요합니다. 노출된 키는 빠르게 폐기할수록 피해가 작습니다.

---

## 7. 인수인계 시점

본 프로젝트가 KISDI에 인수인계되는 시점에 이 키는 폐기됩니다. 인수인계 후:

- 본인 PC에서 키 흔적을 모두 삭제
- KISDI 측은 자체 키를 발급받아 운영 환경에 설정
- 본 문서는 KISDI 인수인계 패키지에서 제외 (`gemini-api-setup.md`만 전달)

---

## 참고

- 운영 담당자용 가이드: [gemini-api-setup.md](gemini-api-setup.md)
- Gemini API 공식 문서: https://ai.google.dev/gemini-api/docs
