#!/usr/bin/env python3
"""ابزار ایجنت برای «برد تولید محتوا» (content.html) و پل دوطرفه با برد اصلی.

داده روی همان شاخهٔ board-data: data/content_items.json، data/content_meta.json (settings، activity)، data/content_ideas.json.
هر دستور نوشتنی = یک commit؛ هر دو برد تا حدود ۲۰ ثانیه بعد تغییر را نشان می‌دهند.

  content.py list [--type reel|post|story] [--stage edit] [--q متن]
  content.py show <id>
  content.py set <id> path=value …        # مسیر نقطه‌ای: date=1405/07/28 caption.text="…" stages.edit.due=1405/08/02
  content.py stage <id> <concept|scenario|storyboard|prep|shoot|edit|color|caption|qc|publish|done>
  content.py approve <id> <concept|scenario|storyboard|caption|qc> <ok|review|fix|draft> ["یادداشت"]
  content.py task <id> "متن" [--owner ممضی] [--due 1405/07/28] [--stage edit]
  content.py comment <id> "پیام"
  content.py ai <id> [--brief "…"] [--prompt "…"] [--ideas "…"]   # پنل «یادداشت Claude» در صفحهٔ محتوا
  content.py add <reel|post|story> "عنوان" [--date 1405/07/28] [--owner ممضی] [--concept "…"] [--board <id تسک برد اصلی>]
  content.py link <id> <id تسک برد اصلی>   # پیوند یک محتوا به تسک برد اصلی
  content.py sync [--dry]                  # همگام‌سازی دوطرفهٔ دو برد (قاعده‌ها پایین)
  content.py check [--md] [--json]          # هشدارهای برد محتوا (مثل ناظر)
  content.py summary                        # خلاصهٔ Markdown برای kb/live.md
  content.py alts <id> [بخش]               # نسخه‌های قبلی متن‌ها (۱ = تازه‌ترین)
  content.py pick <id> <بخش> <n>           # نسخهٔ n رو اصلی کن (متن فعلی می‌ره تو نسخه‌ها)

گزینه‌های کلی (قبل از دستور): --by "نام نویسنده" (پیش‌فرض Claude؛ مثلاً «ادمین پیج» یا «چت Cowork»)، --force (نوشتن روی محتوای hold).
نسخه‌ها: بازنویسی text/tags/prompt بخش‌های concept, scenario, storyboard, shoot, caption, edit, prep متن قبلی رو تو <بخش>.alts نگه می‌داره؛
  آخرین نوشته اصلیه؛ اگه بخش «تأیید شد» بود، برمی‌گرده به «منتظر تأیید» تا آدم یکی رو نهایی کنه.
hold: محتوای متوقف به دستور ممضی؛ set/stage/approve/task/comment/ai/pick بدون --force روش کار نمی‌کنن.

قاعده‌های sync:
  محتوا ← برد اصلی (منبع جزئیات تولید، تاریخ انتشار و مرحله، برد محتواست):
    تسک یک‌به‌یک (boardTask): موعد = تاریخ انتشار؛ وضعیت done وقتی «منتشر شد»، doing وقتی از کانسپت جلوتره؛ چک‌لیست = مرحله‌های تولید.
    تسک تجمیعی (چند محتوا روی یک تسک، مثل پست‌ها یا استوری روزانه): یک خط چک‌لیست برای هر محتوا؛ done وقتی همه منتشر شدن؛ موعد = آخرین تاریخ.
  برد اصلی ← محتوا: اگر مسئول محتوا خالیه، مسئول تسک برد اصلی؛ اگر تاریخ محتوا خالیه و تسک یک‌به‌یک موعد داره، همون موعد.
"""
import hashlib
import argparse, json, os, re, sys, time, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board as B

TYPES = {'reel': 'ریل', 'post': 'پست', 'story': 'استوری'}
FLOW = {'reel': ['concept', 'scenario', 'storyboard', 'prep', 'shoot', 'edit', 'color', 'caption', 'qc', 'publish', 'done'],
        'post': ['concept', 'shoot', 'edit', 'caption', 'qc', 'publish', 'done'],
        'story': ['concept', 'edit', 'qc', 'publish', 'done']}
LBL = {'concept': 'کانسپت', 'scenario': 'سناریو', 'storyboard': 'استوری‌بورد', 'prep': 'هماهنگی', 'shoot': 'ضبط', 'edit': 'تدوین', 'color': 'اصلاح رنگ', 'caption': 'کپشن', 'qc': 'کنترل کیفیت', 'publish': 'آپلود', 'done': 'منتشر شد'}
LBL_OVR = {'post': {'shoot': 'عکاسی یا طراحی', 'edit': 'ادیت و طراحی'}, 'story': {'edit': 'ساخت'}}
APS = ['concept', 'scenario', 'storyboard', 'caption', 'qc']
AP = {'draft': 'پیش‌نویس', 'review': 'منتظر تأیید', 'ok': 'تأیید شد', 'fix': 'نیاز به اصلاح'}
FA = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
MONTHS = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
WDN = ['دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه', 'شنبه', 'یکشنبه']
NAME2ID = {}
CONFLICTS = []
SEV = {3: 'بحرانی', 2: 'مهم', 1: 'جزئی'}
BY = 'Claude'          # نویسندهٔ این اجرا (--by)
FORCE = False          # --force: نوشتن روی محتوای hold
VERS = ('concept', 'scenario', 'storyboard', 'shoot', 'caption', 'edit', 'prep', 'ai')  # ai: فقط برای alts/pick
VKEYS = ('text', 'tags', 'prompt')

def fa(x): return str(x).translate(FA)
def lbl(t, k): return LBL_OVR.get(t, {}).get(k) or LBL.get(k, k)
def today(): return B.fmt_j(B.today_j())
def stamp(): return today() + ' ' + time.strftime('%H:%M')
def jdn(s): return B.parse_j(s) if s else None
def human(s):
    if not s: return 'بی‌تاریخ'
    n = B.parse_j(s); y, m, d = B.d2j(n); return '%s %s %s' % (WDN[datetime.date(*B.d2g(n)).weekday()], fa(d), MONTHS[m - 1])
def norm_date(s):
    s = (s or '').translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')).strip()
    if not s: return ''
    m = re.match(r'^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$', s)
    if not m: sys.exit('تاریخ نامعتبر: ' + s)
    return '%s/%02d/%02d' % (m.group(1), int(m.group(2)), int(m.group(3)))
def flow(it): return FLOW.get(it.get('type'), FLOW['reel'])
def sidx(it):
    f = flow(it); s = it.get('stage') or 'concept'; return f.index(s) if s in f else 0
def ap(it, s): return ((it.get(s) or {}).get('ap') or {}).get('status') or 'draft'
def find(I, i):
    if i in I: return i
    m = [k for k in I if k.startswith(i)]
    if len(m) == 1: return m[0]
    sys.exit('محتوا پیدا نشد یا مبهم است: ' + i)
def deep_merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict): deep_merge(a[k], v)
        else: a[k] = json.loads(json.dumps(v))
    return a
def set_path(o, path, val):
    ks = path.split('.'); c = o
    for k in ks[:-1]:
        if isinstance(c, list): k = int(k)
        if isinstance(c, list):
            while len(c) <= k: c.append({})
            c = c[k]
        else:
            if not isinstance(c.get(k), (dict, list)): c[k] = {}
            c = c[k]
    last = ks[-1]
    if isinstance(c, list): c[int(last)] = val
    else: c[last] = val
def conv_val(path, v):
    k = path.split('.')[-1]
    if k in ('date', 'start', 'due'): return norm_date(v)
    if v in ('true', 'false'): return v == 'true'
    if v == 'null': return None
    if k in ('dur',) and re.match(r'^\d+(\.\d+)?$', v): return float(v)
    return v
def touch(it): it['updatedAt'] = stamp(); it['updatedBy'] = BY
def guard(it):
    if it.get('hold') and not FORCE:
        sys.exit('«%s» به دستور ممضی متوقفه (hold)؛ چیزی روش نوشته نمی‌شه. اگه خود ممضی خواسته، با --force.' % it.get('title'))
def reopen(sec, note):
    if ((sec.get('ap') or {}).get('status')) == 'ok':
        sec['ap'] = {'status': 'review', 'by': BY, 'at': stamp(), 'note': note}
        sec['hist'] = (sec.get('hist') or [])[-19:] + [{'status': 'review', 'by': BY, 'at': stamp(), 'note': note}]
def archive(it, path, new):
    """اگه path متن نسخه‌دار باشه و مقدار قبلی فرق کنه، قبلی رو تو alts نگه دار. خروجی: (نام بخش یا None, آرشیو شد؟)"""
    ks = path.split('.')
    if len(ks) != 2 or ks[0] not in VERS or ks[1] not in VKEYS: return None, False
    sec = it.get(ks[0])
    old = sec.get(ks[1]) if isinstance(sec, dict) else None
    if not old or old == new: return ks[0], False
    al = sec.get('alts') or []
    al.append({'k': ks[1], 'text': old, 'by': sec.get('wby') or it.get('updatedBy') or '?', 'at': sec.get('wat') or ''})
    sec['alts'] = al[-10:]
    return ks[0], True
def logc(M, text):
    a = M.setdefault('activity', {}).get('list') or []
    M['activity'] = {'list': ([{'at': stamp(), 'by': BY, 'text': text}] + a)[:200]}
def names():
    P = B.load('profiles'); return {k: v.get('name', k) for k, v in P.items()}

def commit(msg, fn):
    def mut():
        I = B.load('content_items'); M = B.load('content_meta'); T = B.load('tasks')
        before_T = json.loads(json.dumps(T)); r = fn(I, M, T)
        B.dump('content_items', I); B.dump('content_meta', M)
        if T != before_T: B.dump('tasks', T)
        return r
    return B.commit_push(msg, mut)

# ---------------- commands ----------------
def cmd_list(a):
    B.ensure(); I = B.load('content_items')
    rows = sorted(I.items(), key=lambda kv: (kv[1].get('date') or '9999', kv[1].get('type', '')))
    for k, it in rows:
        if it.get('archived'): continue
        if a.type and it.get('type') != a.type: continue
        if a.stage and (it.get('stage') or 'concept') != a.stage: continue
        if a.q and a.q not in json.dumps(it, ensure_ascii=False): continue
        aps = ' '.join('%s:%s' % (s[:4], ap(it, s)) for s in APS if ap(it, s) != 'draft')
        print('%-14s %-5s %-10s %-11s %-10s %s %s' % (k, it.get('type'), it.get('date') or '—', it.get('stage') or 'concept', it.get('owner') or '—', it.get('title'), ('[' + aps + ']') if aps else ''))

def cmd_show(a):
    B.ensure(); I = B.load('content_items'); print(json.dumps(I[find(I, a.id)], ensure_ascii=False, indent=1))

def cmd_set(a):
    def fn(I, M, T):
        i = find(I, a.id); it = I[i]; guard(it); secs = {}
        for kv in a.kv:
            p, _, v = kv.partition('='); val = conv_val(p, v)
            sn, arch = archive(it, p, val)
            set_path(it, p, val)
            if sn: secs[sn] = secs.get(sn, False) or arch
        for sn, arch in secs.items():
            sec = it[sn]; sec['wby'] = BY; sec['wat'] = stamp()
            if arch: reopen(sec, 'نسخهٔ تازه از %s؛ نسخهٔ قبلی تو «نسخه‌های دیگه»' % BY)
        touch(it); logc(M, '«%s»: ویرایش توسط %s (%s)' % (it.get('title'), BY, '، '.join(x.partition('=')[0] for x in a.kv)))
        return i
    print('ok', commit('content: set %s' % a.id, fn))

def cmd_alts(a):
    B.ensure(); I = B.load('content_items'); it = I[find(I, a.id)]
    secs = [a.sec] if a.sec else [k for k in VERS if isinstance(it.get(k), dict) and it[k].get('alts')]
    if not secs: print('نسخهٔ دیگه‌ای نیست'); return
    for sn in secs:
        sec = it.get(sn) or {}; al = sec.get('alts') or []
        print('== %s · نوشتهٔ فعلی: %s %s · %d نسخهٔ دیگه' % (sn, sec.get('wby') or '?', sec.get('wat') or '', len(al)))
        for n, x in enumerate(reversed(al), 1):
            print('  [%d] %s · %s · %s\n      %s' % (n, x.get('k', 'text'), x.get('by', '?'), x.get('at', ''), (x.get('text') or '').replace('\n', ' ')[:300]))

def cmd_pick(a):
    def fn(I, M, T):
        i = find(I, a.id); it = I[i]; guard(it); sec = it.get(a.sec)
        al = (sec or {}).get('alts') or []
        n = int(a.n)
        if not 1 <= n <= len(al): sys.exit('نسخهٔ %d نیست؛ %d نسخه هست' % (n, len(al)))
        j = len(al) - n; x = al[j]; k = x.get('k', 'text'); old = sec.get(k)
        rest = al[:j] + al[j + 1:]
        if old: rest.append({'k': k, 'text': old, 'by': sec.get('wby') or it.get('updatedBy') or '?', 'at': sec.get('wat') or ''})
        sec[k] = x.get('text', ''); sec['alts'] = rest[-10:]; sec['wby'] = x.get('by', ''); sec['wat'] = x.get('at', '')
        reopen(sec, 'نسخهٔ %s برگشت (انتخاب %s)' % (x.get('by', ''), BY))
        touch(it); logc(M, '«%s»: %s ← نسخهٔ %s' % (it.get('title'), a.sec, x.get('by', ''))); return i
    print('ok', commit('content: pick %s %s' % (a.id, a.sec), fn))

def move_stage(it, key):
    f = flow(it)
    if key not in f: sys.exit('این نوع محتوا مرحلهٔ %s نداره' % key)
    st = it.setdefault('stages', {}); ki = f.index(key)
    for i, k in enumerate(f):
        if i < ki: st.setdefault(k, {})['done'] = True
        elif k in st and st[k].get('done') and ki < sidx(it): st[k]['done'] = False
    it['stage'] = key
    if key == 'done' and not it.get('publishedAt'): it['publishedAt'] = today()

def cmd_stage(a):
    def fn(I, M, T):
        i = find(I, a.id); it = I[i]; guard(it); move_stage(it, a.key); touch(it); logc(M, '«%s» ← %s' % (it.get('title'), lbl(it.get('type'), a.key))); return i
    print('ok', commit('content: stage %s %s' % (a.id, a.key), fn))

def cmd_approve(a):
    if a.sec not in APS or a.st not in AP: sys.exit('بخش یا وضعیت نامعتبر')
    def fn(I, M, T):
        i = find(I, a.id); it = I[i]; guard(it); sec = it.setdefault(a.sec, {})
        apx = sec.get('ap') or {}; apx.update({'status': a.st, 'by': BY, 'at': stamp()})
        if a.note: apx['note'] = a.note
        sec['ap'] = apx; sec['hist'] = (sec.get('hist') or [])[-19:] + [{'status': a.st, 'by': BY, 'at': stamp(), 'note': a.note or ''}]
        touch(it); logc(M, '«%s»: %s ← %s' % (it.get('title'), a.sec, AP[a.st])); return i
    print('ok', commit('content: approve %s %s' % (a.id, a.sec), fn))

def cmd_task(a):
    def fn(I, M, T):
        i = find(I, a.id); it = I[i]; guard(it)
        it.setdefault('tasks', []).append({'text': a.text, 'stage': a.stage or it.get('stage') or '', 'owner': a.owner or '', 'due': norm_date(a.due) if a.due else '', 'done': False, 'by': BY, 'at': stamp()})
        touch(it); logc(M, '«%s»: ریزتسک «%s»' % (it.get('title'), a.text)); return i
    print('ok', commit('content: task %s' % a.id, fn))

def cmd_comment(a):
    def fn(I, M, T):
        i = find(I, a.id); it = I[i]; guard(it); it.setdefault('comments', []).append({'by': BY, 'at': stamp(), 'text': a.text}); touch(it)
        logc(M, '«%s»: پیام تازه از Claude' % it.get('title')); return i
    print('ok', commit('content: comment %s' % a.id, fn))

def cmd_ai(a):
    def fn(I, M, T):
        i = find(I, a.id); it = I[i]; guard(it); x = it.get('ai') or {}
        for k in ('brief', 'prompt', 'ideas'):
            v = getattr(a, k)
            if v is None: continue
            if x.get(k) and x[k] != v:  # متن قبلی پنل «یادداشت Claude» گم نشه
                al = x.get('alts') or []
                al.append({'k': k, 'text': x[k], 'by': x.get('wby') or it.get('updatedBy') or '?', 'at': x.get('at') or ''})
                x['alts'] = al[-10:]
            x[k] = v
        x['at'] = stamp(); x['src'] = 'content'; x['wby'] = BY; it['ai'] = x; touch(it); return i
    print('ok', commit('content: ai %s' % a.id, fn))

def cmd_add(a):
    if a.type not in TYPES: sys.exit('نوع: reel | post | story')
    def fn(I, M, T):
        nid = a.type[0] + format(int(time.time() * 1000), 'x')[-9:]
        it = {'type': a.type, 'title': a.title, 'date': norm_date(a.date) if a.date else '', 'time': '', 'owner': a.owner or '', 'stage': 'concept',
              'concept': {'text': a.concept or '', 'ap': {'status': 'draft'}}, 'stages': {}, 'tasks': [], 'comments': [], 'tags': [],
              'createdAt': stamp(), 'createdBy': BY}
        if a.board: it['boardTask'] = B.find(T, a.board)
        touch(it); I[nid] = it; logc(M, 'ساخت «%s» توسط Claude' % a.title); return nid
    print('ok', commit('content: add', fn))

def cmd_link(a):
    def fn(I, M, T):
        i = find(I, a.id); t = B.find(T, a.task); I[i]['boardTask'] = t; touch(I[i]); return i + ' → ' + t
    print('ok', commit('content: link', fn))

# ---------------- sync ----------------
def sync_core(I, M, T, nm):
    global NAME2ID
    nmap = nm; NAME2ID = {v: k for k, v in nm.items()}
    ch = []
    groups = {}
    for k, it in I.items():
        if it.get('archived') or not it.get('boardTask'): continue
        if it['boardTask'] not in T: ch.append('پیوند شکسته: «%s» → %s' % (it.get('title'), it['boardTask'])); continue
        groups.setdefault(it['boardTask'], []).append((k, it))
    id2name = nm
    for tid, lst in groups.items():
        t = T[tid]; changed = False
        if len(lst) == 1:
            k, it = lst[0]
            # main → content: owner only fills a blank
            if not it.get('owner') and t.get('owner') and t['owner'] not in ('CL',):
                it['owner'] = id2name.get(t['owner'], t['owner']); touch(it); ch.append('«%s»: مسئول از برد اصلی ← %s' % (it.get('title'), it['owner']))
            # publish date: three-way sync (last synced value decides which side changed)
            cd = it.get('date') or ''; md = B.fmt_j(t['due']) if t.get('due') is not None else ''; sd = (it.get('sync') or {}).get('date')
            push = pull = False
            if cd == md: pass
            elif it.get('stage') == 'done' and cd: push = True
            elif sd is None:
                if not cd: pull = True
                elif not md: push = True
                else: CONFLICTS.append((it.get('title'), t.get('t'), cd, md))
            elif cd != sd and md == sd: push = True
            elif md != sd and cd == sd: pull = True
            else: CONFLICTS.append((it.get('title'), t.get('t'), cd, md))
            if push and cd:
                t['due'] = jdn(cd)
                if t.get('start') is not None and t['start'] > t['due']: t['start'] = t['due']
                changed = True; ch.append('برد اصلی «%s»: موعد ← %s (از برد محتوا)' % (t.get('t'), human(cd)))
            if pull and md:
                it['date'] = md; touch(it); ch.append('«%s»: تاریخ انتشار ← %s (از برد اصلی)' % (it.get('title'), human(md)))
            if (it.get('date') or '') == (B.fmt_j(t['due']) if t.get('due') is not None else ''):
                it['sync'] = {'date': it.get('date') or ''}
            want = 'done' if it.get('stage') == 'done' else ('doing' if sidx(it) > 0 and not it.get('stageTasks') else None)
            if want and t.get('status') != want and not (want == 'doing' and t.get('status') in ('done', 'review', 'paused')):
                t['status'] = want; changed = True; ch.append('برد اصلی «%s»: وضعیت ← %s' % (t.get('t'), want))
                if want == 'done' and not t.get('doneAt'): t['doneAt'] = B.today_j()
            # stage checklist mirror
            f = [x for x in flow(it) if x != 'done']; si = sidx(it); st = it.get('stages') or {}
            ck = t.get('check') or []; keep = [c for c in ck if not c.get('cb')]
            mirror = [{'x': lbl(it.get('type'), s), 'done': bool((st.get(s) or {}).get('done') or i < si or it.get('stage') == 'done'), 'cb': 1} for i, s in enumerate(f)]
            old = [c for c in ck if c.get('cb')]
            if [(c['x'], c['done']) for c in old] != [(c['x'], c['done']) for c in mirror]:
                # drop legacy free-text items that duplicate a mirrored stage name
                names_ = {c['x'] for c in mirror}
                keep = [c for c in keep if c.get('x') not in names_ and not any(c.get('x', '').startswith(n) for n in names_)]
                t['check'] = keep + mirror; changed = True
        else:
            lst.sort(key=lambda kv: kv[1].get('date') or '9999')
            mirror = [{'x': '%s · %s' % (human(it.get('date')), it.get('title')), 'done': it.get('stage') == 'done', 'cb': 1} for k, it in lst]
            ck = t.get('check') or []; keep = [c for c in ck if not c.get('cb') and not re.match(r'^(پست|استوری|روزشمار) ?\d|^پست \d', c.get('x', ''))]
            old = [c for c in ck if c.get('cb')]
            if [(c['x'], c['done']) for c in old] != [(c['x'], c['done']) for c in mirror]:
                t['check'] = keep + mirror; changed = True
            dates = [jdn(it.get('date')) for k, it in lst if it.get('date')]
            if dates and t.get('due') != max(dates): t['due'] = max(dates); changed = True
            if dates and (t.get('start') is None or t['start'] > min(dates)): t['start'] = min(dates); changed = True
            alld = all(it.get('stage') == 'done' for k, it in lst)
            want = 'done' if alld else ('doing' if any(it.get('stage') == 'done' or sidx(it) > 0 for k, it in lst) else None)
            if want and t.get('status') != want and not (want == 'doing' and t.get('status') in ('done', 'review', 'paused')):
                t['status'] = want; changed = True; ch.append('برد اصلی «%s»: وضعیت ← %s (%s از %s منتشر شده)' % (t.get('t'), want, fa(sum(1 for k, it in lst if it.get('stage') == 'done')), fa(len(lst))))
                if want == 'done' and not t.get('doneAt'): t['doneAt'] = B.today_j()
        if changed:
            t['upd'] = int(time.time() * 1000); t['by'] = 'CL'
            if not any(c.startswith('برد اصلی «%s»' % t.get('t')) for c in ch): ch.append('برد اصلی «%s»: چک‌لیست و موعد با برد محتوا هم‌گام شد' % t.get('t'))
    # brief/prompt/ideas: whatever the agent writes on the main task shows in the content item's «یادداشت Claude»
    for k, it in I.items():
        t = T.get(it.get('boardTask') or '')
        if not t or it.get('archived'): continue
        ai = it.get('ai') or {}
        if ai.get('src', 'main') != 'main': continue
        new = {'brief': t.get('briefNote') or '', 'prompt': t.get('promptNote') or '', 'ideas': t.get('ideaNote') or ''}
        if any(new.values()) and any((ai.get(x) or '') != new[x] for x in new):
            ai.update(new); ai['src'] = 'main'; ai['at'] = stamp(); it['ai'] = ai; ch.append('«%s»: یادداشت Claude از برد اصلی به‌روز شد' % it.get('title'))
    # stage-level links: item.stageTasks = {stage: [main task ids]}
    for k, it in I.items():
        if it.get('archived') or not it.get('stageTasks'): continue
        st = it.setdefault('stages', {}); ss = it.setdefault('sync', {}).setdefault('stages', {}); f = flow(it); moved = False
        for s, tids in it['stageTasks'].items():
            if s not in f: continue
            tids = [x for x in (tids if isinstance(tids, list) else [tids]) if x in T]
            if not tids: continue
            x = st.setdefault(s, {}); prev = ss.get(s) or {}
            past = f.index(s) < sidx(it) or it.get('stage') == 'done'
            c_done = bool(x.get('done') or past); m_done = all(T[t].get('status') == 'done' for t in tids)
            # done: either side finishing finishes the other
            if m_done and not c_done:
                x['done'] = True; touch(it); ch.append('«%s»: مرحلهٔ %s تمام شد (از برد اصلی)' % (it.get('title'), lbl(it.get('type'), s))); c_done = True
                if f.index(s) >= sidx(it):
                    nxt = next((y for y in f[f.index(s) + 1:] if not (st.get(y) or {}).get('done')), 'done'); move_stage(it, nxt); moved = True
            elif c_done and not m_done and len(tids) == 1 and not any(s2 != s and tids[0] in (v if isinstance(v, list) else [v]) and not ((st.get(s2) or {}).get('done') or f.index(s2) < sidx(it)) for s2, v in it['stageTasks'].items() if s2 in f):
                t = T[tids[0]]
                shared = [o for o in I.values() if o is not it and not o.get('archived') and any(tids[0] in (v if isinstance(v, list) else [v]) for v in (o.get('stageTasks') or {}).values())]
                if not shared or all(any(((o.get('stages') or {}).get(s3) or {}).get('done') or (s3 in flow(o) and flow(o).index(s3) < sidx(o)) for s3, v in (o.get('stageTasks') or {}).items() if tids[0] in (v if isinstance(v, list) else [v])) for o in shared):
                    t['status'] = 'done'; t['doneAt'] = t.get('doneAt') or B.today_j(); t['upd'] = int(time.time() * 1000); t['by'] = 'CL'; ch.append('برد اصلی «%s»: انجام شد (از برد محتوا)' % t.get('t'))
            # due & owner: three-way with the main task (earliest due among linked tasks)
            md = min([B.fmt_j(T[t]['due']) for t in tids if T[t].get('due') is not None] or [''])
            mo = next((nmap.get(T[t].get('owner'), T[t].get('owner')) for t in tids if T[t].get('owner') and T[t].get('owner') != 'CL'), '')
            for fld, mv in (('due', md), ('owner', mo)):
                cv = x.get(fld) or ''; sv = prev.get(fld)
                if cv == mv: continue
                if sv is None or cv == sv:
                    if mv: x[fld] = mv; touch(it); ch.append('«%s»: %s مرحلهٔ %s ← %s (از برد اصلی)' % (it.get('title'), 'موعد' if fld == 'due' else 'مسئول', lbl(it.get('type'), s), human(mv) if fld == 'due' else mv))
                elif mv == sv and len(tids) == 1:
                    t = T[tids[0]]
                    if fld == 'due' and cv: t['due'] = jdn(cv)
                    elif fld == 'owner' and cv: t['owner'] = NAME2ID.get(cv, t.get('owner'))
                    t['upd'] = int(time.time() * 1000); t['by'] = 'CL'; ch.append('برد اصلی «%s»: %s ← %s (از برد محتوا)' % (t.get('t'), 'موعد' if fld == 'due' else 'مسئول', human(cv) if fld == 'due' else cv))
            ss[s] = {'due': x.get('due') or '', 'owner': x.get('owner') or ''}
    # concept/title change watch (تأیید ممضی ۱۱ آبان): تغییر کانسپت = خط هشدار روی تسک برد اصلی + کانسپت تازه در notes
    for k, it in I.items():
        if it.get('archived') or it.get('stage') == 'done': continue
        sig = hashlib.sha1(((it.get('title') or '') + '|' + ((it.get('concept') or {}).get('text') or '')).encode('utf8')).hexdigest()[:12]
        cs = it.get('conceptSync') or {}
        if cs.get('sig') == sig: continue
        first = not cs.get('sig')
        it['conceptSync'] = {'sig': sig, 'at': cs.get('at') or '', 'line': cs.get('line') or ''}
        if first: continue
        line = '⚠️ کانسپت «%s» عوض شد (%s): تسک‌های مرحله و پرامپت تدوین رو چک کن' % (it.get('title'), human(today()))
        it['conceptSync'].update({'at': today(), 'line': line}); touch(it)
        tids = [it.get('boardTask')] if it.get('boardTask') else []
        for v in (it.get('stageTasks') or {}).values(): tids += v if isinstance(v, list) else [v]
        solo = len([1 for o in I.values() if not o.get('archived') and o.get('boardTask') == it.get('boardTask')]) == 1
        for i, tid in enumerate(dict.fromkeys(tids)):
            t = T.get(tid)
            if not t or t.get('status') == 'done': continue
            if tid == it.get('boardTask') or not it.get('boardTask') or not i:
                if not any(c.get('x') == line for c in t.get('check') or []): t['check'] = (t.get('check') or []) + [{'x': line, 'done': False}]
            if solo or tid != it.get('boardTask'):
                n = re.sub(r'\[کانسپت از برد محتوا\][^\n]*\n?', '', t.get('notes') or '')
                t['notes'] = '[کانسپت از برد محتوا] %s\n%s' % (((it.get('concept') or {}).get('text') or '').replace('\n', ' '), n)
            t['upd'] = int(time.time() * 1000); t['by'] = 'CL'
        ch.append('«%s»: کانسپت عوض شد، به برد اصلی خبر داده شد' % it.get('title'))
    return ch

def cmd_sync(a):
    if a.dry:
        B.ensure(); I = B.load('content_items'); M = B.load('content_meta'); T = B.load('tasks')
        for c in sync_core(I, M, T, names()): print('-', c)
        for c in CONFLICTS: print('! اختلاف تاریخ: «%s» محتوا %s / برد اصلی %s' % (c[0], human(c[2]), human(c[3])))
        return
    out = {}
    def fn(I, M, T):
        ch = sync_core(I, M, T, names()); out['ch'] = ch
        if ch: logc(M, 'هم‌گام‌سازی با برد اصلی: %s تغییر' % fa(len(ch)))
        return len(ch)
    n = commit('content: sync با برد اصلی', fn)
    for c in out.get('ch', []): print('-', c)
    for c in CONFLICTS: print('! اختلاف تاریخ: «%s» در برد محتوا %s ولی «%s» در برد اصلی %s — هیچ‌کدوم عوض نشد؛ با تیم روشنش کن و یکی رو درست کن' % (c[0], human(c[2]), c[1], human(c[3])))
    print('ok', n, 'تغییر')

# ---------------- check (supervisor for content) ----------------
def check_all():
    global NAME2ID
    B.ensure(); NAME2ID = {v: k for k, v in names().items()}; I = B.load('content_items'); M = B.load('content_meta'); T = B.load('tasks')
    S = (M.get('settings') or {}); R = dict({'reelGap': 5, 'noPostOnReelDay': True, 'dailyStory': True, 'storyFrom': '', 'storyTo': ''}, **(S.get('rules') or {}))
    td = today(); out = []
    def add(sev, text, who='', fix='', ids=()):
        out.append({'sev': sev, 'text': text, 'who': [w for w in [NAME2ID.get(who, who)] if w], 'fix': fix, 'ids': list(ids), 'k': 'C'})
    act = {k: v for k, v in I.items() if not v.get('archived') and not v.get('hold')}  # hold = متوقف به دستور ممضی، بدون هشدار
    for k, it in act.items():
        tt = it.get('title'); f = flow(it); st = it.get('stages') or {}
        if it.get('date') and it['date'] < td and it.get('stage') != 'done':
            add(2, '«%s» تاریخش (%s) گذشته ولی «منتشر شد» نخورده' % (tt, human(it['date'])), it.get('owner'), 'اگه رفته، تو برد محتوا «✓ منتشر شد» بزن؛ وگرنه تاریخ تازه بده', [k])
        for s in f:
            x = st.get(s) or {}
            if x.get('due') and x['due'] < td and not x.get('done') and f.index(s) >= sidx(it):
                add(2, '«%s»: مرحلهٔ %s عقب افتاده (موعد %s)' % (tt, lbl(it.get('type'), s), human(x['due'])), x.get('owner') or it.get('owner'), 'مرحله رو جلو ببر یا موعد تازه بده', [k])
        if it.get('date') and it.get('stage') != 'done':
            left = B.parse_j(it['date']) - B.today_j()
            if it.get('type') == 'reel' and 0 <= left <= 8 and sidx(it) <= f.index('shoot'):
                add(3, '«%s» %s روز تا انتشار داره ولی هنوز به تدوین نرسیده (حدود ۸ روز کاری لازمه)' % (tt, fa(left)), it.get('owner'), 'تاریخ ضبط رو همین الان قفل کن یا پلن جایگزین', [k])
            if 0 <= left <= 2:
                for s in APS:
                    if s in ('scenario', 'storyboard') and it.get('type') != 'reel': continue
                    if s == 'caption' and it.get('type') == 'story': continue
                    if ap(it, s) in ('draft', 'fix') and s in ('concept', 'caption'):
                        add(2, '«%s»: %s هنوز تأیید نشده و %s روز تا انتشار مونده' % (tt, s == 'concept' and 'کانسپت' or 'کپشن', fa(left)), 'M', 'بفرست برای تأیید', [k])
        if it.get('type') in ('reel', 'post') and not it.get('date'):
            add(1, '«%s» تاریخ انتشار نداره' % tt, it.get('owner'), 'تاریخ بده', [k])
        if not it.get('owner') and it.get('stage') != 'done':
            add(1, '«%s» مسئول نداره' % tt, '', 'مسئول کل بده', [k])
        for s in APS:
            if ap(it, s) == 'fix': add(2, '«%s»: %s نیاز به اصلاح خورده' % (tt, s), it.get('owner'), 'یادداشت بازبینی رو ببین و اصلاح کن', [k])
    by = {}
    for k, it in act.items():
        if it.get('date'): by.setdefault(it['date'], []).append(it)
    if R.get('noPostOnReelDay'):
        for d, l in by.items():
            if any(i.get('type') == 'reel' for i in l) and any(i.get('type') == 'post' for i in l): add(2, '%s: ریل و پست در یک روز' % human(d), 'A', 'یکی رو جابه‌جا کن')
    reels = sorted([it for it in act.values() if it.get('type') == 'reel' and it.get('date')], key=lambda x: x['date'])
    for x, y in zip(reels, reels[1:]):
        g = B.parse_j(y['date']) - B.parse_j(x['date'])
        if g < int(R.get('reelGap') or 5): add(2, 'فاصلهٔ «%s» و «%s» %s روزه' % (x.get('title'), y.get('title'), fa(g)), 'A', 'حداقل %s روز' % fa(R.get('reelGap') or 5))
    if R.get('dailyStory') and R.get('storyFrom') and R.get('storyTo'):
        miss = [B.fmt_j(n) for n in range(max(B.parse_j(R['storyFrom']), B.today_j()), B.parse_j(R['storyTo']) + 1) if not any(i.get('type') == 'story' for i in by.get(B.fmt_j(n), []))]
        if miss: add(1, '%s روز آینده استوری برنامه‌ریزی‌شده نداره: %s' % (fa(len(miss)), '، '.join(human(d) for d in miss[:5])), 'A', 'استوری اضافه کن')
    Tm = B.load('tasks')
    for k, it in act.items():
        cs = it.get('conceptSync') or {}
        if not cs.get('at') or not it.get('date') or it.get('stage') == 'done': continue
        t = Tm.get(it.get('boardTask') or '')
        open_ = t and any(c.get('x') == cs.get('line') and not c.get('done') for c in t.get('check') or [])
        if open_ and jdn(it['date']) - jdn(today()) <= 2:
            add(3, 'کانسپت «%s» عوض شده و کمتر از ۲ روز تا انتشار مونده' % it.get('title'), 'ممضی', 'تسک‌های مرحله و پرامپت تدوین رو هم‌خط کن و خط هشدار رو تیک بزن', (k,))
    for k, it in act.items():
        t = Tm.get(it.get('boardTask') or '')
        if t and len([1 for x in act.values() if x.get('boardTask') == it['boardTask']]) == 1 and t.get('due') is not None and it.get('date') and B.fmt_j(t['due']) != it['date'] and (it.get('sync') or {}).get('date') not in (it['date'], B.fmt_j(t['due'])):
            add(3, 'تاریخ «%s» دو جا فرق داره: برد محتوا %s، برد اصلی %s' % (it.get('title'), human(it['date']), human(B.fmt_j(t['due']))), 'M', 'یکی رو انتخاب کن و تو همون برد درستش کن؛ بعد sync', [k])
    unl = [it.get('title') for it in act.values() if not it.get('boardTask') and it.get('type') == 'reel']
    if unl: add(1, '%s ریل به تسک برد اصلی وصل نیست: %s' % (fa(len(unl)), '، '.join(unl[:4])), 'CL', 'content.py link')
    out.sort(key=lambda r: -r['sev'])
    return out

def render(out, limit=30):
    if not out: return '- هشداری نیست.\n'
    nmx = names()
    return '\n'.join('- **%s** · %s%s%s' % (SEV[r['sev']], r['text'], (' — برای: ' + '، '.join(nmx.get(w, w) for w in r['who'])) if r['who'] else '', (' ← ' + r['fix']) if r['fix'] else '') for r in out[:limit]) + '\n'

def cmd_check(a):
    out = check_all()
    if a.json: print(json.dumps(out, ensure_ascii=False, indent=1))
    else: print(render(out))

def summary():
    B.ensure(); I = B.load('content_items'); td = today(); n = B.today_j()
    act = [it for it in I.values() if not it.get('archived')]
    pub = [it for it in act if it.get('stage') == 'done']
    soon = sorted([it for it in act if it.get('date') and td <= it['date'] and B.parse_j(it['date']) - n <= 7], key=lambda x: x['date'])
    o = ['## برد تولید محتوا', '', '- %s محتوا · %s منتشر شده · ریل‌ها: %s' % (fa(len(act)), fa(len(pub)), '، '.join('%s (%s، %s)' % (it.get('title'), human(it.get('date')), lbl('reel', it.get('stage') or 'concept')) for it in sorted([x for x in act if x.get('type') == 'reel'], key=lambda x: x.get('date') or '9'))), '']
    o += ['### ۷ روز آینده', ''] + (['- %s · %s · %s · %s' % (human(it['date']), TYPES.get(it.get('type')), it.get('title'), lbl(it.get('type'), it.get('stage') or 'concept')) for it in soon] or ['- چیزی برنامه‌ریزی نشده.']) + ['']
    o += ['### هشدارهای برد محتوا', '', render(check_all(), 15)]
    return '\n'.join(o) + '\n'

def main():
    global NAME2ID
    ap_ = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); ap_.add_argument('--by', default='Claude', help='نام نویسنده برای ثبت نسخه و تاریخچه'); ap_.add_argument('--force', action='store_true', help='نوشتن روی محتوای hold'); sp = ap_.add_subparsers(dest='cmd', required=True)
    s = sp.add_parser('list'); s.add_argument('--type'); s.add_argument('--stage'); s.add_argument('--q')
    s = sp.add_parser('show'); s.add_argument('id')
    s = sp.add_parser('set'); s.add_argument('id'); s.add_argument('kv', nargs='+')
    s = sp.add_parser('stage'); s.add_argument('id'); s.add_argument('key')
    s = sp.add_parser('approve'); s.add_argument('id'); s.add_argument('sec'); s.add_argument('st'); s.add_argument('note', nargs='?')
    s = sp.add_parser('task'); s.add_argument('id'); s.add_argument('text'); s.add_argument('--owner'); s.add_argument('--due'); s.add_argument('--stage')
    s = sp.add_parser('comment'); s.add_argument('id'); s.add_argument('text')
    s = sp.add_parser('ai'); s.add_argument('id'); s.add_argument('--brief'); s.add_argument('--prompt'); s.add_argument('--ideas')
    s = sp.add_parser('add'); s.add_argument('type'); s.add_argument('title'); s.add_argument('--date'); s.add_argument('--owner'); s.add_argument('--concept'); s.add_argument('--board')
    s = sp.add_parser('link'); s.add_argument('id'); s.add_argument('task')
    s = sp.add_parser('sync'); s.add_argument('--dry', action='store_true')
    s = sp.add_parser('check'); s.add_argument('--md', action='store_true'); s.add_argument('--json', action='store_true')
    sp.add_parser('summary')
    s = sp.add_parser('alts'); s.add_argument('id'); s.add_argument('sec', nargs='?')
    s = sp.add_parser('pick'); s.add_argument('id'); s.add_argument('sec'); s.add_argument('n')
    a = ap_.parse_args()
    global BY, FORCE
    BY = (a.by or 'Claude').strip() or 'Claude'; FORCE = a.force
    if a.cmd in ('check', 'summary'):
        B.ensure(); NAME2ID = {v: k for k, v in names().items()}
    if a.cmd == 'summary': print(summary()); return
    {'list': cmd_list, 'show': cmd_show, 'set': cmd_set, 'stage': cmd_stage, 'approve': cmd_approve, 'task': cmd_task, 'comment': cmd_comment, 'ai': cmd_ai, 'add': cmd_add, 'link': cmd_link, 'sync': cmd_sync, 'check': cmd_check, 'alts': cmd_alts, 'pick': cmd_pick}[a.cmd](a)

if __name__ == '__main__': main()
