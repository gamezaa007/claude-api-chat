"""แชทกับ Claude ผ่าน Claude API (Anthropic Python SDK)

ใช้งาน:  python main.py
ต้องมี ANTHROPIC_API_KEY ในไฟล์ .env (ดู .env.example)
"""

import anthropic
from dotenv import load_dotenv

load_dotenv()  # อ่าน ANTHROPIC_API_KEY จากไฟล์ .env

MODEL = "claude-opus-5-5"
SYSTEM = "You are a helpful assistant. Reply in the same language the user writes in."

client = anthropic.Anthropic()


def chat_turn(history: list) -> None:
    """ส่งบทสนทนาทั้งหมดให้ Claude แล้วพิมพ์คำตอบแบบ streaming"""
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=64000,
        system=SYSTEM,
        thinking={"type": "adaptive"},
        output_config={"effort": "medium"},
        # ถ้าโมเดลปฏิเสธคำขอ (refusal) ให้เซิร์ฟเวอร์ส่งต่อไปโมเดลสำรองอัตโนมัติ
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=history,
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
        response = stream.get_final_message()
    print()

    if response.stop_reason == "refusal":
        reason = response.stop_details.explanation if response.stop_details else ""
        print(f"[Claude ปฏิเสธคำขอนี้] {reason}")
        history.pop()  # เอาข้อความล่าสุดออก จะได้ถามใหม่ได้
        return

    # เก็บ content ทั้งก้อน (รวม thinking blocks) กลับเข้า history ตามที่ API ต้องการ
    history.append({"role": "assistant", "content": response.content})


def main() -> None:
    print(f"คุยกับ {MODEL} ได้เลย (พิมพ์ exit เพื่อออก)\n")
    history: list = []
    while True:
        try:
            user_input = input("คุณ: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue

        history.append({"role": "user", "content": user_input})
        print("Claude: ", end="", flush=True)
        try:
            chat_turn(history)
        except anthropic.AuthenticationError:
            print("\nAPI key ไม่ถูกต้อง ตรวจ ANTHROPIC_API_KEY ในไฟล์ .env")
            return
        except anthropic.RateLimitError:
            print("\nเรียกถี่เกินไป รอสักครู่แล้วลองใหม่")
            history.pop()
        except anthropic.APIStatusError as e:
            print(f"\nAPI error {e.status_code}: {e.message}")
            history.pop()
        except anthropic.APIConnectionError:
            print("\nเชื่อมต่อ API ไม่ได้ ตรวจอินเทอร์เน็ต")
            history.pop()


if __name__ == "__main__":
    main()
