"""หน้าเว็บแชทกับ Claude

ใช้งาน:  python web.py   แล้วเปิด http://127.0.0.1:5000
"""

import json
import threading
import uuid

from flask import Flask, Response, jsonify, render_template, request

from claude_core import MODEL, run_turn

app = Flask(__name__)

# เก็บบทสนทนาไว้ในหน่วยความจำ แยกตาม session (หายเมื่อปิดโปรแกรม)
_sessions: dict[str, list] = {}
_locks: dict[str, threading.Lock] = {}
_guard = threading.Lock()


def _session(sid: str) -> tuple[list, threading.Lock]:
    with _guard:
        return _sessions.setdefault(sid, []), _locks.setdefault(sid, threading.Lock())


@app.get("/")
def index():
    return render_template("index.html", model=MODEL)


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    sid = str(data.get("session_id") or uuid.uuid4())
    if not message:
        return jsonify(error="ข้อความว่าง"), 400

    history, lock = _session(sid)
    if not lock.acquire(blocking=False):
        return jsonify(error="กำลังตอบข้อความก่อนหน้าอยู่ รอสักครู่"), 409

    def generate():
        try:
            history.append({"role": "user", "content": message})
            for kind, text in run_turn(history):
                yield json.dumps({"type": kind, "text": text}, ensure_ascii=False) + "\n"
            yield json.dumps({"type": "done"}) + "\n"
        finally:
            lock.release()

    return Response(generate(), mimetype="application/x-ndjson",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/reset")
def reset():
    sid = str((request.get_json(silent=True) or {}).get("session_id", ""))
    with _guard:
        _sessions.pop(sid, None)
    return jsonify(ok=True)


if __name__ == "__main__":
    print(f"เปิดเบราว์เซอร์ไปที่ http://127.0.0.1:5000  (โมเดล {MODEL})")
    app.run(host="127.0.0.1", port=5000, threaded=True)
