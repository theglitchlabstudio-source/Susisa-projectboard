---
name: glitchlab-toolbox
description: Glitch Lab / Susisa toolbox. Use whenever a Susisa or Glitch Lab task involves making content or assets (carousel, product post, poster, infographic, isometric explainer, motion post, TV menu video, reel, caption, competitor analysis, website/QR menu) to pick the right free tool for each step, run it, and follow brand rules.
---

# جعبه‌ابزار گلیچ‌لب (سوسیسا)

منبع کامل و همیشه به‌روز: `agent/knowledge/27-toolbox.md` در مخزن
https://github.com/theglitchlabstudio-source/susisa-projectboard
(نسخهٔ وب: https://theglitchlabstudio-source.github.io/Susisa-projectboard/agent/knowledge/27-toolbox.md). اگر در دسترسه، اول همون رو بخون؛ این فایل خلاصه‌شه.

## قاعده‌ها
1. غذا همیشه از عکس واقعی آشپزخانه؛ AI فقط صحنه، نور، پس‌زمینه، گرافیک. اندازه یا تاپینگ رو عوض نکن.
2. متن فارسی رو داخل هیچ ابزاری ننویس؛ با HTML و فونت وزیرمتن یا لاله‌زار بساز، PNG کن، روی خروجی بذار.
3. پالت: قرمز #D5222B، کرم #FDF0D7، خردلی #F09E00، کربنی #2C2C2C. تگ‌لاین: too serious for a hot dog.
4. هر خروجی عمومی تأیید انسانی (امیرحسین یا ممضی) می‌خواد. هیچ مبلغ، توکن یا محتوای حساس ولت در ابزار یا خروجی.
5. محتوای بسته‌های سریال «سه بسته» هرگز لو نره.
6. ابزار GPU یا مرورگر سنگین فقط روی لپ‌تاپ؛ در محیط ابری پرامپت آماده بده.

## مرحله ← ابزار
| مرحله | ابزار پیش‌فرض | پشتیبان |
|---|---|---|
| کروسل محصول | عکس واقعی ← rembg ← صحنه با ComfyUI/Gemini ← Open Carrusel ← متن فارسی PNG | node-carousel، فتوشاپ |
| آناتومی محصول یا ظرف (نمای انفجاری) | SeeCode | Anatomy، iso-figure |
| قطعهٔ امضایی «چطور کار می‌کنه» (فر کراکف، ماشین بسته‌ها) | Anatomy (`/anatomy`) | SeeCode |
| پوستر پگ‌برد، اطلاعیه، اینفوگرافیک | EpicInfographics | فتوشاپ |
| پست موشن، منوی تلویزیون (MP4) | Remotion (+ Wan 2.2 برای حرکت عکس) | ffmpeg |
| ریل داستانی | ffmpeg و خط ماژول ۲۵ | Remotion برای کارت پایانی |
| کپشن، تبلیغ، لانچ | لحن ماژول ۰۰ + marketingskills / social-media-skills | دستی |
| تحلیل رقبا | instaloader (بی‌لاگین، آهسته، فقط پیج عمومی) | مرور دستی |
| سایت و منوی QR | awwwards skill | HTML دستی |

## نصب (Claude Code روی لپ‌تاپ)
`bash tools/install-toolbox.sh` در ریشهٔ مخزن برد.

## بعد از استفاده
در ماژول ۲۷ وضعیت ابزار رو «تست‌شده» کن و یک خط درس زیر «افزوده‌ها» بنویس (به‌خصوص فارسی و راست‌به‌چپ). ابزار رایگان تازه پیدا کردی؟ طبق بخش ۵ همون ماژول اضافه‌اش کن.
