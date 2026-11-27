"""แกนหลักสำหรับคุยกับ Claude: ตั้งค่า, ค้นเว็บ, เรียกเครื่องมือ, streaming

ทั้ง main.py (terminal) และ web.py (หน้าเว็บ) ใช้ไฟล์นี้ร่วมกัน
"""

import os
from collections.abc import Iterator

import anthropic
from dotenv import load_dotenv

from tools import CLIENT_TOOLS, run_tool

load_dotenv()

# ---- ตั้งค่า (แก้ได้ในไฟล์ .env) ----
MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
EFFORT = os.getenv("CLAUDE_EFFORT", "medium")  # low / medium / high / xhigh / max
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are a friendly, helpful assistant. Reply in the same language the user writes in "
    "(usually Thai). Use the web_search tool for recent events or facts you are unsure of, "
    "get_weather for weather questions, and get_current_time for dates and times.",
)
MAX_TOOL_ROUNDS = 10  # กันวนไม่จบ

# โมเดลที่รองรับ server-side fallback แบบ "default" (ส่งต่อเมื่อโมเดลปฏิเสธคำขอ)
_FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-fable-5-2",
                    "claude-fable-5-1", "claude-sonnet-5-5"}
# โมเดลที่ใช้ web search รุ่นใหม่ (dynamic filtering) ได้
_NEW_SEARCH_MODELS = _FALLBACK_MODELS | {"claude-fable-5", "claude-opus-4-8", "claude-opus-4-7",
                                         "claude-opus-4-6", "claude-sonnet-5", "claude-sonnet-4-6"}

client = anthropic.Anthropic()


def _request_params(history: list) -> dict:
    search_type = "web_search_20260209" if MODEL in _NEW_SEARCH_MODELS else "web_search_20250305"
    params = {
        "model": MODEL,
        "max_tokens": 64000,
        "system": SYSTEM_PROMPT,
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": EFFORT},
        "tools": [{"type": search_type, "name": "web_search", "max_uses": 5}, *CLIENT_TOOLS],
        "messages": history,
    }
    if MODEL in _FALLBACK_MODELS:
        params["betas"] = ["server-side-fallback-2026-07-01"]
        params["fallbacks"] = "default"
    return params


def run_turn(history: list) -> Iterator[tuple[str, str]]:
    """ให้ Claude ตอบข้อความล่าสุดใน history

    yield เหตุการณ์ (ชนิด, ข้อความ):
      ("text", ...)   ข้อความคำตอบทีละส่วน
      ("status", ...) สถานะ เช่น กำลังค้นเว็บ / กำลังเรียกเครื่องมือ
      ("error", ...)  เกิดข้อผิดพลาด (history ถูกคืนสภาพแล้ว)
    history จะถูกต่อท้ายด้วยคำตอบของ Claude เมื่อสำเร็จ
    """
    start_len = len(history)
    try:
        for _ in range(MAX_TOOL_ROUNDS):
            with client.beta.messages.stream(**_request_params(history)) as stream:
                for event in stream:
                    if event.type == "content_block_start":
                        block = event.content_block
                        if block.type == "server_tool_use":
                            yield ("status", "🔎 กำลังค้นเว็บ...")
                        elif block.type == "tool_use":
                            yield ("status", f"🛠️ กำลังใช้เครื่องมือ {block.name}...")
                    elif event.type == "content_block_delta" and event.delta.type == "text_delta":
                        yield ("text", event.delta.text)
                response = stream.get_final_message()

            stop = response.stop_reason
            if stop == "refusal":
                del history[start_len - 1:]  # เอาคำถามที่ถูกปฏิเสธออกด้วย
                why = response.stop_details.explanation if response.stop_details else ""
                yield ("error", f"Claude ปฏิเสธคำขอนี้ {why}".strip())
                return

            if stop == "max_tokens" and any(b.type == "tool_use" for b in response.content):
                # tool_use ถูกตัดกลางคัน ห้ามรัน และห้ามเก็บไว้ใน history
                del history[start_len - 1:]
                yield ("error", "คำตอบถูกตัดกลางคันระหว่างเรียกเครื่องมือ ลองถามใหม่")
                return

            history.append({"role": "assistant", "content": response.content})

            if stop == "pause_turn":  # ค้นเว็บยังไม่จบ ส่งกลับไปให้ทำต่อ
                continue
            if stop != "tool_use":  # end_turn / max_tokens / stop_sequence
                if stop == "max_tokens":
                    yield ("status", "⚠️ คำตอบยาวเกินกำหนด ถูกตัดท้าย")
                return

            results = []
            for block in response.content:
                if block.type == "tool_use":
                    output, is_error = run_tool(block.name, block.input)
                    results.append({"type": "tool_result", "tool_use_id": block.id,
                                    "content": output, "is_error": is_error})
            history.append({"role": "user", "content": results})
            yield ("text", "\n")

        del history[start_len - 1:]
        yield ("error", "ใช้เครื่องมือหลายรอบเกินไป หยุดก่อน")
    except anthropic.AuthenticationError:
        del history[start_len - 1:]
        yield ("error", "API key ไม่ถูกต้อง ตรวจ ANTHROPIC_API_KEY ในไฟล์ .env")
    except anthropic.RateLimitError:
        del history[start_len - 1:]
        yield ("error", "เรียกถี่เกินไป รอสักครู่แล้วลองใหม่")
    except anthropic.APIStatusError as e:
        del history[start_len - 1:]
        yield ("error", f"API error {e.status_code}: {e.message}")
    except anthropic.APIConnectionError:
        del history[start_len - 1:]
        yield ("error", "เชื่อมต่อ API ไม่ได้ ตรวจอินเทอร์เน็ต")
