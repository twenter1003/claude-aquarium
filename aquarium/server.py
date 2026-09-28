"""서브에이전트 아쿠아리움: ~/.claude-aquarium/events.jsonl(events.py 훅이 씀)을 읽어 에이전트별 수조를 보여 준다.

  python3 server.py            # http://127.0.0.1:8788 (플러그인 SessionStart 훅이 자동으로 띄움, 이미 떠 있으면 조용히 끝남)
수조는 ~/.claude/agents 와 이벤트에 나온 프로젝트의 .claude/agents 에 정의된 에이전트마다 하나씩 생긴다.
AQUARIUM_THREADS=<dir>이면 그 폴더의 리뷰 스레드(.md)를 회의 수조에 보여 준다.
"""

import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

EVENTS = Path(os.environ.get("AQUARIUM_HOME", Path.home() / ".claude-aquarium")) / "events.jsonl"
PAGE = Path(__file__).resolve().parent / "index.html"
AGENT_ID = re.compile(r"agentId\"?:\s*\"?([0-9a-f]{8,})")  # 문장형·JSON형 결과 둘 다
ASYNC = re.compile(r"Async agent launched|\"isAsync\": true")
TITLE = os.environ.get("AQUARIUM_TITLE", "에이전트 아쿠아리움")
THEME = os.environ.get("AQUARIUM_THEME", "sea")
CSS = Path(os.environ["AQUARIUM_CSS"]) if os.environ.get("AQUARIUM_CSS") else None  # 직접 만든 테마
PORT = int(os.environ.get("AQUARIUM_PORT", 8788))
THREADS = Path(os.environ["AQUARIUM_THREADS"]) if os.environ.get("AQUARIUM_THREADS") else None
POST = re.compile(r"^## (\d+)\. (\S+) \(([^)]*)\) — (\S+)\s*\n\*\*요지:\*\*\s*(.+)(?:\n\*\*한마디:\*\*\s*(.+))?$", re.M)


def talks(n: int = 3) -> list[dict]:
    """최근 리뷰 스레드 n개(파일 수정 순)의 글: 누가·언제·무슨 글·요지. 스레드가 에이전트끼리의 대화다."""
    if not THREADS:
        return []
    files = sorted(THREADS.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)[:n]
    return [{"id": f.stem, "posts": [{"n": int(m[1]), "who": m[2], "time": m[3], "kind": m[4], "gist": m[5].replace("**", "")[:400],
                                      "say": (m[6] or "").strip()}
                                     for m in POST.finditer(f.read_text())]} for f in files]


def state() -> dict:
    """에이전트(agentId)별 마지막 상태와 최근 일지. 백그라운드 에이전트는 SubagentStop에 끝난다."""
    rows = []
    if EVENTS.is_file():
        for line in EVENTS.read_text().splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    agents: dict[str, dict] = {}  # 키: agentId(없으면 tool_use_id)
    by_tool: dict[str, str] = {}
    log = []
    for r in rows:
        ev, key = r["event"], None
        if ev == "PreToolUse":
            key = by_tool[r["tool_use_id"]] = r["tool_use_id"]
            agents[key] = {"type": r["agent_type"] or "general-purpose", "task": r["description"],
                           "prompt": r.get("prompt", ""), "session": r["session"],
                           "started": r["ts"], "status": "working", "result": ""}  # fmt: skip
            log.append({"ts": r["ts"], "type": agents[key]["type"], "what": "시작", "task": r["description"]})
        elif ev == "PostToolUse":
            old = by_tool.get(r["tool_use_id"])
            m = AGENT_ID.search(r.get("result", ""))
            if old and m:  # tool_use_id로 만든 칸을 agentId로 옮긴다(재개·종료가 agentId로 온다)
                agents[m.group(1)] = agents.pop(old)
                by_tool[r["tool_use_id"]] = m.group(1)
            key = by_tool.get(r["tool_use_id"])
            if key in agents and not ASYNC.search(r.get("result", "")):
                done(agents[key], r, log)  # 포그라운드 에이전트는 여기서 끝난다
        elif ev == "Resume":
            a = agents.setdefault(r["agent_id"], {"type": "", "task": "", "prompt": r.get("prompt", ""),
                                                  "session": r["session"], "result": ""})  # 훅 전에 띄운 에이전트
            a.update(status="working", task=r["description"] or a["task"], started=r["ts"])
            log.append({"ts": r["ts"], "type": a["type"], "what": "다시 일함", "task": a["task"]})
        elif ev == "SubagentStop" and r["agent_id"] in agents:
            a = agents[r["agent_id"]]
            a["type"] = a["type"] or r["agent_type"]  # 재개로만 본 에이전트는 여기서 역할을 안다
            done(a, r, log)
    dirs = [Path.home() / ".claude"] + [Path(c) / ".claude" for c in {r.get("cwd") for r in rows} if c]
    files = {f.stem: f for d in dirs for f in sorted((d / "agents").glob("*.md"))}  # 같은 이름이면 프로젝트 쪽이 이김
    roles = [{"id": k, **front(f)} for k, f in sorted(files.items())]
    return {"roles": roles, "agents": list(agents.values()), "log": log[-40:][::-1], "talks": talks()}


FRONT = re.compile(r"^(aquarium_name|aquarium_animal):\s*(.+?)\s*$", re.M)


def front(f: Path) -> dict:
    """에이전트 파일 frontmatter의 aquarium_name(표시 이름)·aquarium_animal(동물 키 또는 이모지)."""
    head = f.read_text().split("---")[1] if f.read_text().startswith("---") else ""
    return {k.removeprefix("aquarium_"): v.strip("\"'") for k, v in FRONT.findall(head)}


def done(a: dict, r: dict, log: list) -> None:
    if a.get("status") == "done":
        return
    a.update(status="done", ended=r["ts"], result=r.get("result", ""))
    log.append({"ts": r["ts"], "type": a["type"], "what": "끝냄", "task": a["task"]})


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.headers.get("Host", "").rsplit(":", 1)[0] not in ("127.0.0.1", "localhost"):  # DNS 리바인딩 차단
            self.send_error(403)
            return
        if self.path.startswith("/api/state"):
            body, ctype = json.dumps({**state(), "title": TITLE, "theme": THEME}, ensure_ascii=False).encode(), "application/json"
        elif self.path.startswith("/theme.css"):
            body, ctype = (CSS.read_bytes() if CSS and CSS.is_file() else b""), "text/css"
        else:
            body, ctype = PAGE.read_bytes(), "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_) -> None:  # 폴링 로그로 launchd 로그가 불지 않게
        pass


if __name__ == "__main__":
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:  # 이미 떠 있다(다른 세션이 먼저 띄움)
        raise SystemExit(0)
    srv.serve_forever()
