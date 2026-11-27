# Claude API Chat (Python)

แชทกับ Claude ผ่าน Anthropic Python SDK ได้ทั้งใน **terminal** และ **หน้าเว็บ**
Claude ค้นเว็บ ดูพยากรณ์อากาศ และบอกวันเวลาได้

## ติดตั้ง

```powershell
python -m pip install -r requirements.txt
copy .env.example .env
notepad .env
```

ใส่ `ANTHROPIC_API_KEY` ของคุณในไฟล์ `.env` (สร้าง key ได้ที่ https://platform.claude.com/settings/keys ต้องเติมเครดิตก่อนใช้)

## ใช้งาน

**หน้าเว็บ**

```powershell
python web.py
```

แล้วเปิด http://127.0.0.1:5000

**Terminal**

```powershell
python main.py
```

พิมพ์ `reset` เพื่อเริ่มบทสนทนาใหม่ หรือ `exit` เพื่อออก

## ตั้งค่า (ในไฟล์ `.env`)

| ตัวแปร | ค่าเริ่มต้น | ความหมาย |
|---|---|---|
| `CLAUDE_MODEL` | `claude-opus-5-5` | เปลี่ยนเป็น `claude-sonnet-5-5` หรือ `claude-haiku-5-5` (ถูกที่สุด) เพื่อประหยัด |
| `CLAUDE_EFFORT` | `medium` | ความลึกในการคิด `low` / `medium` / `high` / `xhigh` / `max` |
| `SYSTEM_PROMPT` | ผู้ช่วยทั่วไป | นิสัย/บทบาทของบอท เช่น พนักงานตอบลูกค้า |

## เครื่องมือที่ Claude ใช้ได้

| เครื่องมือ | ทำงานที่ | รายละเอียด |
|---|---|---|
| `web_search` | เซิร์ฟเวอร์ Anthropic | ค้นข้อมูลล่าสุดจากเว็บ (สูงสุด 5 ครั้งต่อคำตอบ, มีค่าใช้จ่ายต่อครั้ง) |
| `get_weather` | เครื่องคุณ | อากาศปัจจุบันจาก [Open-Meteo](https://open-meteo.com) (ฟรี ไม่ต้องใช้ key) |
| `get_current_time` | เครื่องคุณ | วันเวลาปัจจุบันตาม timezone |

เพิ่มเครื่องมือเองได้ใน `tools.py`: เพิ่มคำนิยามใน `CLIENT_TOOLS`, เขียนฟังก์ชัน, แล้วใส่ใน `_HANDLERS` และ `_validate`

## โครงสร้าง

```
claude_core.py   ตั้งค่า + ลูปคุยกับ Claude (streaming, เครื่องมือ, จัดการ error)
tools.py         เครื่องมือที่รันบนเครื่องคุณ
main.py          แชทใน terminal
web.py           เซิร์ฟเวอร์หน้าเว็บ (Flask)
templates/       หน้าเว็บ
```

## หมายเหตุ

- เปิด server-side fallback ไว้ (เฉพาะ Opus 5.5 / Sonnet 5.5): ถ้าโมเดลปฏิเสธคำขอ ระบบส่งต่อให้โมเดลสำรอง
- บทสนทนาบนหน้าเว็บเก็บในหน่วยความจำ ปิดโปรแกรมแล้วหาย
- หน้าเว็บนี้สำหรับใช้บนเครื่องตัวเอง (127.0.0.1) ไม่ควรเปิดให้คนอื่นเข้าโดยไม่มีระบบ login เพราะจะใช้ key ของคุณ
- ไฟล์ `.env` อยู่ใน `.gitignore` ไม่ถูก push ขึ้น GitHub
