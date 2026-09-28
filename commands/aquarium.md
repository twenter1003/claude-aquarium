---
description: 아쿠아리움 대시보드 주소를 알려 주고, 꺼져 있으면 켠다
---
Run `(nohup python3 "${CLAUDE_PLUGIN_ROOT}/aquarium/server.py" >/dev/null 2>&1 &)` via Bash, then tell the user the dashboard is at http://127.0.0.1:8788 (or $AQUARIUM_PORT if set).
