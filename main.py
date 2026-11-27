"""แชทกับ Claude ใน terminal

ใช้งาน:  python main.py
ต้องมี ANTHROPIC_API_KEY ในไฟล์ .env (ดู .env.example)
"""

from claude_core import MODEL, run_turn


def main() -> None:
    print(f"คุยกับ {MODEL} ได้เลย (พิมพ์ exit เพื่อออก, reset เพื่อเริ่มใหม่)\n")
    history: list = []
    while True:
        try:
            user_input = input("คุณ: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user_input.lower() in {"exit", "quit"}:
            break
        if user_input.lower() == "reset":
            history.clear()
            print("— เริ่มบทสนทนาใหม่ —\n")
            continue
        if not user_input:
            continue

        history.append({"role": "user", "content": user_input})
        print("Claude: ", end="", flush=True)
        for kind, text in run_turn(history):
            if kind == "text":
                print(text, end="", flush=True)
            elif kind == "status":
                print(f"\n  [{text}]", flush=True)
            elif kind == "error":
                print(f"\n  [ผิดพลาด] {text}", flush=True)
        print("\n")


if __name__ == "__main__":
    main()
