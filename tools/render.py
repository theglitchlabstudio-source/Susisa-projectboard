#!/usr/bin/env python3
"""ساخت نسخهٔ خوانا و قابل چاپ از فایل‌های Markdown (برای تیم و برندبوک).

  render.py file.md [-o out.html] [--title "عنوان"] [--docx]
  render.py file.md --stdout

- خروجی: HTML تک‌فایلی، راست‌به‌چپ، با فونت وزیرمتن، آمادهٔ چاپ A4 (در مرورگر: Print ← Save as PDF).
- کد رنگ‌ها (#CC0212) خودکار نمونهٔ رنگ می‌گیرند.
- بلوک پالت: در Markdown بنویس
      ```palette
      قرمز سوسیسا | #CC0212 | رنگ اصلی، لوگو و تیترها
      کرم | #FDF0D7 | پس‌زمینه
      ```
  تا صفحهٔ پالت (نمونهٔ بزرگ، HEX، RGB، کنتراست با سفید/مشکی/کرم) ساخته شود.
- --docx: نسخهٔ Word هم با pandoc (اگر نصب باشد).
"""
import html, os, re, subprocess, sys, time

BRAND = {'red': '#CC0212', 'cream': '#FDF0D7', 'ink': '#22140F'}

def _rgb(h):
    h = h.lstrip('#')
    if len(h) == 3: h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def _lum(h):
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = _rgb(h); return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)

def contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True); return (la + 0.05) / (lb + 0.05)

def _grade(c):
    return 'AAA' if c >= 7 else 'AA' if c >= 4.5 else 'AA تیتر' if c >= 3 else 'ضعیف'

def palette_html(body):
    cards = []
    for line in body.strip().splitlines():
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 2 or not re.match(r'^#[0-9A-Fa-f]{3,6}$', parts[1]): continue
        name, hx, use = parts[0], parts[1].upper(), (parts[2] if len(parts) > 2 else '')
        r, g, b = _rgb(hx)
        rows = ''.join('<tr><td>روی %s</td><td>%.2f</td><td>%s</td></tr>' % (n, contrast(hx, bg), _grade(contrast(hx, bg)))
                       for n, bg in (('سفید', '#FFFFFF'), ('مشکی', '#000000'), ('کرم', BRAND['cream'])))
        cards.append('<div class="pal"><div class="chip" style="background:%s"><span style="color:%s">Aa</span></div><div class="pi"><b>%s</b><code>%s</code><code>RGB %d, %d, %d</code><small>%s</small>'
                     '<table class="ct"><tr><th>کنتراست متن</th><th>نسبت</th><th>سطح</th></tr>%s</table><small class="cm">CMYK: از نمونهٔ چاپی (پروف) بگیر، نه تبدیل خودکار</small></div></div>'
                     % (hx, '#FFFFFF' if _lum(hx) < 0.4 else '#000000', html.escape(name), hx, r, g, b, html.escape(use), rows))
    return '<div class="palette">%s</div>' % ''.join(cards)

def md_to_html(md):
    blocks = {}
    def keep(m):
        k = '@@PAL%d@@' % len(blocks); blocks[k] = palette_html(m.group(1)); return '\n\n' + k + '\n\n'
    md = re.sub(r'```palette\n(.*?)```', keep, md, flags=re.S)
    try:
        import markdown
        out = markdown.markdown(md, extensions=['tables', 'fenced_code', 'sane_lists', 'nl2br'])
    except Exception:
        try:
            out = subprocess.run(['pandoc', '-f', 'gfm', '-t', 'html'], input=md, capture_output=True, text=True, check=True).stdout
        except Exception:
            out = '\n'.join('<p>%s</p>' % html.escape(p).replace('\n', '<br>') for p in md.split('\n\n'))
    for k, v in blocks.items():
        out = out.replace('<p>%s</p>' % k, v).replace(k, v)
    # نمونهٔ رنگ کنار هر کد HEX در متن (نه داخل پالت و کد)
    def sw(m):
        return '<span class="sw" style="background:%s"></span>%s' % (m.group(0), m.group(0))
    parts = re.split(r'(<div class="palette">.*?</div></div></div>|<code>.*?</code>|<pre>.*?</pre>|<[^>]+>)', out, flags=re.S)
    out = ''.join(p if (p.startswith('<')) else re.sub(r'(?<![\w&])#[0-9A-Fa-f]{6}\b', sw, p) for p in parts)
    return out

CSS = """
:root{--red:#CC0212;--cream:#FDF0D7;--ink:#22140F;--mute:#7C6658;--line:#EEDDC6;--bg:#FFFBF4}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/2 Vazirmatn,Tahoma,sans-serif;direction:rtl}
.doc{max-width:860px;margin:0 auto;padding:28px 20px 60px}
.hd{display:flex;justify-content:space-between;align-items:baseline;gap:12px;border-bottom:3px solid var(--red);padding-bottom:10px;margin-bottom:24px;flex-wrap:wrap}
.hd b{font:400 28px/1 Lalezar,Vazirmatn,sans-serif;color:var(--red)}.hd span{color:var(--mute);font-size:13px}
h1{font:400 34px/1.35 Lalezar,Vazirmatn,sans-serif;margin:.2em 0 .6em}h2{font:400 25px/1.4 Lalezar,Vazirmatn,sans-serif;color:var(--red);margin:1.6em 0 .5em;border-bottom:1px solid var(--line);padding-bottom:4px}
h3{font-size:19px;margin:1.3em 0 .4em}p,li{unicode-bidi:plaintext}
table{border-collapse:collapse;width:100%;margin:12px 0;font-size:14.5px;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:6px 10px;text-align:right;vertical-align:top}th{background:var(--cream)}
blockquote{margin:14px 0;padding:8px 16px;border-inline-start:4px solid var(--red);background:#fff;border-radius:8px}
code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.88em;background:#fff;border:1px solid var(--line);border-radius:5px;padding:0 5px;direction:ltr;unicode-bidi:embed}
pre{background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px;overflow:auto;direction:ltr;text-align:left}pre code{border:0;padding:0}
a{color:var(--red)}hr{border:0;border-top:1px dashed var(--line);margin:24px 0}
.sw{display:inline-block;width:.95em;height:.95em;border-radius:3px;border:1px solid rgba(0,0,0,.15);margin-inline-end:4px;vertical-align:-2px}
.palette{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px;margin:16px 0}
.pal{background:#fff;border:1px solid var(--line);border-radius:16px;overflow:hidden;box-shadow:0 8px 20px -14px rgba(60,20,0,.5)}
.pal .chip{height:120px;display:flex;align-items:flex-end;padding:10px 14px;font:400 30px Lalezar,sans-serif}
.pal .pi{padding:10px 14px;display:flex;flex-direction:column;gap:2px}.pal .pi b{font-size:17px}.pal .pi code{align-self:flex-start}
.pal small{color:var(--mute);font-size:13px;line-height:1.7}.ct{font-size:12.5px;margin:6px 0}.ct th,.ct td{padding:2px 6px}
.ft{margin-top:40px;color:var(--mute);font-size:12px;border-top:1px solid var(--line);padding-top:8px}
@media print{body{background:#fff}.doc{max-width:none;padding:0}@page{size:A4;margin:16mm 14mm}h2{break-after:avoid}.pal,table,blockquote{break-inside:avoid}}
"""

def render(md, title=None, src=''):
    m = re.search(r'^#\s+(.+)$', md, re.M)
    title = title or (m.group(1).strip() if m else os.path.splitext(os.path.basename(src))[0] or 'سند')
    t = time.localtime()
    body = md_to_html(md)
    return ('<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>%s</title><link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Lalezar&family=Vazirmatn:wght@400;600;700&display=swap" rel="stylesheet">'
            '<style>%s</style></head><body><div class="doc"><div class="hd"><b>سوسیسا</b><span>گلیچ‌لب · نسخهٔ خوانا · %s</span></div>%s'
            '<div class="ft">ساخته‌شده از %s با tools/render.py · برای PDF: چاپ ← ذخیره به‌صورت PDF</div></div></body></html>\n') % (
        html.escape(title), CSS, time.strftime('%Y-%m-%d', t), body, html.escape(os.path.basename(src) or 'Markdown'))

def main(a):
    if not a or a[0] in ('-h', '--help'): print(__doc__); return
    src = a[0]; md = sys.stdin.read() if src == '-' else open(src, encoding='utf8').read()
    title = a[a.index('--title') + 1] if '--title' in a else None
    out = render(md, title, src)
    if '--stdout' in a: sys.stdout.write(out); return
    dst = a[a.index('-o') + 1] if '-o' in a else os.path.splitext(src)[0] + '.html'
    open(dst, 'w', encoding='utf8').write(out); print(dst)
    if '--docx' in a:
        d = os.path.splitext(dst)[0] + '.docx'
        r = subprocess.run(['pandoc', src, '-o', d, '-M', 'dir=rtl', '-M', 'lang=fa'], capture_output=True, text=True)
        print(d if r.returncode == 0 else 'docx ساخته نشد: ' + r.stderr.strip()[:200])

if __name__ == '__main__':
    main(sys.argv[1:])
