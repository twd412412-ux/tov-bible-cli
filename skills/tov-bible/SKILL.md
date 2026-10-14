---
name: tov-bible
description: "토브성경 개역한글만을 기준으로 성구를 조회·검색하거나 설교 인용문을 검증한다. 설치된 tov CLI와 함께 사용하며 사전·다른 번역본·교리 판단은 포함하지 않는다."
---

# 토브성경 개역한글

이 스킬은 `tov-bible-cli` 패키지와 함께 사용한다. 계정·로그인·토큰·서버가 필요 없다. CLI의 동봉된 데이터는 토브성경에서 정상 다운로드된 한국어 개역한글 스냅샷이다.

## 준비

첫 설치 점검이나 데이터 오류가 있을 때 `tov data check --json`을 사용한다. 평소 조회는 이미 무결성 검사를 포함하므로 별도 점검을 매번 반복하지 않는다. `tov` 명령이 없다면 같은 Python 환경의 `python3 -m tov_bible` 또는 Windows의 `py -m tov_bible`을 사용한다. 패키지까지 없으면 사용자가 받은 비공개 저장소/배포 파일의 설치 안내를 따른다. 다른 성경을 임시 기준으로 삼지 않는다.

## 조회

```bash
tov verse "요3:16" --json
tov passage "요3:16-18" --json
tov chapter 창세기 1 --format md
tov books --json
tov search "기도 감사" --all --json
tov search "하나님" --book 요한복음 --limit 100 --offset 0 --json
tov batch references.json --json
```

- 모든 본문은 반환된 `text` 그대로 사용한다. 원문 철자·띄어쓰기·괄호를 임의로 교정하지 않는다.
- `source.dataset_version`, `source.dataset_sha256`, `source.source_url`을 검수 기록에 남긴다. URL은 출처 표기이며 조회 시 인터넷에 접속하지 않는다.
- 검색의 `total`, `returned`, `truncated`, `next_offset`을 읽는다. 일부 결과만 받고 전체 검색이 완료됐다고 주장하지 않는다.
- 권명·장절 오류와 데이터 오류는 모델 기억으로 보완하지 않는다.
- 토브성경 원문을 정본으로 취급한다. 다른 사이트나 번역본으로 토브 원문의 옳고 그름을 이중 확인하지 않는다. 여러 성구는 `batch` 한 번으로 조회한다. CLI가 반환한 원문을 그대로 넣어 새 인용을 작성했다면 동일한 조회/검증을 중복 수행할 필요는 없다.

## 인용 검증

이 단계는 이미 작성된 인용을 대조할 때 사용한다. 토브에서 직접 조회한 원문을 사용하는 모든 작업에 추가 검증 호출을 강제하지 않는다.

```bash
tov verify sermon.md --json
tov verify quotes.json --json
```

MD는 `> [!info] **권명 장:절**` 또는 `> **권명 장:절**` 뒤에 이어지는 인용 줄을 읽는다. JSON은 `[{"reference":"요3:16","quote":"확인할 인용문","kind":"quotation"}]` 형식이다. 지원하지 않는 문서는 성구 전수 목록을 명시적으로 JSON으로 준비한다. 파싱된 수와 실제 인용 수를 대조하며 도구가 인식한 일부만으로 전수 검증했다고 주장하지 않는다.

- `exact`: 전체 인용 정확 일치.
- `ordered_excerpt`: 줄임표로 나눈 발췌 조각이 지정 범위의 원문 순서와 일치. 전문 일치는 아니다.
- `formatting_difference`: 공백/NFC 차이. 기본적으로 실패이며 `--allow-formatting`을 명시했을 때만 허용된다. 차이를 숨기지 않는다.
- `reference_only`: 의역/단순 언급의 장절만 존재. 본문 인용 검증 성공이 아니며 별도 검수한다.
- `mismatch`, `missing_quote`, `not_found`, `invalid_reference`: 수정/확인 전에는 인용 검증 PASS로 전달하지 않는다.

종료 코드: `0` 성공, `1` 인용 검증 실패/미검증, `2` 입력·장절 오류 또는 인용 없음, `3` 기준 데이터 오류.

서로 다른 번역이나 다른 사이트 본문을 섞지 않는다. 데이터 스냅샷이 현재 토브성경 서버와 항상 최신/동일하다고 주장하지 않는다. 기존 설교정리 스킬은 자막·설교 충실성·형식 검수를 계속 맡고, 이 CLI는 성구 원문 조회와 인용 대조를 맡는다.
