#!/usr/bin/env python3
"""ابزار خط فرمان Claude برای ویرایش مستقیم دادهٔ زندهٔ برد (شاخهٔ board-data).
هر تغییر = یک commit روی board-data؛ برد روی همهٔ دستگاه‌ها تا ~۱۵ ثانیه بعد آن را نشان می‌دهد.
نمونه:
  board.py list --status doing        board.py show s1k
  board.py status s1k done            board.py set s1k due=1405/07/20 prio=p1 notes="متن"
  board.py add "عنوان تسک" --svc sv2 --due 1405/07/25 --owner M
  board.py comment s1k "متن پیام"      board.py note "یادداشت امروز" [--day 1405/07/12]
  board.py rm n123abc                 board.py assign s1k CL
محیط: BOARD_DIR (پوشهٔ checkout، پیش‌فرض ~/.cache/susisa-board-data)، BOARD_REMOTE (آدرس مخزن)، BOARD_BRANCH (board-data)، BOARD_AS (شناسهٔ پروفایل، پیش‌فرض CL).
"""
import json, os, subprocess, sys, time, random, argparse

BRANCH = os.environ.get('BOARD_BRANCH', 'board-data')
AS = os.environ.get('BOARD_AS', 'CL')
DIR = os.path.expanduser(os.environ.get('BOARD_DIR', '~/.cache/susisa-board-data'))

def sh(*a, check=True, cwd=None):
    r = subprocess.run(a, cwd=cwd or DIR, capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError(' '.join(a) + '\n' + r.stderr.strip())
    return r.stdout.strip()

def remote_url():
    if os.environ.get('BOARD_REMOTE'): return os.environ['BOARD_REMOTE']
    here = os.path.dirname(os.path.abspath(__file__))
    r = subprocess.run(['git', 'remote', 'get-url', 'origin'], cwd=here, capture_output=True, text=True)
    if r.returncode == 0: return r.stdout.strip()
    sys.exit('BOARD_REMOTE را تنظیم کنید')

def ensure():
    if not os.path.isdir(os.path.join(DIR, '.git')):
        os.makedirs(os.path.dirname(DIR), exist_ok=True)
        subprocess.run(['git', 'clone', '--quiet', '--branch', BRANCH, '--single-branch', remote_url(), DIR], check=True)
        sh('git', 'config', 'user.name', 'Claude'); sh('git', 'config', 'user.email', 'noreply@anthropic.com')
    pull()

def pull():
    sh('git', 'fetch', '--quiet', 'origin', BRANCH)
    sh('git', 'reset', '--quiet', '--hard', 'origin/' + BRANCH)

def load(col):
    p = os.path.join(DIR, 'data', col + '.json')
    if not os.path.exists(p): return {}
    return json.load(open(p, encoding='utf8')).get('docs', {})

def dump(col, docs):
    ids = sorted(docs)
    body = '{"v":1,"docs":{' + ('\n' if ids else '') + ',\n'.join(json.dumps(i, ensure_ascii=False) + ':' + json.dumps(docs[i], ensure_ascii=False, separators=(',', ':')) for i in ids) + ('\n' if ids else '') + '}}\n'
    os.makedirs(os.path.join(DIR, 'data'), exist_ok=True)
    open(os.path.join(DIR, 'data', col + '.json'), 'w', encoding='utf8').write(body)

def commit_push(msg, mutate):
    """mutate() روی آخرین نسخهٔ سرور اعمال می‌شود؛ اگر push رد شد دوباره از نو."""
    for attempt in range(6):
        ensure() if attempt == 0 else pull()
        res = mutate()
        pth = ['data'] + (['files'] if os.path.isdir(os.path.join(DIR, 'files')) else [])
        sh('git', 'add', '-A', *pth)
        if not sh('git', 'status', '--porcelain', *pth):
            print('بدون تغییر'); return res
        sh('git', 'commit', '--quiet', '-m', 'board: ' + msg + ' (by Claude)')
        r = subprocess.run(['git', 'push', '--quiet', 'origin', 'HEAD:' + BRANCH], cwd=DIR, capture_output=True, text=True)
        if r.returncode == 0: return res
        time.sleep(0.5 + random.random())
    sys.exit('push ناموفق بود: ' + r.stderr.strip())

# ---- تقویم جلالی (همان الگوریتم برد) ----
def _div(a, b): return int(a / b)
BR = [-61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210, 1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178]
def jal_cal(jy):
    bl = len(BR); gy = jy + 621; leapJ = -14; jp = BR[0]; jump = 0
    for i in range(1, bl):
        jm = BR[i]; jump = jm - jp
        if jy < jm: break
        leapJ += _div(jump, 33) * 8 + _div(jump % 33, 4); jp = jm
    n = jy - jp
    leapJ += _div(n, 33) * 8 + _div(n % 33 + 3, 4)
    if jump % 33 == 4 and jump - n == 4: leapJ += 1
    leapG = _div(gy, 4) - _div((_div(gy, 100) + 1) * 3, 4) - 150
    march = 20 + leapJ - leapG
    if jump - n < 6: n = n - jump + _div(jump + 4, 33) * 33
    leap = ((n + 1) % 33 - 1) % 4
    if leap == -1: leap = 4
    return gy, march
def g2d(gy, gm, gd):
    d = _div((gy + _div(gm - 8, 6) + 100100) * 1461, 4) + _div(153 * ((gm + 9) % 12) + 2, 5) + gd - 34840408
    return d - _div(_div(gy + 100100 + _div(gm - 8, 6), 100) * 3, 4) + 752
def j2d(jy, jm, jd):
    gy, march = jal_cal(jy)
    return g2d(gy, 3, march) + (jm - 1) * 31 - _div(jm, 7) * (jm - 7) + jd - 1
def d2g(jdn):
    j = 4 * jdn + 139361631; j += _div(_div(4 * jdn + 183187720, 146097) * 3, 4) * 4 - 3908
    i = _div(j % 1461, 4) * 5 + 308; gd = _div(i % 153, 5) + 1; gm = _div(i, 153) % 12 + 1
    return _div(j, 1461) - 100100 + _div(8 - gm, 6), gm, gd
def d2j(jdn):
    gy, gm, gd = d2g(jdn); jy = gy - 621; g1, mar = jal_cal(jy); k = jdn - g2d(gy, 3, mar)
    if k >= 0:
        if k <= 185: return jy, 1 + _div(k, 31), k % 31 + 1
        k -= 186
    else:
        jy -= 1; k += 179
        g1, mar2 = jal_cal(jy)
    return jy, 7 + _div(k, 30), k % 30 + 1
def parse_j(s):
    if s in (None, '', 'none', 'null'): return None
    p = [int(x) for x in s.replace('-', '/').split('/')]
    if len(p) == 2: p = [1405] + p
    return j2d(*p)
def fmt_j(d):
    if d is None: return '—'
    y, m, dd = d2j(d); return '%04d/%02d/%02d' % (y, m, dd)
def today_j():
    t = time.localtime(); return g2d(t.tm_year, t.tm_mon, t.tm_mday)

INT_F = {'start': parse_j, 'due': parse_j}
BOOL_F = {'urgent'}
def conv(k, v):
    if k in INT_F: return INT_F[k](v)
    if k in BOOL_F: return v.lower() in ('1', 'true', 'yes', 'y')
    if v in ('null', 'none'): return None
    return v

def stamp(t): t['upd'] = int(time.time() * 1000); t['by'] = AS

def find(tasks, i):
    if i in tasks: return i
    m = [k for k in tasks if k.startswith(i)]
    if len(m) == 1: return m[0]
    sys.exit('تسک پیدا نشد یا مبهم است: ' + i)

def cmd_list(a):
    ensure(); T = load('tasks'); st = {s['id']: s['n'] for s in load('cfg').get('main', {}).get('statuses', [])}
    for t in sorted(T.values(), key=lambda t: (t.get('due') is None, t.get('due') or 0, t['id'])):
        if a.status and t.get('status') != a.status: continue
        if a.svc and t.get('svc') != a.svc: continue
        if a.owner and t.get('owner') != a.owner: continue
        if a.q and a.q not in t.get('t', '') + t.get('notes', ''): continue
        print('%-8s %-7s %s  %-4s %s  %s' % (t['id'], t.get('status'), fmt_j(t.get('due')), t.get('owner'), t.get('prio'), t.get('t')))

def cmd_show(a):
    ensure(); T = load('tasks'); i = find(T, a.id); t = T[i]
    print(json.dumps(t, ensure_ascii=False, indent=2))
    for c in sorted(load('comments').values(), key=lambda c: c.get('at', 0)):
        if c.get('task') == i: print('💬', c.get('by'), c.get('text'))

def cmd_set(a):
    def mut():
        T = load('tasks'); i = find(T, a.id); t = T[i]
        for kv in a.kv:
            k, _, v = kv.partition('=')
            if k in ('id',): sys.exit('id قابل تغییر نیست')
            t[k] = conv(k, v)
        if t.get('status') == 'done' and not t.get('doneAt'): t['doneAt'] = today_j()
        if t.get('status') != 'done': t['doneAt'] = None
        stamp(t); dump('tasks', T); return i
    i = commit_push('tasks %s' % a.id, mut); print('ok', i)

def cmd_status(a):
    cmd_set(argparse.Namespace(id=a.id, kv=['status=' + a.status]))

def cmd_assign(a):
    cmd_set(argparse.Namespace(id=a.id, kv=['owner=' + a.owner]))

def cmd_add(a):
    nid = 'n' + format(int(time.time() * 1000), 'x')[-8:] + format(random.randrange(46656), 'x')
    def mut():
        T = load('tasks')
        t = {'id': nid, 't': a.title, 'svc': a.svc, 'phase': None, 'bb': None, 'owner': a.owner, 'prio': a.prio, 'status': 'todo', 'start': parse_j(a.start), 'due': parse_j(a.due), 'deps': [], 'notes': a.notes or '', 'check': [], 'type': 'task', 'early': False, 'doneAt': None, 'budget': None, 'urgent': False, 'files': [], 'lane': 'main'}
        stamp(t); T[nid] = t; dump('tasks', T)
    commit_push('tasks %s add' % nid, mut); print('ok', nid)

def cmd_rm(a):
    def mut():
        T = load('tasks'); i = find(T, a.id); del T[i]; dump('tasks', T)
    commit_push('tasks %s rm' % a.id, mut); print('ok')

def cmd_comment(a):
    cid = 'c' + format(int(time.time() * 1000), 'x')[-8:] + format(random.randrange(46656), 'x')
    def mut():
        T = load('tasks'); i = find(T, a.id); C = load('comments')
        C[cid] = {'id': cid, 'task': i, 'text': a.text, 'by': AS, 'at': int(time.time() * 1000)}; dump('comments', C)
    commit_push('comment %s' % a.id, mut); print('ok', cid)

def cmd_note(a):
    nid = 'n' + format(int(time.time() * 1000), 'x')[-8:] + format(random.randrange(46656), 'x')
    day = parse_j(a.day) if a.day else today_j()
    def mut():
        N = load('notes'); N[nid] = {'id': nid, 'day': day, 'text': a.text, 'by': AS, 'at': int(time.time() * 1000), 'kind': 'note'}; dump('notes', N)
    commit_push('note %s' % fmt_j(day), mut); print('ok', nid)

def cmd_svc(a):
    """مدیریت دستهٔ خدمات: list | add | edit | rm"""
    if a.op == 'list':
        ensure(); [print(x['id'], x['n'], '[جانبی]' if x.get('side') else '') for x in load('cfg').get('main', {}).get('services', [])]; return
    def mut():
        C = load('cfg'); m = C['main']; S = m['services']
        cur = next((x for x in S if x['id'] == a.id), None)
        if a.op == 'rm':
            if not cur: sys.exit('دسته پیدا نشد: ' + a.id)
            if any(t.get('svc') == a.id for t in load('tasks').values()): sys.exit('این دسته هنوز تسک دارد؛ اول جابه‌جایشان کن')
            S.remove(cur); m['v'] = m.get('v', 1) + 1; dump('cfg', C); return
        if a.op == 'add':
            if cur: sys.exit('این شناسه وجود دارد: ' + a.id)
            cur = {'id': a.id, 'n': a.name, 's': a.short or a.name, 'c': a.color or '#7A7068'}
            idx = next((i + 1 for i, x in enumerate(S) if x['id'] == a.after), len(S))
            S.insert(idx, cur)
        else:
            if not cur: sys.exit('دسته پیدا نشد: ' + a.id)
            if a.name: cur['n'] = a.name
            if a.short: cur['s'] = a.short
            if a.color: cur['c'] = a.color
            if a.after:
                S.remove(cur); S.insert(next((i + 1 for i, x in enumerate(S) if x['id'] == a.after), len(S)), cur)
        if a.side is not None:
            if a.side: cur['side'] = True
            else: cur.pop('side', None)
        m['v'] = m.get('v', 1) + 1; dump('cfg', C)
    commit_push('svc %s %s' % (a.op, a.id), mut); print('ok', a.id)

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sp = p.add_subparsers(dest='cmd', required=True)
    s = sp.add_parser('list'); s.add_argument('--status'); s.add_argument('--svc'); s.add_argument('--owner'); s.add_argument('--q'); s.set_defaults(f=cmd_list)
    s = sp.add_parser('show'); s.add_argument('id'); s.set_defaults(f=cmd_show)
    s = sp.add_parser('set'); s.add_argument('id'); s.add_argument('kv', nargs='+'); s.set_defaults(f=cmd_set)
    s = sp.add_parser('status'); s.add_argument('id'); s.add_argument('status'); s.set_defaults(f=cmd_status)
    s = sp.add_parser('assign'); s.add_argument('id'); s.add_argument('owner'); s.set_defaults(f=cmd_assign)
    s = sp.add_parser('svc'); s.add_argument('op', choices=['list', 'add', 'edit', 'rm']); s.add_argument('id', nargs='?'); s.add_argument('--name'); s.add_argument('--short'); s.add_argument('--color'); s.add_argument('--after'); s.add_argument('--side', type=lambda v: v.lower() in ('1', 'true', 'yes'), default=None); s.set_defaults(f=cmd_svc)
    s = sp.add_parser('add'); s.add_argument('title'); s.add_argument('--svc', default='sv2'); s.add_argument('--owner', default=AS); s.add_argument('--prio', default='p2'); s.add_argument('--start'); s.add_argument('--due'); s.add_argument('--notes'); s.set_defaults(f=cmd_add)
    s = sp.add_parser('rm'); s.add_argument('id'); s.set_defaults(f=cmd_rm)
    s = sp.add_parser('comment'); s.add_argument('id'); s.add_argument('text'); s.set_defaults(f=cmd_comment)
    s = sp.add_parser('note'); s.add_argument('text'); s.add_argument('--day'); s.set_defaults(f=cmd_note)
    a = p.parse_args(); a.f(a)

if __name__ == '__main__':
    main()
