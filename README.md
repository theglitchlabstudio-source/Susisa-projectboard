# برد پروژهٔ سوسیسا (Glitch Lab)

برد مستقل و نصب‌شدنی (PWA)؛ بدون وابستگی به Claude. هر commit روی `main` خودکار روی GitHub Pages می‌آید و دستگاه‌ها با باز کردن برد به‌روز می‌شوند.

**آدرس:** https://theglitchlabstudio-source.github.io/Susisa-projectboard/

## نصب
- **اندروید (Chrome):** منو ⋮ ← Install app / افزودن به صفحهٔ اصلی
- **آیفون (Safari):** Share ← Add to Home Screen
- **لپ‌تاپ (Chrome/Edge):** آیکون نصب کنار نوار آدرس

## فعال‌سازی همگام‌سازی آنلاین (یک‌بار، حدود ۵ دقیقه، رایگان)
1. https://console.firebase.google.com ← Add project (Analytics لازم نیست).
2. Build ← **Firestore Database** ← Create database (حالت production، هر منطقه).
3. تب **Rules** ← محتوای فایل `firestore.rules` همین ریپو را جایگزین و Publish کنید.
4. Project settings ← Your apps ← آیکون وب `</>` ← Register app ← مقادیر `firebaseConfig` را کپی کنید.
5. فایل `config.js` را ویرایش کنید: `apiKey`، `authDomain`، `projectId`، `appId` و یک `board` (کد طولانی و غیرقابل حدس مثل `susisa-k7x92mq4`) و commit کنید.
   - یا بدون ویرایش فایل: در برد ← تنظیمات ← «وضعیت اتصال» همان تنظیمات و کد برد را Paste کنید (باید روی هر دستگاه یک‌بار انجام شود).
6. روی هر دستگاه برد را باز کنید و در پروفایل نام خود را انتخاب کنید. نشان بالای صفحه باید «آنلاین · مشترک» شود.

## نکات
- «کد برد» نقش رمز را دارد؛ آن را فقط به امیرحسین بدهید. ریپو public است، پس اگر کد را در `config.js` می‌گذارید ریپو را Private کنید (Pages روی Private نیاز به پلن پولی دارد) یا کد را فقط از طریق تنظیمات برد روی دستگاه‌ها وارد کنید.
- فایل ضمیمه تا ۷۰۰ کیلوبایت در خود دیتابیس ذخیره می‌شود؛ برای فایل بزرگ لینک بگذارید.
- بدون تنظیم Firebase، برد در حالت محلی (فقط همان دستگاه) کار می‌کند.
