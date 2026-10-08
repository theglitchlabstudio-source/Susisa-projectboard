#!/usr/bin/env python3
"""گزارش‌ها و خلاصهٔ زندهٔ برد (فارسی، خوانا، بدون کد تسک).

  report.py weekly [--days 7] [--analysis جمع‌بندی.md] [-o out.md] [--save]
      گزارش کار هفتگی از روی دادهٔ برد. --analysis: متن تحلیل Claude بالای گزارش.
      --save: فایل md و نسخهٔ خوانای HTML روی برد (بخش «گزارش‌ها») ذخیره می‌شود.
  report.py digest [-o kb/live.md]
      خلاصهٔ زندهٔ برد برای «دستیار پروژه» (از هر دستگاه، از روی گیت‌هاب/وب). ایجنت آخر هر اجرا می‌سازد و روی main می‌گذارد.
"""
import json, os, sys, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board as B

MONTHS = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
FA = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
def fa(x): return str(x).translate(FA)
def jd(d):
    if d is None: return 'بی‌تاریخ'
    y, m, dd = B.d2j(d); return fa('%d %s' % (dd, MONTHS[m - 1]))
def ms_day(ms):
    t = time.localtime(ms / 1000); return B.g2d(t.tm_year, t.tm_mon, t.tm_mday)

def load_all():
    B.ensure()
    cfg = B.load('cfg').get('main', {})
    return dict(T=B.load('tasks'), C=B.load('comments'), N=B.load('notes'), L=B.load('log'), P=B.load('profiles'), BR=B.load('briefs'),
                st={s['id']: s for s in cfg.get('statuses', [])}, sv={s['id']: s for s in cfg.get('services', [])})

def helpers(D):
    nm = lambda i: D['P'].get(i, {}).get('name', i or '—')
    done = {k for k, v in D['st'].items() if v.get('done')} or {'done'}
    closed = done | {'paused'}
    stn = lambda s: D['st'].get(s, {}).get('n', s)
    svn = lambda s: D['sv'].get(s, {}).get('n', s or 'سایر')
    return nm, done, closed, stn, svn

def line(t, nm, stn, show_status=True):
    bits = ['**%s**' % t.get('t'), 'مسئول: ' + nm(t.get('owner'))]
    if t.get('with'): bits.append('همکار: ' + '، '.join(nm(x) for x in t['with']))
    if t.get('due') is not None: bits.append('موعد ' + jd(t['due']))
    if show_status: bits.append(stn(t.get('status')))
    return '- ' + ' · '.join(bits)

def weekly(days=7, analysis=None):
    D = load_all(); nm, done, closed, stn, svn = helpers(D); T = D['T']; today = B.today_j(); start = today - days + 1
    tasks = [t for t in T.values() if t.get('type') != 'gate']
    finished = [t for t in tasks if t.get('status') in done and t.get('doneAt') is not None and start <= t['doneAt'] <= today]
    late = sorted([t for t in tasks if t.get('status') not in closed and t.get('due') is not None and t['due'] < today], key=lambda t: t['due'])
    nxt = sorted([t for t in tasks if t.get('status') not in closed and t.get('due') is not None and today <= t['due'] <= today + 7], key=lambda t: t['due'])
    waiting = [t for t in tasks if t.get('status') not in closed and (t.get('owner') == 'C' or t.get('status') == 'budget')]
    props = [t for t in tasks if (t.get('t') or '').startswith('پیشنهاد') and t.get('status') not in closed]
    gates = sorted([t for t in T.values() if t.get('type') == 'gate'], key=lambda g: g.get('due') or 0)
    allw = [t for t in tasks]; pct = round(100 * len([t for t in allw if t.get('status') in done]) / max(1, len(allw)))
    ev = [e for e in D['L'].values() if ms_day(e.get('at', 0)) >= start]
    cm = [c for c in D['C'].values() if ms_day(c.get('at', 0)) >= start]
    who = {}
    for e in ev + cm: who[e.get('by')] = who.get(e.get('by'), 0) + 1
    o = ['# گزارش کار هفتگی سوسیسا', '', '**بازه:** %s تا %s · **ساخته‌شده:** %s' % (jd(start), jd(today), jd(today)), '']
    if analysis: o += ['## جمع‌بندی Claude', '', analysis.strip(), '']
    o += ['## در یک نگاه', '',
          '| شاخص | این هفته |', '|---|---|',
          '| تسک تمام‌شده | %s |' % fa(len(finished)), '| عقب‌افتاده (الان) | %s |' % fa(len(late)),
          '| موعد هفتهٔ بعد | %s |' % fa(len(nxt)), '| منتظر امیررضا یا بودجه | %s |' % fa(len(waiting)),
          '| پیشنهاد منتظر تأیید | %s |' % fa(len(props)), '| پیشرفت کل برنامه | %s٪ |' % fa(pct),
          '| فعالیت روی برد (تغییر و پیام) | %s |' % '، '.join('%s %s' % (nm(k), fa(v)) for k, v in sorted(who.items(), key=lambda x: -x[1])), '']
    o += ['## کارهای تمام‌شده', '']
    if finished:
        by = {}
        for t in sorted(finished, key=lambda t: t['doneAt']): by.setdefault(svn(t.get('svc')), []).append(t)
        for k, L in by.items(): o += ['### ' + k] + [line(t, nm, stn, False) + ' · تمام شد ' + jd(t['doneAt']) for t in L] + ['']
    else: o += ['این هفته تسکی بسته نشد.', '']
    o += ['## عقب‌افتاده‌ها', ''] + ([line(t, nm, stn) for t in late] or ['چیزی عقب نیست 👌']) + ['']
    o += ['## هفتهٔ بعد', ''] + ([line(t, nm, stn) for t in nxt] or ['موعدی ثبت نشده.']) + ['']
    o += ['## گیت‌ها', '']
    for g in gates:
        ds = [T[i] for i in (g.get('deps') or []) if i in T]; dn = len([x for x in ds if x.get('status') in done])
        o.append('- **%s** · %s · %s از %s پیش‌نیاز تمام' % (g.get('t'), jd(g.get('due')), fa(dn), fa(len(ds))))
    o += ['', '## منتظر امیررضا یا بودجه', ''] + ([line(t, nm, stn) for t in waiting] or ['چیزی منتظر نیست.']) + ['']
    o += ['## پیشنهادهای منتظر تأیید ممضی', ''] + (['- ' + t.get('t') for t in props] or ['پیشنهاد بازی نیست.']) + ['']
    notes = sorted([n for n in D['N'].values() if n.get('by') == 'CL' and (n.get('day') or 0) >= start], key=lambda n: n.get('at', 0))
    if notes:
        o += ['## یادداشت‌های روز Claude (خط اول هر روز)', ''] + ['- %s: %s' % (jd(n.get('day')), (n.get('text') or '').split('\n')[0][:200]) for n in notes] + ['']
    o += ['---', 'این گزارش خودکار از برد ساخته شده (tools/report.py). مبلغ و قرارداد در آن نمی‌آید.']
    return '\n'.join(o) + '\n'

def digest():
    D = load_all(); nm, done, closed, stn, svn = helpers(D); T = D['T']; today = B.today_j()
    open_ = sorted([t for t in T.values() if t.get('status') not in closed and t.get('type') != 'gate'], key=lambda t: (t.get('due') is None, t.get('due') or 0))
    o = ['# وضعیت زندهٔ پروژهٔ سوسیسا (برای دستیار پروژه)', '',
         '> خودکار از برد (شاخهٔ board-data) ساخته شده: %s. برای دادهٔ لحظه‌ای‌تر: مخزن عمومی theglitchlabstudio-source/Susisa-projectboard، شاخهٔ board-data، پوشهٔ data/. شناسهٔ تسک داخل [] فقط برای ابزار و بلوک تحویل است؛ با تیم با عنوان حرف بزن.' % time.strftime('%Y-%m-%d %H:%M'), '',
         '- امروز: %s · تا افتتاحیهٔ ۱ آبان: %s روز' % (jd(today), fa(max(0, B.j2d(1405, 8, 1) - today))), '']
    cl = sorted([n for n in D['N'].values() if n.get('by') == 'CL'], key=lambda n: n.get('at', 0))
    if cl: o += ['## آخرین یادداشت روز Claude', '', cl[-1].get('text', ''), '']
    o += ['## گیت‌ها', '']
    for g in sorted([t for t in T.values() if t.get('type') == 'gate'], key=lambda g: g.get('due') or 0):
        ds = [T[i] for i in (g.get('deps') or []) if i in T]
        o.append('- %s · %s · %s/%s' % (g.get('t'), jd(g.get('due')), fa(len([x for x in ds if x.get('status') in done])), fa(len(ds))))
    o += ['', '## کارهای باز (به ترتیب موعد)', '']
    for t in open_:
        flag = ' ⚠️ عقب' if t.get('due') is not None and t['due'] < today else ''
        o.append('### %s [%s]%s' % (t.get('t'), t['id'], flag))
        o.append('- %s · %s · مسئول: %s%s · موعد: %s' % (svn(t.get('svc')), stn(t.get('status')), nm(t.get('owner')), (' · همکار: ' + '، '.join(nm(x) for x in t['with'])) if t.get('with') else '', jd(t.get('due'))))
        if t.get('briefNote'): o.append('- یادداشت مدیر: ' + t['briefNote'].replace('\n', ' ')[:600])
        if t.get('promptNote'): o.append('- پرامپت پیشنهادی: ' + t['promptNote'].replace('\n', ' ')[:600])
        ck = [c for c in (t.get('check') or []) if isinstance(c, dict)]
        if ck: o.append('- چک‌لیست: ' + '، '.join(('✓ ' if c.get('done') else '◻ ') + c.get('x', '') for c in ck))
        o.append('')
    since = time.time() * 1000 - 3 * 86400000
    ev = sorted([e for e in D['L'].values() if e.get('at', 0) >= since], key=lambda e: e['at'])[-60:]
    cm = sorted([c for c in D['C'].values() if c.get('at', 0) >= since], key=lambda c: c['at'])[-40:]
    o += ['## سه روز اخیر: تغییرها', ''] + ['- %s · %s: %s' % (jd(ms_day(e['at'])), nm(e.get('by')), e.get('text', '')) for e in ev] + ['']
    o += ['## سه روز اخیر: پیام‌ها', ''] + ['- %s · %s%s: %s' % (jd(ms_day(c['at'])), nm(c.get('by')), (' روی «%s»' % T[c['task']]['t']) if c.get('task') in T else '', (c.get('text') or '').replace('\n', ' ')[:400]) for c in cm] + ['']
    return '\n'.join(o) + '\n'

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sp = p.add_subparsers(dest='cmd', required=True)
    s = sp.add_parser('weekly'); s.add_argument('--days', type=int, default=7); s.add_argument('--analysis'); s.add_argument('-o'); s.add_argument('--save', action='store_true')
    s = sp.add_parser('digest'); s.add_argument('-o')
    a = p.parse_args()
    if a.cmd == 'weekly':
        md = weekly(a.days, open(a.analysis, encoding='utf8').read() if a.analysis else None)
        out = a.o or '/tmp/weekly-%s.md' % time.strftime('%Y%m%d')
        open(out, 'w', encoding='utf8').write(md); print(out)
        if a.save: B.cmd_report(argparse.Namespace(op='add', path=out, title='گزارش کار هفتگی · ' + jd(B.today_j()), kind='weekly'))
    else:
        md = digest()
        if a.o:
            os.makedirs(os.path.dirname(os.path.abspath(a.o)), exist_ok=True); open(a.o, 'w', encoding='utf8').write(md); print(a.o)
        else: sys.stdout.write(md)

if __name__ == '__main__':
    main()
