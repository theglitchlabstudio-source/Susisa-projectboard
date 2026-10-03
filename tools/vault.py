#!/usr/bin/env python3
"""ابزار کتابدار: اتصال ولت خصوصی Obsidian (مخزن susisa-vault) به ایجنت و برد.
محتوای ولت هرگز در این مخزن عمومی یا شاخهٔ board-data کپی نمی‌شود؛ در برد فقط «لینک» به فایل در مخزن خصوصی ثبت می‌شود.
فهرست و حافظهٔ کتابدار داخل خود ولت است: _agent/index.json و _agent/INDEX.md

  vault.py scan                      فایل‌های تازه/تغییرکرده/حذف‌شده نسبت به فهرست (JSON)
  vault.py set <path> key=value ...  ثبت در فهرست: sum="خلاصه" tasks=s0l,e01 svc=sv2 type=سند sens=normal|private|secret|skip dup=<path>
                                     private = محتوا حساس، فقط لینک در برد · secret = هرگز در برد (مثل مالی) · skip = نادیده
  vault.py link <task> <path> [نام]  لینک فایل ولت روی تسک برد (اگر فایل عوض شده باشد، لینک به‌روز و کامنت ثبت می‌شود)
  vault.py render                    ساخت _agent/INDEX.md از فهرست
  vault.py save "پیام"               commit و push فهرست در مخزن ولت
محیط: VAULT_DIR (پیش‌فرض ~/susisa-vault یا /home/claude/susisa-vault)، VAULT_REPO (owner/repo)
"""
import json, os, sys, subprocess, hashlib, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board as B

REPO = os.environ.get('VAULT_REPO', 'theglitchlabstudio-source/susisa-vault')
CANDS = [os.environ.get('VAULT_DIR', ''), '/home/claude/susisa-vault', os.path.expanduser('~/susisa-vault')]
VD = next((c for c in CANDS if c and os.path.isdir(os.path.join(c, '.git'))), None)
if not VD: sys.exit('ولت پیدا نشد: VAULT_DIR را تنظیم کنید یا مخزن %s را clone کنید' % REPO)
IDX = os.path.join(VD, '_agent', 'index.json')
SKIP_PREFIX = ('_agent/', '.obsidian/')

def git(*a): return subprocess.run(('git', '-C', VD) + a, capture_output=True, text=True, check=True).stdout
def files():
    out = {}
    for line in git('ls-files', '-s', '-z').split('\0'):
        if not line.strip(): continue
        meta, path = line.split('\t', 1); sha = meta.split()[1]
        if path.startswith(SKIP_PREFIX) or path in ('.gitignore',): continue
        out[path] = sha
    return out
def load():
    try: return json.load(open(IDX, encoding='utf8'))
    except FileNotFoundError: return {'v': 1, 'files': {}}
def save_idx(ix):
    os.makedirs(os.path.dirname(IDX), exist_ok=True)
    json.dump(ix, open(IDX, 'w', encoding='utf8'), ensure_ascii=False, indent=1, sort_keys=True)
def url(path): return 'https://github.com/%s/blob/main/%s' % (REPO, '/'.join(__import__('urllib.parse').parse.quote(p) for p in path.split('/')))

def cmd_scan():
    ix = load(); cur = files(); known = ix['files']
    new = [p for p in cur if p not in known]
    changed = [p for p in cur if p in known and known[p].get('sha') != cur[p]]
    gone = [p for p in known if p not in cur and not known[p].get('gone')]
    print(json.dumps({'vault': VD, 'head': git('rev-parse', '--short', 'HEAD').strip(), 'new': new, 'changed': changed, 'removed': gone,
                      'total': len(cur), 'indexed': len(known)}, ensure_ascii=False, indent=1))

def cmd_set(path, kv):
    ix = load(); cur = files()
    if path not in cur and path not in ix['files']: sys.exit('فایل در ولت نیست: ' + path)
    e = ix['files'].setdefault(path, {})
    for x in kv:
        k, _, v = x.partition('=')
        e[k] = [s for s in v.split(',') if s] if k == 'tasks' else v
    if path in cur: e['sha'] = cur[path]; e.pop('gone', None)
    else: e['gone'] = True
    e['seen'] = B.fmt_j(B.today_j()); save_idx(ix); print('ok', path)

def cmd_link(tid, path, name=None):
    cur = files()
    if path not in cur: sys.exit('فایل در ولت نیست: ' + path)
    ix = load(); ent = ix['files'].get(path, {})
    if ent.get('sens') in ('secret', 'skip'): sys.exit('این فایل محرمانه/نادیده است و روی برد لینک نمی‌شود: ' + path)
    lid = 'v' + hashlib.sha1(path.encode()).hexdigest()[:10]
    nm = name or os.path.basename(path)
    def mut():
        T = B.load('tasks'); i = B.find(T, tid); t = T[i]; fs = t.get('files') or []
        ex = next((f for f in fs if f.get('id') == lid), None); note = None
        if ex:
            if ex.get('sha') == cur[path] and ex.get('name') == nm: return 'same'
            if ex.get('sha') != cur[path]: note = 'سند ولت به‌روز شد: «%s»' % nm
            ex.update({'name': nm, 'url': url(path), 'sha': cur[path], 'at': int(time.time() * 1000), 'by': B.AS})
        else:
            fs.append({'id': lid, 'kind': 'link', 'name': nm, 'url': url(path), 'vault': path, 'sha': cur[path], 'at': int(time.time() * 1000), 'by': B.AS})
        t['files'] = fs; B.stamp(t); B.dump('tasks', T)
        if note:
            C = B.load('comments'); cid = 'c' + hashlib.sha1((lid + cur[path]).encode()).hexdigest()[:10]
            C[cid] = {'id': cid, 'task': i, 'text': note, 'by': B.AS, 'at': int(time.time() * 1000)}; B.dump('comments', C)
        return 'ok'
    r = B.commit_push('tasks %s vault-link' % tid, mut)
    e = ix['files'].setdefault(path, {}); tl = e.setdefault('tasks', [])
    if tid not in tl: tl.append(tid)
    e['sha'] = cur[path]; save_idx(ix); print(r or 'ok', tid, path)

def cmd_render():
    ix = load(); F = ix['files']
    rows = sorted(F.items(), key=lambda kv: kv[0])
    out = ['# فهرست اسناد ولت سوسیسا (کتابدار Claude)', '',
           '> این فایل خودکار ساخته می‌شود؛ دستی ویرایش نکنید. خلاصه‌ها و ارتباط هر سند با تسک‌های برد. 🔒حساس = در برد فقط لینک (به همین مخزن خصوصی) · ⛔محرمانه = هرگز در برد · نادیده = بایگانی یا تکراری.', '',
           'به‌روزرسانی: ' + B.fmt_j(B.today_j()) + ' · ' + str(len([1 for p, e in rows if not e.get('gone')])) + ' سند', '']
    folder = None
    for p, e in rows:
        if e.get('gone'): continue
        d = os.path.dirname(p) or '(ریشه)'
        if d != folder: out += ['', '## ' + d, '']; folder = d
        tag = {'private': ' 🔒حساس (فقط لینک)', 'secret': ' ⛔محرمانه', 'skip': ' ·نادیده'}.get(e.get('sens'), '')
        dup = (' · تکراری از `%s`' % e['dup']) if e.get('dup') else ''
        tk = (' · تسک‌ها: ' + '، '.join(e.get('tasks', []))) if e.get('tasks') else ''
        out.append('- **%s**%s — %s%s%s' % (os.path.basename(p), tag, e.get('sum', '(بدون خلاصه)'), dup, tk))
    open(os.path.join(VD, '_agent', 'INDEX.md'), 'w', encoding='utf8').write('\n'.join(out) + '\n'); print('ok INDEX.md')

def cmd_save(msg):
    git('add', '_agent')
    if not git('status', '--porcelain', '_agent').strip(): print('بدون تغییر'); return
    git('commit', '-q', '-m', 'agent: ' + msg)
    for _ in range(4):
        r = subprocess.run(['git', '-C', VD, 'push', '-q', 'origin', 'HEAD:main'], capture_output=True, text=True)
        if r.returncode == 0: print('ok pushed'); return
        subprocess.run(['git', '-C', VD, 'pull', '-q', '--rebase', 'origin', 'main'], capture_output=True, text=True)
    sys.exit('push ناموفق: ' + r.stderr.strip())

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit()
    c = a[0]
    if c == 'scan': cmd_scan()
    elif c == 'set': cmd_set(a[1], a[2:])
    elif c == 'link': cmd_link(a[1], a[2], a[3] if len(a) > 3 else None)
    elif c == 'render': cmd_render()
    elif c == 'save': cmd_save(a[1] if len(a) > 1 else 'index')
    else: print(__doc__)
