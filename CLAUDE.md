# راهنمای Claude برای برد سوسیسا

برد زنده یک PWA ایستا روی GitHub Pages است (`index.html`) و دادهٔ مشترکش روی شاخهٔ **`board-data`** همین مخزن می‌ماند. Claude در برد پروفایل جدا دارد: `id: CL`، نام Claude، ربات (`bot:true`)؛ می‌شود به او تسک سپرد و هر تغییری که می‌دهد با `by:"CL"` ثبت می‌شود.

## قاعده‌ها
- **داده** (تسک، وضعیت، یادداشت، کامنت) را فقط با `python3 tools/board.py` تغییر بده؛ هر دستور یک commit روی `board-data` است و برد همه تا حدود ۱۵ ثانیه بعد آن را نشان می‌دهد. نسخهٔ جدید `index.html` لازم نیست.
- **کد برد** (`index.html`, `sw.js`, …) فقط وقتی قابلیت یا باگ تغییر می‌کند روی `main` می‌رود. با push روی main، Pages خودکار آپدیت می‌شود و دستگاه‌ها بنر «نسخهٔ جدید» می‌گیرند. بعد از تغییر کد، تست Playwright با mock همین API را اجرا کن (نمونه در تاریخچهٔ commit).
- شاخهٔ `board-data` را دستی ویرایش نکن، فقط با ابزار؛ فایل‌ها `data/{cfg,tasks,notes,comments,profiles,briefs,log}.json` با ساختار `{"v":1,"docs":{id:{…}}}` هستند و ضمیمه‌ها در `files/`.
- توکن یا رمز را هیچ‌جا ننویس (نه کد، نه commit، نه حافظه).
- تاریخ‌ها داخل داده عدد روز جولیانی‌اند؛ ابزار ورودی/خروجی جلالی `1405/07/20` دارد.

## دستورها
```
python3 tools/board.py list [--status doing] [--svc sv2] [--owner M] [--q متن]
python3 tools/board.py show <id>
python3 tools/board.py status <id> done|doing|review|budget|paused|replan|todo
python3 tools/board.py set <id> due=1405/07/20 prio=p1 owner=A notes="متن" urgent=true
python3 tools/board.py assign <id> CL
python3 tools/board.py set <id> with=A,M      # همکاران: تسک روی میز کار آن‌ها هم دیده می‌شود
python3 tools/board.py add "عنوان" --svc sv2 --due 1405/07/25 --owner M
python3 tools/board.py comment <id> "پیام"
python3 tools/board.py note "یادداشت امروز" [--day 1405/07/12]
python3 tools/board.py svc list|add|edit [id] [--name ... --short ... --color ... --after ... --side true]
python3 tools/board.py rm <id>
python3 tools/board.py log --after <ms> | --hours 24 [--others] [--task id] [--by M] [--json]   # تاریخچه: تغییرها + کامنت + یادداشت
python3 tools/board.py now                                  # زمان فعلی به ms برای last_run_ms در STATUS
python3 tools/board.py attach <id> <file> [--name "نام"]    # فایل روی تسک (با نسخه)؛ برای .md نسخهٔ خوانای HTML هم ضمیمه می‌شود
python3 tools/board.py check <id> add|done|undo "متن"  ·  check bbstep   # چک‌لیست؛ bbstep = گام «افزودن به برندبوک» برای همهٔ تسک‌های برندبوک
python3 tools/board.py report add <file.md> | list           # گزارش در بخش «گزارش کار» برد (md + HTML)
python3 tools/report.py weekly [--analysis تحلیل.md] [--save]  ·  report.py digest -o kb/live.md   # گزارش هفتگی؛ خلاصهٔ زنده برای دستیار
python3 tools/render.py file.md [--docx]                     # نسخهٔ خوانا و قابل چاپ (HTML، با نمونهٔ رنگ و بلوک ```palette)
python3 tools/brandbook.py chapters | show <n> | upsert <n> <بخش> --md f.md --st final --task <id> | log "…" | save "…"   # برندبوک زنده (ماژول ۲۳)

# ولت خصوصی Obsidian (مخزن susisa-vault، clone در /home/claude/susisa-vault)
python3 tools/vault.py ingest [--dry] | scan | set <path> k=v… | link <task> <path> [نام] | relink | render | save "پیام"
```
# بستهٔ تسک برای دستیار تسک در Claude (agent/copilot/)
python3 tools/brief.py <id>… | --open [--owner M] | --critical [--stdout]
بریف‌ها در board-data: `data/briefs.json` (زیر هر تسک در برد دیده می‌شود)؛ متن دستی agent: `board.py set <id> briefNote="…" promptNote="…" ideaNote="…"` (یادداشت مدیر، پرامپت اجرا، ایده‌ها؛ ماژول ۱۳)؛ `--vault` نسخهٔ کامل در ولت. تحویل‌ها: کامنت‌های «@Claude تحویل تسک …» (قالب agent/copilot/HANDOFF.md).

از ولت فقط اسناد `sens=normal` (≤۵MB) و فقط با `vault.py link` در board-data کپی می‌شوند؛ حساس فقط لینک، محرمانه هرگز. راهنما: `agent/knowledge/12-vault-librarian.md`.
اولین اجرا شاخهٔ داده را در `~/.cache/susisa-board-data` می‌گیرد (`BOARD_DIR` برای تغییر). نیاز: دسترسی push به این مخزن (در Claude Code با add_repo/ورود GitHub).

## رابط برد (نسخهٔ ۱۳)
ظاهر اپ: هدر با صفحه حرکت می‌کند (دسکتاپ: با اسکرول پایین پنهان)، نوار پایین شناور، چیپ و دکمه‌های سه‌بعدی آیکن‌دار. **برنامه**: کاشی‌های وضعیت (باز، عقب، ۷ روز، بحرانی، انجام‌شده، همه)، فیلتر مسئول با آواتار، دسته‌بندی، «نمایش همهٔ تسک‌ها»، دو نما: فهرست و زمان‌بندی هفته‌به‌هفته. **تقویم**: ماه گرافیکی (رنگ شلوغی، نقطهٔ رنگی خدمت روی گوشی) و روزبه‌روز کارتی. **گزارش کار**: گزارش هفتگی فوری از برد (md و HTML)، درخواست گزارش تحلیلی از Claude، گزارش‌های ذخیره‌شده (مجموعهٔ `reports`). صفحه‌ها: **تازه‌ها** (تاریخچهٔ همهٔ تغییرها/کامنت‌ها/یادداشت‌ها به تفکیک روز، نشان تعداد نخوانده روی تب و عنوان صفحه، کادر «تازه از آخرین بازدید» در میز کار، اعلان مرورگر روی هر دستگاه)، **میز کار** (کارهای هر نفر، گیت‌ها، مسیر بحرانی افتتاحیه، صندوق Claude با تأیید/رد پیشنهادها، منتظر امیررضا، یادداشت امروز)، **برنامه** (همهٔ تسک‌ها بر اساس خدمت ← مرحله، با فیلتر)، **تقویم** (روزبه‌روز یا ماه، کشیدن برای تغییر موعد)، **گفتگو** (یادداشت‌ها و کامنت‌ها)، **فایل‌ها** (همهٔ ضمیمه‌های برد با گروه‌بندی خدمت/نوع/تسک، فیلتر، جستجو، آپلود، دیدن داخل برد با نمایشگر مناسب گوشی، دانلود و «نسخهٔ جدید»؛ هر فایل `vers` دارد: نسخه‌های قبلی)، **بیشتر** (پروفایل، اتصال GitHub، ظاهر، دسته‌ها). جزئیات تسک در پنل کناری/برگهٔ پایین. فیلدهای تازهٔ تسک: `kind` (G/S/D/E/I/M) و `stage`.

## یادآوری
- اولویت‌ها و سه دسته‌بندی مستقل: نوع خدمت (`svc`)، فاز (`phase`/از روی موعد)، وضعیت (`status`).
- قرارداد و پرداخت داخل برد/رودمپ نیست.
- فایل ضمیمه روی `files/` شاخهٔ داده می‌رود؛ اگر Claude فایل اضافه کرد، آن را با commit به `files/` بگذار و در `files` تسک `{kind:"gh",id,path,name,type,size}` ثبت کن (نسخهٔ جدید: آرایهٔ `vers` از نسخه‌های قبلی).

- سند ولتِ عادی (≤۵MB) با `vault.py link` در `files/` برد کپی می‌شود (`kind:gh` + فیلد `vault`/`sha`)؛ حساس فقط `kind:link` است و برد (v10) با توکن همان دستگاهِ کاربر از مخزن خصوصی ولت می‌خواند. هیچ توکنی در داده/پروفایل برد ذخیره نمی‌شود.
- تاریخچه (`data/log.json`): برد و `board.py` هر تغییر تسک را خودکار ثبت می‌کنند (`{id,at,by,task,k,text}`، k: done/status/edit/file/new/del/brief)؛ ۶۰ روز / ۱۵۰۰ رویداد نگه داشته می‌شود. چرخهٔ روزانهٔ ایجنت (سه اجرا، اجرای دستورهای ممضی، یادگیری و تحقیق): `agent/knowledge/13-daily-cycle-and-learning.md`؛ دفتر درس‌ها: `14-learnings.md`.
- هر تسک **همیشه مسئول دارد** (`owner`). `with` = همکاران (آرایهٔ شناسه)؛ تسک روی میز کار مسئول و همکاران دیده می‌شود. مسئول `T` («همکار گلیچ‌لب») یعنی کار همکاری تیم و روی میز کار **همه** دیده می‌شود. ایجنت: تسک بدون مسئول نساز (`board.py add --owner`)؛ برای کار مشترک `with` را تنظیم کن.
- تقویم (v12): کلیک روی هر روز ← صفحهٔ روز (کارت بزرگ هر تسک زیر هم با وضعیت قابل تغییر، مسئول/همکار، بازه، پیش‌نیاز باز، توضیح؛ تسک‌های در جریان؛ یادداشت‌های روز؛ اتفاق‌های برد آن روز) با دکمهٔ روز قبل/بعد و «روز بعدی با تسک».
- **لحن هر متنی که تیم می‌خونه** (کامنت، یادداشت، بریف، پیام): محاوره‌ای و دوستانه، کوتاه، اول نتیجه؛ **بدون کد تسک** (فقط عنوان یا خلاصه‌اش)، اسم آدم‌ها به‌جای M/A/T/C، تاریخ آدمیزادی. راهنما: `agent/knowledge/00-voice.md`.
