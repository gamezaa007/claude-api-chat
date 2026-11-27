# Claude API Chat (Python)

แชทใน terminal กับ Claude (`claude-opus-5-5`) ผ่าน Anthropic Python SDK

## ติดตั้ง

```powershell
python -m pip install -r requirements.txt
copy .env.example .env
```

แล้วเปิดไฟล์ `.env` ใส่ `ANTHROPIC_API_KEY` ของคุณ (สร้างได้ที่ https://platform.claude.com/settings/keys)

## ใช้งาน

```powershell
python main.py
```

## รายละเอียด

- โมเดล: `claude-opus-5-5` พร้อม adaptive thinking, effort `medium`
- ตอบแบบ streaming (เห็นข้อความทีละส่วน)
- เปิด server-side fallback: ถ้าโมเดลปฏิเสธคำขอ จะส่งต่อให้โมเดลสำรองอัตโนมัติ
- ไฟล์ `.env` อยู่ใน `.gitignore` ไม่ถูก push ขึ้น GitHub
