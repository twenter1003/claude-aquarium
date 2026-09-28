"""Claude Code 훅: 서브에이전트 시작·끝을 ~/.claude-aquarium/events.jsonl에 한 줄씩 남긴다.

플러그인 hooks.json의 PreToolUse(Agent)·PostToolUse(Agent)·SubagentStop이 부른다(stdin = 훅 JSON).
모든 프로젝트·세션이 한 파일에 쌓이고, server.py가 읽어 보여 준다. 프롬프트·결과는 앞부분만 남긴다.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

OUT = Path(os.environ.get("AQUARIUM_HOME", Path.home() / ".claude-aquarium")) / "events.jsonl"
CLIP = 600


def clip(v) -> str:
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return s if len(s) <= CLIP else s[:CLIP] + " …"


def main() -> None:
    h = json.load(sys.stdin)
    ev, ti = h.get("hook_event_name", ""), h.get("tool_input") or {}
    row = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "event": ev,
        "session": h.get("session_id", "")[:8],
        "cwd": h.get("cwd", ""),
        "tool_use_id": h.get("tool_use_id", ""),
        "agent_id": h.get("agent_id", ""),
        "agent_type": ti.get("subagent_type") or h.get("agent_type", ""),
        "description": ti.get("description", ""),
    }
    if h.get("tool_name") == "SendMessage":  # 이미 띄운 에이전트를 다시 깨움(재개)
        if ev != "PreToolUse":
            return
        row.update(event="Resume", agent_id=ti.get("to", ""), description=ti.get("summary", ""),
                   prompt=clip(ti.get("message", "")))
    elif ev == "PreToolUse":
        row["prompt"] = clip(ti.get("prompt", ""))
        row["background"] = ti.get("run_in_background", True)
    elif ev == "PostToolUse":
        row["result"] = clip(h.get("tool_response", ""))
    elif ev == "SubagentStop":
        row["result"] = clip(h.get("last_assistant_message", "") or "")
    OUT.parent.mkdir(mode=0o700, parents=True, exist_ok=True)  # 프롬프트 일부가 담기니 나만 읽게
    with OUT.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
