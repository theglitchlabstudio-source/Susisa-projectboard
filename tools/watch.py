#!/usr/bin/env python3
"""ناظر پروژه: بررسی خودکار خلأها، تضادها، ریسک‌ها و خطر تصمیم/روش غلط روی دادهٔ زندهٔ برد.
قاعده‌ها (R1…R15) عین ماژول agent/knowledge/24-supervisor-role.md هستند و همان‌ها در خود برد (پنل «ناظر پروژه») اجرا می‌شوند.

  watch.py [--who M] [--min 1] [--json] [--md]
      --who: فقط هشدارهای مربوط به یک نفر (شناسه) + هشدارهای کلی   --min: حداقل شدت (1 جزئی، 2 مهم، 3 بحرانی)
"""
import json, os, re, sys, datetime, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board as B

OPEN_DAY = None  # از cfg: گیت افتتاحیه
PR = {'p0': 0, 'p1': 1, 'p2': 2, 'p3': 3}
MONEY = re.compile(r'(\d[\d,٬٫.۰-۹]*\s*(میلیون|هزار|تومان|ریال))')
SEV = {3: 'بحرانی', 2: 'مهم', 1: 'جزئی'}

def wd(d): return datetime.date(*B.d2g(d)).weekday()          # دوشنبه 0 … جمعه 4، شنبه 5
def week_start(d): return d - ((wd(d) - 5) % 7)                # شنبه همان هفته
def fa(x): return str(x).translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))
MONTHS = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
def jdh(d):
    y, m, dd = B.d2j(d); return fa('%d %s' % (dd, MONTHS[m - 1]))

def run():
    B.ensure()
    T = B.load('tasks'); C = B.load('comments'); P = B.load('profiles'); cfg = B.load('cfg').get('main', {})
    st = {s['id']: s for s in cfg.get('statuses', [])}
    done = {k for k, v in st.items() if v.get('done')} or {'done'}
    closed = done | {'paused'}
    nm = lambda i: P.get(i, {}).get('name', i or '—')
    today = B.today_j()
    opn = [t for t in T.values() if t.get('status') not in closed and t.get('type') != 'gate' and not (t.get('t') or '').startswith(('پیشنهاد', 'درخواست خدمت'))]
    out = []
    def add(sev, k, text, ids=(), who=(), fix=''):
        out.append({'sev': sev, 'k': k, 'text': text, 'ids': list(ids), 'who': sorted(set(x for x in who if x)), 'fix': fix})
    title = lambda i: T[i].get('t', i)

    # R1 شروع قبل از تمام شدن پیش‌نیاز
    for t in opn:
        for d in t.get('deps', []):
            x = T.get(d)
            if x and x.get('status') not in done and x.get('due') is not None and t.get('start') is not None and x['due'] > t['start'] and x.get('status') not in ('paused',):
                add(2, 'R1', '«%s» قبل از تمام شدن «%s» شروع می‌شود (پیش‌نیازش %s موعد دارد، خودش %s شروع)' % (t['t'], x['t'], jdh(x['due']), jdh(t['start'])), [t['id'], x['id']], [t.get('owner'), x.get('owner')], 'موعد پیش‌نیاز را جلو بکش یا شروع این تسک را عقب ببر')
    # R2 تاریخ برعکس
    for t in opn:
        if t.get('start') is not None and t.get('due') is not None and t['start'] > t['due']:
            add(2, 'R2', '«%s»: شروع بعد از موعد است' % t['t'], [t['id']], [t.get('owner')], 'تاریخ‌ها را درست کن')
    # R3 روز تعطیل
    bad = [t for t in opn if t.get('due') is not None and t['due'] >= today and wd(t['due']) in (3, 4)]
    if bad: add(1, 'R3', '%s تسک در پنج‌شنبه یا جمعه موعد دارند (قاعده: فقط شنبه تا چهارشنبه)' % fa(len(bad)), [t['id'] for t in bad[:8]], [t.get('owner') for t in bad], 'به شنبه تا چهارشنبه ببر')
    # R4 بار هفتگی هر نفر
    byw = {}
    for t in opn:
        if t.get('due') is None or t['due'] < today - 6: continue
        for p in set([t.get('owner')] + (t.get('with') or [])):
            if p in ('T',) and False: continue
            byw.setdefault((p, week_start(t['due'])), []).append(t)
    for (p, w), L in sorted(byw.items(), key=lambda x: x[0][1]):
        own = [t for t in L if t.get('owner') == p]
        if p in (None, 'C') or P.get(p, {}).get('bot'): continue
        n = len(own); hi = len([t for t in own if PR.get(t.get('prio'), 2) <= 1])
        if n >= 9 or hi >= 7: add(3 if n >= 12 else 2, 'R4', 'بار %s در هفتهٔ %s: %s تسک (%s با اولویت بالا)' % (nm(p), jdh(w), fa(n), fa(hi)), [t['id'] for t in own[:6]], [p], 'بخشی را به امیرحسین یا همکار بده، یا موعد را پخش کن')
    # R5 عقب‌افتاده
    late = [t for t in opn if t.get('due') is not None and t['due'] < today]
    crit = [t for t in late if t.get('prio') == 'p0']
    if crit: add(3, 'R5', '%s کار مسیر بحرانی عقب افتاده: %s' % (fa(len(crit)), '، '.join('«%s»' % t['t'] for t in crit[:4])), [t['id'] for t in crit], [t.get('owner') for t in crit], 'امروز تکلیفش را روشن کن: انجام، جابه‌جایی با دلیل، یا واگذاری')
    elif late: add(2, 'R5', '%s کار عقب افتاده' % fa(len(late)), [t['id'] for t in late[:8]], [t.get('owner') for t in late], 'هر کدام: انجام، جابه‌جایی با دلیل یا حذف')
    # R6 باید شروع می‌شد
    miss = [t for t in opn if t.get('status') == 'todo' and t.get('start') is not None and t['start'] < today and not (t.get('due') is not None and t['due'] < today)]
    if len(miss) >= 3: add(1, 'R6', '%s کار تاریخ شروعش گذشته ولی هنوز شروع نشده' % fa(len(miss)), [t['id'] for t in miss[:8]], [t.get('owner') for t in miss], 'وضعیت را به «در جریان» ببر یا تاریخ را اصلاح کن')
    # R7 هفتهٔ خالی
    ends = max([t['due'] for t in T.values() if t.get('due') is not None] + [today])
    w = week_start(today) + 7; empties = []
    while w <= ends:
        if not any(t.get('due') is not None and w <= t['due'] < w + 7 for t in opn): empties.append(w)
        w += 7
    if empties: add(1, 'R7', 'هفته‌هایی بدون هیچ تسک: %s' % '، '.join(jdh(x) for x in empties[:5]), [], [], 'ببین کار این هفته‌ها جا افتاده یا واقعاً خالی است')
    # R8 ورودی کارفرما
    for t in opn:
        if t.get('owner') == 'C' and t.get('due') is not None and t['due'] - today <= 3:
            n = len([x for x in opn if t['id'] in x.get('deps', [])])
            add(2 if t['due'] >= today else 3, 'R8', 'ورودی منتظر امیررضا: «%s» (%s) · %s کار به آن وابسته است' % (t['t'], 'گذشته' if t['due'] < today else 'تا ' + jdh(t['due']), fa(n)), [t['id']], ['M'], 'ممضی در دیدار روزانه پیگیری کند')
    # R9 تصمیم باز با وابسته نزدیک
    for t in opn:
        if t.get('kind') == 'D' or t.get('type') == 'decision':
            ds = [x for x in opn if t['id'] in x.get('deps', []) and x.get('start') is not None and x['start'] - today <= 3]
            if ds: add(3, 'R9', 'تصمیم «%s» هنوز گرفته نشده و %s کار تا ۳ روز دیگر منتظرش‌اند' % (t['t'], fa(len(ds))), [t['id']] + [x['id'] for x in ds[:3]], [t.get('owner')], 'همین هفته تصمیم بگیر؛ گزینه‌ها را با فیلتر هفت بسنج')
    # R10 گیت در خطر
    for g in T.values():
        if g.get('type') != 'gate' or g.get('status') in done or g.get('due') is None: continue
        ds = [T[i] for i in g.get('deps', []) if i in T and T[i].get('status') not in done]
        risky = [x for x in ds if (x.get('due') is not None and x['due'] < today) or x.get('status') in ('budget', 'paused') or unmet_open(T, x, done)]
        if g['due'] - today <= 10 and risky: add(3, 'R10', 'گیت «%s» (%s) در خطر: %s کار پیش‌نیازش عقب یا گیر است' % (re.sub(r'^گیت\s*[۰-۹0-9]+\s*·\s*', '', g['t']), jdh(g['due']), fa(len(risky))), [g['id']] + [x['id'] for x in risky[:4]], ['M'], 'پیش‌نیازهای گیر را اول حل کن')
    # R11 بدون مسئول یا تاریخ
    noo = [t for t in opn if not t.get('owner')]; nod = [t for t in opn if t.get('due') is None and t.get('status') != 'paused' and t.get('start') is None]
    if noo: add(2, 'R11', '%s تسک مسئول ندارند' % fa(len(noo)), [t['id'] for t in noo[:6]], [], 'مسئول بده')
    if nod: add(1, 'R11', '%s تسک باز هیچ تاریخی ندارند' % fa(len(nod)), [t['id'] for t in nod[:6]], [t.get('owner') for t in nod], 'تاریخ بده یا متوقف کن')
    # R12 بن‌بست وابستگی چرخه
    for t in opn:
        if t['id'] in t.get('deps', []): add(2, 'R12', '«%s» به خودش وابسته است' % t['t'], [t['id']], [t.get('owner')], 'وابستگی را بردار')
    # R13 گام برندبوک جا مانده
    for t in T.values():
        if t.get('status') in done and any((c.get('x') or '').startswith('افزودن به برندبوک') and not c.get('done') for c in t.get('check', [])):
            add(1, 'R13', '«%s» تمام شده ولی هنوز به برندبوک اضافه نشده' % t['t'], [t['id']], [t.get('owner'), 'CL'], 'گام «افزودن به برندبوک»')
    # R14 خط قرمز مبلغ در متن عمومی
    leak = [t for t in T.values() if MONEY.search((t.get('t') or '') + ' ' + (t.get('notes') or '') + ' ' + (t.get('briefNote') or ''))]
    if leak: add(3, 'R14', 'احتمال مبلغ یا عدد مالی در متن %s تسک (مخزن عمومی است)' % fa(len(leak)), [t['id'] for t in leak[:6]], ['M', 'CL'], 'مبلغ را حذف کن؛ فقط در ولت خصوصی')
    # R15 پیشنهاد بی‌پاسخ
    props = [t for t in T.values() if (t.get('t') or '').startswith(('پیشنهاد', 'درخواست خدمت')) and t.get('status') not in closed]
    old = [t for t in props if not any(c.get('task') == t['id'] and re.match(r'^(تأیید|تایید|رد)', (c.get('text') or '').strip()) for c in C.values())]
    if len(old) >= 3: add(1, 'R15', '%s پیشنهاد منتظر تصمیم ممضی است' % fa(len(old)), [t['id'] for t in old[:6]], ['M'], 'در صندوق Claude تأیید یا رد کن')
    out.sort(key=lambda x: -x['sev'])
    return out, nm, T

def unmet_open(T, x, done):
    return any(T.get(d) and T[d].get('status') not in done and T[d].get('due') is not None and x.get('start') is not None and T[d]['due'] > x['start'] for d in x.get('deps', []))

def render_md(out, nm, T, limit=40):
    if not out: return '- هشداری نیست.\n'
    o = []
    for r in out[:limit]:
        who = '، '.join(nm(w) for w in r['who'])
        o.append('- **%s** · %s%s%s' % (SEV[r['sev']], r['text'], (' — برای: ' + who) if who else '', (' ← ' + r['fix']) if r['fix'] else ''))
    return '\n'.join(o) + '\n'

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--who'); ap.add_argument('--min', type=int, default=1); ap.add_argument('--json', action='store_true'); ap.add_argument('--md', action='store_true')
    a = ap.parse_args(); out, nm, T = run()
    out = [r for r in out if r['sev'] >= a.min and (not a.who or a.who in r['who'] or not r['who'])]
    if a.json: print(json.dumps(out, ensure_ascii=False, indent=1))
    else: print(render_md(out, nm, T))
if __name__ == '__main__': main()
