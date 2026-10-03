#!/usr/bin/env python3
"""بستهٔ تسک (brief) برای «دستیار تسک» در Claude: یک فایل کوتاه و کامل برای شروع کار روی یک تسک.
می‌سازد از: برد (تسک، وابستگی‌ها، کامنت‌ها)، فهرست ولت (اسناد مرتبط) و قالب ثابت.
خروجی پیش‌فرض: مجموعهٔ `briefs` در board-data (data/briefs.json، برد زیر هر تسک «بریف دستیار تسک» + دکمهٔ کپی نشان می‌دهد
و دستیار از آدرس raw همان فایل می‌خواند). فقط وقتی متن عوض شده باشد نوشته می‌شود (هش، بدون تاریخ). چون برد عمومی است،
اسناد sens=private/secret/skip در بستهٔ برد نمی‌آیند (فقط تعدادشان). --vault: نسخهٔ کامل (با لینک اسناد حساس) هم در ولت خصوصی.
«یادداشت مدیر پروژه» از فیلد briefNote تسک می‌آید (ایجنت: board.py set <id> briefNote="…").
--stdout فقط چاپ؛ --open تسک‌های باز را می‌سازد و بستهٔ تسک‌های تمام‌شده/حذف‌شده را پاک می‌کند.

  brief.py <id> [<id>…]          ساخت/به‌روز بستهٔ این تسک‌ها (در برد: مجموعهٔ briefs؛ هر تسک یک سند)
  brief.py --open [--owner M]    همهٔ تسک‌های باز (todo/doing/review/replan/budget) با آن مالک (پیش‌فرض همه)
  brief.py --critical            فقط تسک‌های urgent/early و باز تا ۱۰ روز آینده
محتوای حساس ولت (sens=secret|skip) هرگز در بسته نمی‌آید؛ sens=private فقط مسیر و لینک.
"""
import json, os, sys, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board as B
import vault as V

OPEN = ('todo', 'doing', 'review', 'replan', 'budget')

def build(tid, T, C, svc, prof, ix, full=False):
    t = T[tid]; st = {s['id']: s['n'] for s in B.load('cfg').get('main', {}).get('statuses', [])}
    nm = lambda i: prof.get(i, {}).get('name', i or '—')
    def line(i):
        x = T.get(i)
        return '- `%s` %s — %s، مالک %s، موعد %s' % (i, x.get('t'), st.get(x.get('status'), x.get('status')), nm(x.get('owner')), B.fmt_j(x.get('due'))) if x else '- `%s` (پیدا نشد)' % i
    deps = t.get('deps') or []
    after = sorted(k for k, x in T.items() if tid in (x.get('deps') or []))
    allowed = ('secret', 'skip') if full else ('secret', 'skip', 'private')
    docs = [(p, e) for p, e in ix['files'].items() if tid in (e.get('tasks') or []) and e.get('sens') not in ('secret', 'skip') and not e.get('gone') and (full or e.get('sens') != 'private')]
    hidden = len([1 for p, e in ix['files'].items() if tid in (e.get('tasks') or []) and e.get('sens') == 'private' and not e.get('gone')]) if not full else 0
    com = sorted([c for c in C.values() if c.get('task') == tid], key=lambda c: c.get('at', 0))[-10:]
    o = ['# بستهٔ تسک `%s` — %s' % (tid, t.get('t')), '',
         '> ساخته‌شده خودکار از برد در %s (امروز همین تاریخ است). دستیار تسک: اول این را کامل بخوان، بعد طبق دستورالعمل پروژه عمل کن. مبلغ ننویس.' % B.fmt_j(B.today_j()), '',
         '## خلاصه',
         '- خدمت: %s' % svc.get(t.get('svc'), t.get('svc')),
         '- مرحله: %s · نوع: %s' % (t.get('stage') or '—', t.get('kind') or '—'),
         '- وضعیت: %s · اولویت: %s%s' % (st.get(t.get('status'), t.get('status')), t.get('prio'), ' · فوری' if t.get('urgent') else ''),
         '- **مالک (فقط او روی این تسک کار می‌کند):** %s' % nm(t.get('owner')),
         '- شروع: %s · موعد: %s' % (B.fmt_j(t.get('start')), B.fmt_j(t.get('due'))), '',
         '## یادداشت مدیر پروژه (ایجنت)', (t.get('briefNote') or '(هنوز ندارد؛ تعریف «تمام‌شده» و هشدارها را دستیار در بریف پیشنهاد دهد)'), '',
         '## شرح و مراحل (از برد)', (t.get('notes') or '(ندارد)'), '']
    if t.get('check'): o += ['## چک‌لیست'] + ['- [%s] %s' % ('x' if (c.get('done') if isinstance(c, dict) else False) else ' ', c.get('t') if isinstance(c, dict) else c) for c in t['check']] + ['']
    o += ['## پیش‌نیازها (باید تمام باشند)'] + ([line(i) for i in deps] or ['- ندارد']) + ['', '## بعد از این تسک (منتظرش هستند)'] + ([line(i) for i in after] or ['- ندارد']) + ['']
    o += ['## اسناد مرتبط در ولت']
    if docs:
        for p, e in sorted(docs):
            tag = ' 🔒حساس: فقط لینک' if e.get('sens') == 'private' else ''
            o.append('- `%s`%s — %s%s' % (p, tag, '' if e.get('sens') == 'private' else (e.get('sum') or '(بدون خلاصه)'), ' · لینک: ' + V.url(p) if e.get('sens') == 'private' else ''))
    else: o.append('- (سند ثبت‌شده‌ای نیست؛ در ولت بگرد یا از ممضی بپرس)')
    if hidden: o.append('- + %s سند حساس در ولت خصوصی (در برد عمومی نمی‌آید؛ از ممضی بخواه)' % hidden)
    fs = [f for f in (t.get('files') or []) if f.get('kind') == 'gh']
    if fs: o += ['', '## ضمیمه‌های روی برد'] + ['- %s (%s)' % (f.get('name'), nm(f.get('by'))) for f in fs]
    if com: o += ['', '## آخرین کامنت‌ها'] + ['- %s: %s' % (nm(c.get('by')), (c.get('text') or '').replace('\n', ' ')[:300]) for c in com]
    o += ['', '## تعریف «تمام‌شده» و خروجی',
          '- (ایجنت مدیر پروژه یا ممضی پر کند؛ اگر خالی است دستیار در بریف پیشنهاد می‌دهد و ممضی تأیید می‌کند)', '',
          '## فرمت تحویل', 'در پایان کار «بلوک تحویل» طبق `agent/copilot/HANDOFF.md` بنویس؛ فایل‌ها فقط با تأیید ممضی ذخیره و به برد/ولت می‌روند.']
    return '\n'.join(o) + '\n'

import hashlib
def body_hash(txt): return hashlib.sha1('\n'.join(l for l in txt.split('\n') if not l.startswith('> ساخته‌شده')).encode()).hexdigest()[:12]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('ids', nargs='*'); ap.add_argument('--open', action='store_true'); ap.add_argument('--owner')
    ap.add_argument('--critical', action='store_true'); ap.add_argument('--stdout', action='store_true'); ap.add_argument('--vault', action='store_true'); a = ap.parse_args()
    B.ensure(); T = B.load('tasks'); C = B.load('comments'); ix = V.load()
    svc = {s['id']: s['n'] for s in B.load('cfg').get('main', {}).get('services', [])}; prof = B.load('profiles')
    ids = [B.find(T, i) for i in a.ids]
    if a.open or a.critical:
        td = B.today_j()
        for k, t in sorted(T.items()):
            if t.get('status') not in OPEN or t.get('type') not in (None, 'task'): continue
            if a.owner and t.get('owner') != a.owner: continue
            if a.critical and not ((t.get('urgent') or t.get('early')) and (t.get('due') or 9e9) <= td + 10): continue
            ids.append(k)
    if not ids: sys.exit('تسکی انتخاب نشد')
    ids = list(dict.fromkeys(ids)); texts = {i: build(i, T, C, svc, prof, ix) for i in ids}
    if a.stdout:
        for i in ids: print(texts[i]); 
        return
    if a.vault:
        out = os.path.join(V.VD, '_agent', 'briefs'); os.makedirs(out, exist_ok=True)
        for i in ids: open(os.path.join(out, i + '.md'), 'w', encoding='utf8').write(build(i, T, C, svc, prof, ix, full=True))
    stat = {'new': [], 'changed': [], 'same': 0, 'pruned': []}
    def mut():
        T2 = B.load('tasks'); Bd = B.load('briefs'); now = int(time.time() * 1000)
        for i in ids:
            h = body_hash(texts[i]); cur = Bd.get(i)
            if cur and cur.get('hash') == h: stat['same'] += 1; continue
            (stat['changed'] if cur else stat['new']).append(i)
            Bd[i] = {'id': i, 'text': texts[i], 'hash': h, 'at': now, 'by': B.AS}
        if a.open:
            for k in list(Bd):
                if T2.get(k, {}).get('status') not in OPEN: stat['pruned'].append(k); del Bd[k]
        if stat['new'] or stat['changed'] or stat['pruned']: B.dump('briefs', Bd)
    B.commit_push('briefs (%d)' % len(ids), mut)
    print(json.dumps(stat, ensure_ascii=False))

if __name__ == '__main__': main()
