#!/usr/bin/env python3
"""گزارش انجام کار هر تسک (حافظهٔ مشترک روش کار) — دستور ممضی و امیرحسین، ۴ آبان ۱۴۰۵.

بعد از «انجام شد» هر تسک، یک گزارش Markdown از روند، متد، تصمیم‌ها، تأییدها، خروجی‌ها و درس‌ها ساخته می‌شود و
در همهٔ حافظه‌های مشترک می‌نشیند: مخزن (kb/tasks/<id>.md + kb/tasks/INDEX.md) برای ایجنت و Claude Code،
ضمیمهٔ همان تسک در برد (md + نسخهٔ خوانا؛ ولت با `vault.py ingest` برش می‌دارد)، و برای تسک‌های فصل‌دار برندبوک یک خط در تاریخچهٔ برندبوک.

  taskreport.py make <id> [--method روند.md] [--lessons "درس ۱ | درس ۲"] [--tools "ffmpeg، Remotion"] [--local "E:\\…"] [--no-attach] [--no-bb]
  taskreport.py pending [--days 21]      تسک‌های done بدون گزارش (یا با گزارش قدیمی‌تر از آخرین تغییر)
  taskreport.py index                    بازسازی kb/tasks/INDEX.md

قاعده: بدون مبلغ، قرارداد، پرداخت و محتوای حساس ولت (همان خط قرمزهای منشور). بخش «روند و متد» و «درس‌ها» را
نویسنده (ایجنت یا Claude Code) از تجربهٔ واقعی کار پر می‌کند؛ اگر خالی بماند، از تاریخچه و کامنت‌ها خودکار ساخته می‌شود.
"""
import argparse, datetime, json, os, re, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import board as B

REPO = os.path.dirname(HERE)
KB = os.path.join(REPO, 'kb', 'tasks')
NAMES = {'M': 'ممضی', 'A': 'امیرحسین', 'C': 'امیررضا', 'CL': 'Claude', 'T': 'همکار گلیچ‌لب'}
ST = {'done': 'انجام شد', 'doing': 'در جریان', 'review': 'در انتظار تأیید', 'todo': 'برنامه‌ریزی‌شده', 'paused': 'متوقف',
      'replan': 'بازبرنامه‌ریزی', 'budget': 'منتظر بودجه'}
MONEY = re.compile(r'(\d[\d٬,\.]*\s*(تومان|ریال|میلیون|هزار تومان))|(مبلغ|قرارداد|پرداخت|فاکتور)')

def nm(x): return NAMES.get(x, x or '—')
def jd(v): return B.fmt_j(v) if isinstance(v, int) else (v or '—')
def ms2j(ms):
    d = datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(hours=3, minutes=30)
    return B.fmt_j(B.g2d(d.year, d.month, d.day)) + d.strftime(' %H:%M')
def clean(s):
    """خط قرمز: جمله‌هایی که مبلغ یا قرارداد دارند حذف می‌شوند."""
    out = []
    for line in (s or '').splitlines():
        out.append('(حذف شد: مالی/قراردادی)' if MONEY.search(line) else line)
    return '\n'.join(out).strip()

def gather(tid):
    B.ensure()
    T = B.load('tasks'); i = B.find(T, tid); t = T[i]
    Cm = sorted([c for c in B.load('comments').values() if c.get('task') == i], key=lambda c: c.get('at', 0))
    try: L = [e for e in B.load('log').values() if e.get('task') == i]
    except Exception: L = []
    L.sort(key=lambda e: e.get('at', 0))
    try: I = {k: v for k, v in B.load('content_items').items() if v.get('boardTask') == i or i in sum([x if isinstance(x, list) else [x] for x in (v.get('stageTasks') or {}).values()], [])}
    except Exception: I = {}
    svc = {}
    try: svc = {x['id']: x.get('n') for x in B.load('cfg')['main'].get('services') or []}
    except Exception: pass
    return i, t, Cm, L, I, svc, T

def build(tid, method='', lessons='', tools='', local=''):
    i, t, Cm, L, I, svc, T = gather(tid)
    title = t.get('title') or t.get('t')
    md = ['# گزارش انجام کار: %s' % title, '',
          '> حافظهٔ مشترک روش کار سوسیسا · ساخته‌شده %s با `tools/taskreport.py` · شناسهٔ تسک: `%s`' % (ms2j(int(time.time() * 1000)), i), '',
          '| | |', '|---|---|',
          '| وضعیت | %s |' % ST.get(t.get('status'), t.get('status')),
          '| خدمت | %s |' % (svc.get(t.get('svc')) or t.get('svc') or '—'),
          '| مسئول | %s |' % nm(t.get('owner')),
          '| همکاران | %s |' % ('، '.join(nm(x) for x in t.get('with') or []) or '—'),
          '| شروع · موعد · پایان | %s · %s · %s |' % (jd(t.get('start')), jd(t.get('due')), jd(t.get('doneAt'))),
          '| پیش‌نیازها | %s |' % ('، '.join('«%s»' % (T.get(d, {}).get('title') or T.get(d, {}).get('t') or d) for d in t.get('deps') or []) or '—')]
    folders = [v.get('folder') for v in I.values() if v.get('folder')]
    if local or folders: md.append('| پوشهٔ کاری | %s |' % '، '.join([local] if local else folders))
    md += ['', '## چی بود و چرا', clean(t.get('notes')) or '—', '']
    md += ['## روند و متد کار']
    if method: md += [clean(method), '']
    else:
        md += ['(خودکار از تاریخچه؛ نویسندهٔ کار باید روند واقعی را با `--method` کامل کند)', '']
        for e in L: md.append('- %s · %s · %s' % (ms2j(e['at']), nm(e.get('by')), clean(e.get('text', ''))[:220]))
        md.append('')
    if tools: md += ['**ابزارها:** ' + tools, '']
    ch = t.get('check') or []
    aps = [c for c in ch if 'امیررضا' in c.get('x', '')]
    md += ['## تأییدها و تصمیم‌ها']
    md += ['- [%s] %s' % ('x' if c.get('done') else ' ', c['x']) for c in aps] or ['- تأیید ثبت‌شده‌ای روی تسک نیست']
    for k, v in I.items():
        for s in ('concept', 'scenario', 'storyboard', 'caption', 'qc'):
            a = (v.get(s) or {}).get('ap') or {}
            if a.get('status'): md.append('- برد محتوا «%s» · %s: %s %s' % (v.get('title'), s, a.get('status'), a.get('note', '')))
    md += ['', '## چک‌لیست']
    md += ['- [%s] %s' % ('x' if c.get('done') else ' ', c['x']) for c in ch if c not in aps] or ['—']
    md += ['', '## خروجی‌ها و فایل‌ها']
    fs = [f for f in t.get('files') or [] if not (f.get('name') or '').startswith('گزارش انجام کار')]
    md += ['- %s%s' % (f.get('name'), ' (نسخه %d)' % (len(f.get('vers') or []) + 1) if f.get('vers') else '') for f in fs] or ['—']
    for k, v in I.items():
        md.append('- برد محتوا: «%s» · مرحله: %s · انتشار: %s' % (v.get('title'), v.get('stage'), v.get('publishedAt') or v.get('date') or '—'))
    md += ['', '## بریف و پرامپت']
    for k, l in (('briefNote', 'یادداشت مدیر'), ('promptNote', 'پرامپت اجرا'), ('ideaNote', 'ایده‌ها')):
        if t.get(k): md += ['**%s:** %s' % (l, clean(t[k])), '']
    for k, v in I.items():
        p = (v.get('edit') or {}).get('prompt')
        if p: md += ['**پرامپت تدوین «%s»:**' % v.get('title'), '```', p, '```', '']
    md += ['## گفتگو روی تسک']
    md += ['- %s · %s: %s' % (ms2j(c['at']), nm(c.get('by')), clean(c.get('text', '')).replace('\n', ' ')[:600]) for c in Cm] or ['—']
    md += ['', '## درس‌ها و قاعدهٔ قابل تکرار']
    md += ['- ' + x.strip() for x in lessons.split('|') if x.strip()] if lessons else ['- (نویسنده پر کند: چی جواب داد، چی نه، دفعهٔ بعد چطور سریع‌تر؛ قاعدهٔ ثابت ← `agent/knowledge/14-learnings.md` و ماژول مربوط)']
    return i, t, '\n'.join(md) + '\n'

def update_index():
    os.makedirs(KB, exist_ok=True)
    rows = []
    for f in sorted(os.listdir(KB)):
        if not f.endswith('.md') or f == 'INDEX.md': continue
        head = open(os.path.join(KB, f), encoding='utf8').readline().strip().lstrip('# ').replace('گزارش انجام کار: ', '')
        rows.append('- [%s](%s)' % (head, f))
    open(os.path.join(KB, 'INDEX.md'), 'w', encoding='utf8').write(
        '# گزارش‌های انجام کار (حافظهٔ مشترک روش کار)\n\n> هر تسکی که تمام می‌شود یک گزارش اینجا دارد (`tools/taskreport.py`). ایجنت، Claude Code و دستیار پروژه قبل از کار مشابه همین‌ها را می‌خوانند.\n\n' + '\n'.join(rows) + '\n')

def cmd_make(a):
    method = open(a.method, encoding='utf8').read() if a.method and os.path.isfile(a.method) else (a.method or '')
    i, t, md = build(a.id, method, a.lessons or '', a.tools or '', a.local or '')
    os.makedirs(KB, exist_ok=True)
    p = os.path.join(KB, '%s.md' % i)
    open(p, 'w', encoding='utf8').write(md); update_index()
    print('ok', os.path.relpath(p, REPO))
    title = t.get('title') or t.get('t')
    if not a.no_attach:
        r = subprocess.run([sys.executable, os.path.join(HERE, 'board.py'), 'attach', i, p, '--name', 'گزارش انجام کار · %s.md' % title[:60]], capture_output=True, text=True)
        print(r.stdout.strip() or r.stderr.strip())
    def mut():
        T = B.load('tasks'); t2 = T[i]; t2['reportAt'] = int(time.time() * 1000); B.dump('tasks', T)
    B.commit_push('tasks %s report' % i, mut)
    if t.get('bb') and not a.no_bb and os.path.isdir('/home/claude/susisa-brandbook'):
        r = subprocess.run([sys.executable, os.path.join(HERE, 'brandbook.py'), 'log', 'روند کار «%s» ثبت شد (فصل %s)' % (title, t['bb'])], capture_output=True, text=True)
        print('brandbook:', (r.stdout or r.stderr).strip()[:200])

def cmd_pending(a):
    B.ensure(); T = B.load('tasks'); lim = B.today_j() - a.days
    for k, t in sorted(T.items(), key=lambda kv: kv[1].get('doneAt') or 0):
        if t.get('status') != 'done' or not t.get('doneAt') or t['doneAt'] < lim: continue
        if t.get('reportAt') and t['reportAt'] >= (t.get('upd') or 0) - 60000: continue
        print('%-14s %s  %s  %s' % (k, jd(t.get('doneAt')), nm(t.get('owner')), t.get('title') or t.get('t')))

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = ap.add_subparsers(dest='cmd', required=True)
    m = s.add_parser('make'); m.add_argument('id'); m.add_argument('--method'); m.add_argument('--lessons'); m.add_argument('--tools'); m.add_argument('--local')
    m.add_argument('--no-attach', action='store_true'); m.add_argument('--no-bb', action='store_true')
    p = s.add_parser('pending'); p.add_argument('--days', type=int, default=21)
    s.add_parser('index')
    a = ap.parse_args()
    {'make': cmd_make, 'pending': cmd_pending, 'index': lambda a: (update_index(), print('ok'))}[a.cmd](a)

if __name__ == '__main__': main()
