# tov-bible-cli

토브성경 개역한글만 사용하는 **오프라인 성구 조회·검색·인용 검증 CLI**. 개인·가족 및 AI 도구용 비공개 프로젝트입니다.

실행에는 토브성경 계정, GitHub 계정, 비밀번호, 쿠키, API 키, 인터넷, Chrome, REA가 필요 없습니다. Python 3.9 이상만 필요합니다. 런타임 외부 의존성은 없습니다.

## 설치

비공개 저장소 접근은 소스를 내려받을 때만 필요합니다. 접근 권한이 없는 가족에게는 관리자가 만든 wheel/ZIP을 전달하면 됩니다. 프로그램 실행에 로그인 절차는 없습니다.

### 전달받은 wheel (가장 간단)

```bash
python3 -m pip install --no-deps tov_bible_cli-0.1.0-py3-none-any.whl
tov verse "요3:16" --json
```

Windows에서는 `python3` 대신 `py`, 명령 탐색이 안 되면 `py -m tov_bible`을 사용합니다. `--no-deps`로 오프라인 wheel 설치도 가능합니다.

### 비공개 저장소 접근 권한이 있는 경우

```bash
gh repo clone twd412412-ux/tov-bible-cli
cd tov-bible-cli
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/tov verse "요3:16"
```

Windows: `py -m venv .venv`, `.venv\Scripts\python -m pip install .`, `.venv\Scripts\tov verse "요3:16"`.

소스 ZIP은 설치 없이도 실행할 수 있습니다. Mac: `PYTHONPATH=src python3 -m tov_bible verse "요3:16"`; PowerShell: `$env:PYTHONPATH="src"; py -m tov_bible verse "요3:16"`. 이는 빌드 도구가 없는 환경을 위한 대안입니다.

## 명령

```bash
tov books --json
tov book 요한복음 --json
tov verse "요3:16" --json
tov passage "요3:16-18" --json
tov passage "요3:36-4:2" --json
tov chapter 창세기 1 --format md
tov search "기도 감사" --all --json
tov search "하나님 사랑" --any --book 요한복음 --json
tov search "하나님이 세상을" --phrase --json
tov search "하나님" --limit 0 --json
tov batch references.json --json
tov verify sermon.md --json
tov data info --json
tov data check --json
tov data diff /path/to/other/data --json
```

기본 검색은 모든 단어(AND), `--any`는 OR, `--phrase`는 연속 문자열 검색입니다. 기본 100건이며 `total`·`truncated`·`next_offset`을 명시합니다. `--limit 0`은 전체입니다. 검색은 형태소/의미 검색이 아닙니다.

`verse`는 반드시 한 절이어야 합니다. 범위에는 `passage`를 사용하세요. `마24:36,33`처럼 같은 장의 비연속 절과 `요3:16;창1:1` 목록도 입력 순서대로 지원합니다. 여러 권을 하나의 연속 범위로 표현하지 않습니다. 약칭은 원본 권명 목록에 있는 정확한 약칭을 사용하고, 요한일서/이서/삼서 별칭도 지원합니다. 임의 prefix 추측은 하지 않습니다.

`batch` 입력은 성구 문자열의 JSON 목록 또는 한 줄에 한 성구인 텍스트입니다. `-`는 표준입력입니다.

## 인용 검증

전체 인용은 원문 그대로 일치해야 합니다. 줄임표(`…`, `...`)가 있으면 조각의 등장 순서를 검사합니다. 공백/NFC 차이는 `formatting_difference`로 기본 실패하며, 표시 차이를 허용하기로 결정한 경우에만 `--allow-formatting`을 쓰세요. 따옴표의 바깥 포장만 제거하며 성경 본문 문장부호는 임의 삭제하지 않습니다.

지원 MD:

```markdown
> [!info] **창세기 1:1**
> “태초에 하나님이 천지를 창조하시니라”
```

Apple 메모용 `> **성구**` 형식도 지원합니다. ‘성구’ 자리는 실제 장절이어야 합니다. MD 파서는 이 명시적 인용 블록만 인식합니다. 일반 본문 속 모든 성구/각주/HTML을 자동 탐지한다고 주장하지 않습니다. 실제 인용 수와 반환된 `checked`를 대조하세요.

복잡한 문서에는 명시적 JSON 목록을 권장합니다:

```json
[{"reference":"창1:1","quote":"태초에 하나님이 천지를 창조하시니라","kind":"quotation"}]
```

`kind`는 `quotation`, `mention`, `paraphrase`. 뒤의 두 유형은 장절만 확인하고 `reference_only`로 남깁니다. 전문 정확 일치로 통과시키지 않습니다. 도구는 설교자의 뜻, 발췌의 문맥 적절성, 실제 낭독 여부를 판단하지 않습니다.

종료 코드: 0 성공 / 1 인용 실패 또는 미검증 / 2 입력·장절 오류·인용 없음 / 3 데이터 손상. 오류 시 다른 성경 사이트나 모델 기억으로 대체하지 않습니다.

## 출처와 데이터 무결성

- `https://bible.jbch.org/`의 공식 오프라인 IndexedDB 중 `kor` 본문·권명만 추출.
- 66권, 1,189장, 31,101절. 원본 `sentence`를 변경하지 않고 압축해 패키지에 포함.
- manifest에 확보 시각, 원본 추출 파일 SHA-256, 데이터 SHA-256, 압축 파일 SHA-256, 개수를 기록.
- 매 실행마다 압축/본문 해시 및 구조를 검사. 자동 온라인 업데이트/대체 출처 없음.
- 데이터는 **확보 시점 스냅샷**입니다. 현재 사이트와의 모든 절 전수 대조 또는 최신성은 별도 확인이 필요합니다. 다른 성경의 절 수를 억지로 맞추지 않습니다.
- 계정정보·쿠키·개인 노트·읽기 기록·사이트 실행 코드·사전은 포함하지 않습니다.

본문 데이터의 일반 재배포 라이선스를 주장하지 않습니다. 비공개 개인·가족 용도를 유지하고 공개 배포로 변경하지 마세요. 이 저장소의 접근 권한을 다른 사용자에게 추가하는 일은 별도 관리 작업입니다.

## AI 스킬

`skills/tov-bible` 폴더를 AI 도구의 사용자 스킬 디렉터리에 설치하고, 위 CLI도 설치하세요. 예: Codex `~/.codex/skills/tov-bible`. 스킬만 복사하면 CLI가 자동 설치되는 것은 아닙니다. 스킬은 항상 JSON 결과·종료 코드·출처 버전을 확인하고 다른 성경으로 대체하지 않게 안내합니다.

기존 설교정리 스킬은 이번 릴리스에서 수정하지 않았습니다. 검증 엔진을 별도로 시험한 후 연결하면 됩니다.

## 개발/검사

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 tools/import_snapshot.py /path/to/official-browser-export.json
```

import 도구는 비어 있는 출력 폴더에만 씁니다. 업데이트는 이전 manifest와 원문 diff를 검토한 후 새 버전으로 관리합니다. 출처 메타데이터와 SHA-256은 변조 탐지/재현 근거이며 사이트 자체의 진위를 독립적으로 증명하지는 않습니다.
