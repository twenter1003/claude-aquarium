# claude-aquarium

Claude Code 서브에이전트가 일하는 모습을 수조 속 동물로 보여 주는 로컬 대시보드. 표준 라이브러리 파이썬만 쓰고, 데이터는 내 컴퓨터 밖으로 나가지 않는다.

## 설치
```
/plugin marketplace add twenter1003/claude-aquarium
/plugin install claude-aquarium@claude-aquarium
```
세션을 새로 열면 서버가 자동으로 뜬다 → http://127.0.0.1:8788 (`/aquarium`으로도 켤 수 있다). python3 필요.

## 동작
- 훅이 서브에이전트 시작·끝을 `~/.claude-aquarium/events.jsonl`에 쌓는다(프롬프트·결과는 앞 600자만).
- `~/.claude/agents/*.md`와 쓰는 프로젝트의 `.claude/agents/*.md`에 정의한 에이전트마다 수조가 하나씩 생긴다. 동물은 이름 순서대로 배정된다.
- 정의 파일이 없는 에이전트(general-purpose, Explore 등)는 회의 수조의 손님 불가사리로 보인다.

## 캐릭터 설정 (에이전트 파일 frontmatter, 선택)
```yaml
---
name: supervisor
description: ...
aquarium_name: 감독관        # 수조 이름표 (없으면 에이전트 이름)
aquarium_animal: 펭귄        # 없으면 순서대로 배정
---
```
`aquarium_animal`에는 기본 그림 8종(펭귄 penguin, 돌고래 dolphin, 문어 octopus, 거북이 turtle, 물범 seal, 수달 otter, 해파리 jelly, 햄스터 hamster)을 한국어나 영어로 쓰거나, 아무 이모지(🚀, 🤖, 🐱…)를 쓸 수 있다.
컨셉을 바꾸려면 이모지와 `AQUARIUM_TITLE`을 함께 바꾸면 된다. 예: 🚀·🛰️·👽 + `AQUARIUM_TITLE="우주 정거장"`.

## 설정 (환경변수, 전부 선택)
| 변수 | 기본값 | 뜻 |
|---|---|---|
| `AQUARIUM_TITLE` | 에이전트 아쿠아리움 | 화면 제목 |
| `AQUARIUM_PORT` | 8788 | 서버 포트 |
| `AQUARIUM_HOME` | `~/.claude-aquarium` | 이벤트 파일 위치 |
| `AQUARIUM_THREADS` | 없음 | 리뷰 스레드 폴더. `## N. <에이전트> (HH:MM) — <종류>` + `**요지:**` + `**한마디:**` 형식의 .md를 회의 수조에 보여 준다 |

기록 지우기: `rm ~/.claude-aquarium/events.jsonl`
