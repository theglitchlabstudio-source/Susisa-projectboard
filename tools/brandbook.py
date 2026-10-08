#!/usr/bin/env python3
"""انتشار در برندبوک زندهٔ سوسیسا (مخزن theglitchlabstudio-source/Susisa-Brandbook، سایت GitHub Pages).

  brandbook.py chapters                       فهرست فصل‌ها و بخش‌ها (شناسه، عنوان، وضعیت، تسک مرتبط)
  brandbook.py show <فصل>                     محتوای یک فصل به Markdown
  brandbook.py upsert <فصل> <بخش> --md file.md [--title "عنوان"] [--st final|early|draft|open|later|raw] [--owner M|A|T] [--task <شناسهٔ تسک>]
                                              ساخت یا جایگزینی یک بخش (مثلاً 6.2) از روی Markdown
  brandbook.py log "متن تغییر"                 ثبت در «تاریخچهٔ تغییرات» و تاریخ به‌روزرسانی سایت
  brandbook.py save "پیام"                     commit و push (سایت چند دقیقه بعد به‌روز می‌شود)

Markdown پشتیبانی‌شده ← بلوک‌های برندبوک:
  پاراگراف ← p · «- مورد» ← list · «> نقل» ← quote · «!! متن» یا «!!! متن» ← note (هشدار) · جدول md ← table
  «### زیرتیتر» ← h · ```palette (نام | #HEX | کاربرد) ← swatches · «منبع: …» ← src · فهرست لینک‌های [متن](آدرس) ← links · ![توضیح](آدرس) ← img
قاعده‌ها (ماژول ۲۳): بدون مبلغ، بدون محتوای حساس ولت، بدون کد تسک در متن؛ لحن برند و قالب ماژول ۱۸ بخش ۱۲ برای دارایی‌های بصری.
"""
import json, os, re, subprocess, sys, time, argparse

CANDS = [os.environ.get('BRANDBOOK_DIR'), '/home/claude/susisa-brandbook', '/home/claude/theglitchlabstudio-source/susisa-brandbook', os.path.expanduser('~/.cache/susisa-brandbook')]
REMOTE = os.environ.get('BRANDBOOK_REMOTE', 'https://github.com/theglitchlabstudio-source/Susisa-Brandbook')
FA = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
MONTHS = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']

def repo():
    for c in CANDS:
        if c and os.path.isdir(os.path.join(c, '.git')): return c
    d = CANDS[-1]; os.makedirs(os.path.dirname(d), exist_ok=True)
    subprocess.run(['git', 'clone', '-q', REMOTE, d], check=True); return d

def git(*a, check=True): return subprocess.run(('git', '-C', repo()) + a, capture_output=True, text=True, check=check).stdout

def today_fa():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import board as B
    y, m, d = B.d2j(B.today_j()); return ('%d %s %d' % (d, MONTHS[m - 1], y)).translate(FA)

def load(n):
    p = os.path.join(repo(), 'data', 'ch%02d.js' % n)
    js = "var window={};var BB={ch:{}};%s;process.stdout.write(JSON.stringify(BB.ch[%d]))" % (open(p, encoding='utf8').read(), n)
    r = subprocess.run(['node', '-e', js], capture_output=True, text=True)
    if r.returncode: sys.exit('خواندن فصل %d نشد: %s' % (n, r.stderr[:300]))
    return json.loads(r.stdout)

def dump(n, ch):
    p = os.path.join(repo(), 'data', 'ch%02d.js' % n)
    open(p, 'w', encoding='utf8').write('BB.ch[%d] = %s;\n' % (n, json.dumps(ch, ensure_ascii=False, indent=1)))

def chapters():
    out = []
    for f in sorted(os.listdir(os.path.join(repo(), 'data'))):
        m = re.match(r'ch(\d\d)\.js$', f)
        if m: out.append(int(m.group(1)))
    return out

def md_to_blocks(md):
    blocks, lines, i = [], md.strip('\n').split('\n'), 0
    def para(buf):
        t = ' '.join(x.strip() for x in buf).strip()
        if not t: return
        m = re.match(r'^(منبع|منابع|مبنا)\s*[:：]\s*(.+)$', t)
        blocks.append({'type': 'src', 'label': m.group(1) + ':', 'text': m.group(2)} if m else {'type': 'p', 'text': t})
    buf = []
    while i < len(lines):
        ln = lines[i]; s = ln.strip()
        if s.startswith('```palette'):
            para(buf); buf = []; items = []; i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                ps = [x.strip() for x in lines[i].split('|')]
                if len(ps) >= 2 and re.match(r'^#[0-9A-Fa-f]{3,6}$', ps[1]): items.append({'name': ps[0], 'hex': ps[1].upper(), 'use': ps[2] if len(ps) > 2 else ''})
                i += 1
            blocks.append({'type': 'swatches', 'items': items}); i += 1; continue
        if not s: para(buf); buf = []; i += 1; continue
        if s.startswith('#'):
            para(buf); buf = []; blocks.append({'type': 'h', 'text': s.lstrip('#').strip()}); i += 1; continue
        if s.startswith('!!'):
            para(buf); buf = []; blocks.append({'type': 'note', 'kind': 'warn' if s.startswith('!!!') else '', 'text': s.lstrip('!').strip()}); i += 1; continue
        if s.startswith('>'):
            para(buf); buf = []; q = []
            while i < len(lines) and lines[i].strip().startswith('>'): q.append(lines[i].strip().lstrip('>').strip()); i += 1
            blocks.append({'type': 'quote', 'text': ' '.join(q)}); continue
        if re.match(r'^!\[[^\]]*\]\([^)]+\)$', s):
            para(buf); buf = []; m = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)$', s); blocks.append({'type': 'img', 'alt': m.group(1), 'src': m.group(2)}); i += 1; continue
        if re.match(r'^([-*•]|\d+[.)])\s+', s):
            para(buf); buf = []; items = []
            while i < len(lines) and re.match(r'^([-*•]|\d+[.)])\s+', lines[i].strip()):
                items.append(re.sub(r'^([-*•]|\d+[.)])\s+', '', lines[i].strip())); i += 1
            lk = [re.match(r'^\[([^\]]+)\]\((https?://[^)]+)\)$', x) for x in items]
            blocks.append({'type': 'links', 'items': [{'t': m.group(1), 'u': m.group(2)} for m in lk]} if all(lk) else {'type': 'list', 'items': items}); continue
        if s.startswith('|') and i + 1 < len(lines) and re.match(r'^\|?\s*:?-{2,}', lines[i + 1].strip()):
            para(buf); buf = []
            row = lambda x: [c.strip() for c in x.strip().strip('|').split('|')]
            head = row(s); i += 2; rows = []
            while i < len(lines) and lines[i].strip().startswith('|'): rows.append(row(lines[i])); i += 1
            blocks.append({'type': 'table', 'head': head, 'rows': rows}); continue
        buf.append(re.sub(r'\*\*|__', '', ln)); i += 1
    para(buf)
    return blocks

def blocks_to_md(bs):
    o = []
    for b in bs:
        t = b.get('type')
        if t == 'p': o.append(b['text'])
        elif t == 'h': o.append('### ' + b['text'])
        elif t == 'list': o.append('\n'.join('- ' + x for x in b['items']))
        elif t == 'quote': o.append('> ' + b['text'])
        elif t == 'note': o.append(('!!! ' if b.get('kind') == 'warn' else '!! ') + b['text'])
        elif t == 'table': o.append('\n'.join(['| ' + ' | '.join(b['head']) + ' |', '|' + '---|' * len(b['head'])] + ['| ' + ' | '.join(r) + ' |' for r in b['rows']]))
        elif t == 'swatches': o.append('```palette\n' + '\n'.join('%s | %s | %s' % (x.get('name'), x.get('hex'), x.get('use', '')) for x in b['items']) + '\n```')
        elif t == 'links': o.append('\n'.join('- [%s](%s)' % (x['t'], x['u']) for x in b['items']))
        elif t == 'src': o.append('%s %s' % (b.get('label', 'منبع:'), b.get('text', '')))
        elif t == 'img': o.append('![%s](%s)' % (b.get('alt', ''), b.get('src', '')))
        else: o.append('<!-- بلوک %s -->' % t)
    return '\n\n'.join(o)

def set_updated(ch):
    ch['updated'] = today_fa()

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sp = p.add_subparsers(dest='cmd', required=True)
    sp.add_parser('chapters')
    s = sp.add_parser('show'); s.add_argument('n', type=int)
    s = sp.add_parser('upsert'); s.add_argument('n', type=int); s.add_argument('sid'); s.add_argument('--md', required=True); s.add_argument('--title'); s.add_argument('--st', default='draft'); s.add_argument('--owner'); s.add_argument('--task'); s.add_argument('--after')
    s = sp.add_parser('log'); s.add_argument('text')
    s = sp.add_parser('save'); s.add_argument('msg')
    a = p.parse_args()
    if a.cmd == 'chapters':
        git('pull', '-q', '--rebase', check=False)
        for n in chapters():
            ch = load(n); print('فصل %d · %s (%s بخش)' % (n, ch.get('title'), len(ch.get('sections', []))))
            for x in ch.get('sections', []): print('   %-5s %-6s %s%s' % (x.get('id'), x.get('st'), x.get('t'), ('  [تسک %s]' % x['task']) if x.get('task') else ''))
    elif a.cmd == 'show':
        ch = load(a.n); print('# فصل %d · %s\n\n%s\n' % (a.n, ch.get('title'), ch.get('intro', '')))
        for x in ch.get('sections', []): print('## %s %s [%s]\n\n%s\n' % (x['id'], x['t'], x['st'], blocks_to_md(x.get('body', []))))
    elif a.cmd == 'upsert':
        if a.st not in ('raw', 'final', 'early', 'draft', 'open', 'later'): sys.exit('وضعیت نامعتبر')
        md = open(a.md, encoding='utf8').read(); body = md_to_blocks(md)
        if re.search(r'\b[snpxbeGgk]\d[0-9a-z]?\b|\bn0[0-9a-f]{6,}', md): print('هشدار: به نظر کد تسک در متن هست؛ عنوان را بنویس.', file=sys.stderr)
        ch = load(a.n); secs = ch.setdefault('sections', []); cur = next((x for x in secs if x.get('id') == a.sid), None)
        if cur:
            cur['body'] = body; cur['st'] = a.st
            if a.title: cur['t'] = a.title
            if a.owner: cur['owner'] = a.owner
            if a.task: cur['task'] = a.task
            act = 'به‌روز شد'
        else:
            if not a.title: sys.exit('بخش تازه عنوان می‌خواهد (--title)')
            cur = {'id': a.sid, 't': a.title, 'st': a.st, 'owner': a.owner or ch.get('owner', 'T'), 'body': body}
            if a.task: cur['task'] = a.task
            idx = next((k + 1 for k, x in enumerate(secs) if x.get('id') == a.after), None)
            if idx is None:
                key = lambda s: [int(x) if x.isdigit() else 0 for x in re.split(r'[.\-]', s)]
                idx = next((k for k, x in enumerate(secs) if key(x.get('id', '0')) > key(a.sid)), len(secs))
            secs.insert(idx, cur); act = 'اضافه شد'
        set_updated(ch); dump(a.n, ch); print('ok', 'فصل %d بخش %s %s (%d بلوک)' % (a.n, a.sid, act, len(body)))
    elif a.cmd == 'log':
        mp = os.path.join(repo(), 'data', 'meta.js'); s = open(mp, encoding='utf8').read(); d = today_fa()
        s = re.sub(r"(updated:\s*)'[^']*'", lambda m: m.group(1) + "'" + d + "'", s, count=1)
        s = s.replace('log: [', "log: [\n    {d:'%s', t:%s}," % (d, json.dumps(a.text, ensure_ascii=False)), 1)
        open(mp, 'w', encoding='utf8').write(s); print('ok log')
    elif a.cmd == 'save':
        for n in chapters():
            r = subprocess.run(['node', '-e', "var window={};var BB={ch:{}};" + open(os.path.join(repo(), 'data', 'ch%02d.js' % n), encoding='utf8').read()], capture_output=True, text=True)
            if r.returncode: sys.exit('فصل %d خراب است؛ ذخیره نشد: %s' % (n, r.stderr[:200]))
        git('add', '-A', 'data', 'assets')
        if not git('status', '--porcelain').strip(): print('بدون تغییر'); return
        git('-c', 'user.name=Claude', '-c', 'user.email=noreply@anthropic.com', 'commit', '-q', '-m', 'brandbook: ' + a.msg + ' (by Claude)')
        for _ in range(4):
            r = subprocess.run(['git', '-C', repo(), 'push', '-q', 'origin', 'HEAD:main'], capture_output=True, text=True)
            if r.returncode == 0: print('ok pushed'); return
            subprocess.run(['git', '-C', repo(), 'pull', '-q', '--rebase', 'origin', 'main'], capture_output=True, text=True)
        sys.exit('push ناموفق: ' + r.stderr.strip()[:300])

if __name__ == '__main__':
    main()
