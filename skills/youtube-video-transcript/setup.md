# Setup — YouTube Video Transcript

Read this for a new installation or missing dependencies. Sermon workflows require the Tov CLI section below as well as yt-dlp.

## Your Attitude

You're offering a powerful way to work with video content. The user might be a researcher, content creator, student, or just someone who prefers reading to watching. Adapt to their needs.

## Verify yt-dlp Installation

Before first use, verify `yt-dlp` is available:

```bash
which yt-dlp
```

If not installed, offer to help:
- "I need yt-dlp to extract transcripts. Want me to help you install it?"
- Options: `brew install yt-dlp` (macOS) or `pip install yt-dlp`

## Priority Order

### 1. First: Help With Their Immediate Request

If they came with a specific video, help with that first. Don't delay with questions before delivering value.

### 2. Then: Ask About Caching Preference

After the first transcript, ask:
- "Want me to save transcripts locally for faster access next time? They'll go in ~/youtube-video-transcript/videos/"
- Respect their choice. If they say no, don't cache.

### 3. Finally: Integration

When appropriate in conversation:
- "Want me to automatically offer to transcribe when you share YouTube links?"
- "Should I remember your format preferences (timestamps, summaries)?"

## What to Save (With User Consent)

If user agrees to caching, save to `~/youtube-video-transcript/memory.md`:
- **Preferred format:** markdown / text / srt
- **Timestamp preference:** always / sometimes / never
- **Summary style:** brief / detailed / chapter-based
- **Export location:** if they have a preference

Tell the user what you're saving: "I'll remember you prefer summaries with timestamps."

## Transparency Rules

1. **Always tell the user** what you're about to save and where
2. **Ask before caching** transcripts for the first time
3. **Confirm preferences** before storing them
4. **Offer to show** saved files if they ask

## When "Ready"

You're ready after:
1. Successfully extracting one transcript
2. Understanding if they want caching (yes/no)

Everything else builds naturally over time.

## 토브 CLI 설치와 스킬 전달

설교 성경 인용에는 토브성경 개역한글 CLI와 동봉된 본문 데이터가 필요하다. Python 3.9 이상을 사용한다. 스킬만 복사해도 CLI가 자동 설치되는 것은 아니다. 사용자가 설치를 요청하면 아래 해당 경로로 설치하고, 기존 설치가 있으면 다시 설치하지 않는다.

### 공개 GitHub에서 설치

저장소: [twd412412-ux/tov-bible-cli](https://github.com/twd412412-ux/tov-bible-cli). 공개 저장소이므로 GitHub·토브 계정이나 초대가 필요 없다. 같은 저장소에 `skills/youtube-video-transcript`와 `skills/tov-bible`이 들어 있다. 아래는 Git과 Python이 설치된 환경의 예다. 기존 폴더를 덮어쓰지 않는다.

Mac/Linux:

```bash
git clone https://github.com/twd412412-ux/tov-bible-cli.git
cd tov-bible-cli
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/tov data check --json
```

Windows PowerShell:

```powershell
git clone https://github.com/twd412412-ux/tov-bible-cli.git
cd tov-bible-cli
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\tov.exe data check --json
```

Git이 없으면 공개 저장소에서 소스 ZIP을 받아 풀고, 해당 폴더에서 가상환경 생성·설치 단계를 실행해도 된다. Windows 명령은 안내용이며 실제 Windows 호스트에서는 별도로 동작 확인한다.

### 오프라인 설치 파일을 전달할 경우

관리자가 성경 데이터가 포함된 wheel을 전달한다. 현재 파일명은 `tov_bible_cli-0.1.0-py3-none-any.whl`, 크기는 약 1.6MB다. 파일명은 실제 전달된 버전을 따른다. 다운로드 가능한 GitHub 릴리스가 있다고 가정하지 않는다.

wheel이 있는 폴더에서 새 가상환경을 만든 뒤 설치한다. Mac/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --no-index --no-deps tov_bible_cli-0.1.0-py3-none-any.whl
.venv/bin/tov data check --json
```

Windows에서는 `py -m venv .venv`로 생성하고, 위 Python과 tov 경로를 `.\.venv\Scripts\python.exe`, `.\.venv\Scripts\tov.exe`로 바꾼다. wheel 설치는 인터넷·GitHub 계정·토브 계정 없이 가능하다. Python 자체는 먼저 설치되어 있어야 한다.

### 전달물과 첫 설치 확인

- 설교정리 스킬 폴더 전체: `SKILL.md`, `setup.md`, `templates/`, `scripts/` 등 연결된 파일을 함께 전달한다.
- 토브 CLI: 공개 저장소 링크 또는 데이터가 포함된 wheel 파일을 함께 전달한다. 비밀번호·쿠키·토큰은 포함하지 않는다. 설치·조회 요청을 원격 저장소 수정·푸시나 계정 권한 변경의 허가로 해석하지 않는다.
- 선택 사항: 저장소의 `skills/tov-bible` 폴더도 상대 AI의 스킬 디렉터리에 설치하면 별도 성구 조회 요청에도 쓸 수 있다. 설교정리 스킬에는 필수 조회 지침이 있으므로 이 보조 스킬이 없다고 다른 성경을 사용하지 않는다.
- 첫 설치 때 `tov data check --json` 성공을 확인한다. 가상환경을 썼다면 AI가 위 환경의 tov 경로 또는 Python의 `-m tov_bible` 호출을 사용하도록 안내한다. 검사가 실패하면 다른 출처로 대체하지 않는다. 평소 설교마다 이 설치 검사를 반복하지 않는다.

CLI 런타임에는 로그인·인터넷·REA·브라우저가 필요 없다. 저장소는 공개지만, 이 설치 안내가 본문 데이터의 별도 재배포 라이선스를 부여하는 것은 아니다.

### AI에 두 스킬 등록

CLI 설치 후 `skills/youtube-video-transcript`와 `skills/tov-bible` 폴더 전체를 상대 AI의 사용자 스킬 디렉터리에 설치한다. 예를 들어 Codex에서는 `~/.agents/skills/`를 사용한다. 기존 같은 이름의 스킬이 있으면 덮어쓰지 말고 비교·백업 후 사용자에게 갱신 여부를 확인한다. 다른 AI는 해당 제품의 지원 경로를 따른다.

가상환경으로 설치했으면 AI에 CLI 실행 경로도 알려준다. 위 예에서 Mac/Linux는 `<저장소 절대경로>/.venv/bin/tov`, Windows는 `<저장소 절대경로>\.venv\Scripts\tov.exe`다. 활성화한 환경의 `python -m tov_bible`로도 실행할 수 있다. `tov`를 찾을 수 없다는 이유로 다른 성경을 사용하지 않는다.

최초 설치 점검은 데이터 검사와 스킬 필수 파일 확인까지다. 이것을 실제 유튜브 설교 한 편의 전체 정리 검증이라고 주장하지 않는다. 설치 후 유튜브 설교 링크와 ‘정리해줘’ 요청에 기존 자막·교정 전문·토브 성구·시간순 정리·두 MD 전달 절차를 적용한다.
