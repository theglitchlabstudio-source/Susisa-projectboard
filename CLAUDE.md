# راهنمای Claude برای برد سوسیسا

برد زنده یک PWA ایستا روی GitHub Pages است (`index.html`) و دادهٔ مشترکش روی شاخهٔ **`board-data`** همین مخزن می‌ماند. Claude در برد پروفایل جدا دارد: `id: CL`، نام Claude، ربات (`bot:true`)؛ می‌شود به او تسک سپرد و هر تغییری که می‌دهد با `by:"CL"` ثبت می‌شود.

## قاعده‌ها
- **داده** (تسک، وضعیت، یادداشت، کامنت) را فقط با `python3 tools/board.py` تغییر بده؛ هر دستور یک commit روی `board-data` است و برد همه تا حدود ۱۵ ثانیه بعد آن را نشان می‌دهد. نسخهٔ جدید `index.html` لازم نیست.
- **کد برد** (`index.html`, `sw.js`, …) فقط وقتی قابلیت یا باگ تغییر می‌کند روی `main` می‌رود. با push روی main، Pages خودکار آپدیت می‌شود و دستگاه‌ها بنر «نسخهٔ جدید» می‌گیرند. بعد از تغییر کد، تست Playwright با mock همین API را اجرا کن (نمونه در تاریخچهٔ commit).
- شاخهٔ `board-data` را دستی ویرایش نکن، فقط با ابزار؛ فایل‌ها `data/{cfg,tasks,notes,comments,profiles}.json` با ساختار `{"v":1,"docs":{id:{…}}}` هستند و ضمیمه‌ها در `files/`.
- توکن یا رمز را هیچ‌جا ننویس (نه کد، نه commit، نه حافظه).
- تاریخ‌ها داخل داده عدد روز جولیانی‌اند؛ ابزار ورودی/خروجی جلالی `1405/07/20` دارد.

## دستورها
```
python3 tools/board.py list [--status doing] [--svc sv2] [--owner M] [--q متن]
python3 tools/board.py show <id>
python3 tools/board.py status <id> done|doing|review|budget|paused|replan|todo
python3 tools/board.py set <id> due=1405/07/20 prio=p1 owner=A notes="متن" urgent=true
python3 tools/board.py assign <id> CL
python3 tools/board.py add "عنوان" --svc sv2 --due 1405/07/25 --owner M
python3 tools/board.py comment <id> "پیام"
python3 tools/board.py note "یادداشت امروز" [--day 1405/07/12]
python3 tools/board.py svc list|add|edit [id] [--name ... --short ... --color ... --after ... --side true]
python3 tools/board.py rm <id>

# ولت خصوصی Obsidian (مخزن susisa-vault، clone در /home/claude/susisa-vault)
python3 tools/vault.py ingest [--dry] | scan | set <path> k=v… | link <task> <path> [نام] | render | save "پیام"
```
# بستهٔ تسک برای دستیار تسک در Claude (agent/copilot/)
python3 tools/brief.py <id>… | --open [--owner M] | --critical [--stdout]
بریف‌ها در board-data: `data/briefs.json` (زیر هر تسک در برد دیده می‌شود)؛ متن دستی agent: `board.py set <id> briefNote="…"`؛ `--vault` نسخهٔ کامل در ولت. تحویل‌ها: کامنت‌های «@Claude تحویل تسک …» (قالب agent/copilot/HANDOFF.md).

محتوای ولت را هرگز در این مخزن یا board-data کپی نکن؛ در برد فقط لینک. راهنما: `agent/knowledge/12-vault-librarian.md`.
اولین اجرا شاخهٔ داده را در `~/.cache/susisa-board-data` می‌گیرد (`BOARD_DIR` برای تغییر). نیاز: دسترسی push به این مخزن (در Claude Code با add_repo/ورود GitHub).

## رابط برد (نسخهٔ ۹)
پنج صفحه: **میز کار** (کارهای هر نفر، گیت‌ها، مسیر بحرانی افتتاحیه، صندوق Claude با تأیید/رد پیشنهادها، منتظر امیررضا، یادداشت امروز)، **برنامه** (همهٔ تسک‌ها بر اساس خدمت ← مرحله، با فیلتر)، **تقویم** (روزبه‌روز یا ماه، کشیدن برای تغییر موعد)، **گفتگو** (یادداشت‌ها و کامنت‌ها)، **فایل‌ها** (همهٔ ضمیمه‌های برد با گروه‌بندی خدمت/نوع/تسک، فیلتر، جستجو، آپلود، دیدن داخل برد با نمایشگر مناسب گوشی، دانلود و «نسخهٔ جدید»؛ هر فایل `vers` دارد: نسخه‌های قبلی)، **بیشتر** (پروفایل، اتصال GitHub، ظاهر، دسته‌ها). جزئیات تسک در پنل کناری/برگهٔ پایین. فیلدهای تازهٔ تسک: `kind` (G/S/D/E/I/M) و `stage`.

## یادآوری
- اولویت‌ها و سه دسته‌بندی مستقل: نوع خدمت (`svc`)، فاز (`phase`/از روی موعد)، وضعیت (`status`).
- قرارداد و پرداخت داخل برد/رودمپ نیست.
- فایل ضمیمه روی `files/` شاخهٔ داده می‌رود؛ اگر Claude فایل اضافه کرد، آن را با commit به `files/` بگذار و در `files` تسک `{kind:"gh",id,path,name,type,size}` ثبت کن (نسخهٔ جدید: آرایهٔ `vers` از نسخه‌های قبلی).
