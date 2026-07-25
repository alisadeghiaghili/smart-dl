# SmartDL v3.0

> **اتصال ضعیفه؟ حلقه retry من رو نگه دار.**

دانلودر رسانه مقاوم برای شبکه‌های ناپایدار.
طراحی شده برای کاربران پشت اتصالات ضعیف و VPN — SmartDL هرگز تسلیم نمی‌شود.

[![Python](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

> اگر SmartDL در ساعت 3 صبح دانلود شکسته‌ات رو نجات داد — می‌دونی چیکار باید بکنی. ☕  
> **[buymeacoffee.com/alisadeghil](https://buymeacoffee.com/alisadeghil)**

---

## امکانات

### هسته
- **یوتیوب** — لیست کامل فرمت‌ها (همه رزولوشن‌ها، همه ترک‌های صوتی)
- **آپارات** — پشتیبانی بومی از پلتفرم ویدیوی ایران (ویدیو + پلی‌لیست)
- **۱۸۰۰+ سایت** — TikTok, Instagram, Twitter/X, Reddit, Twitch, Vimeo, SoundCloud و بیشتر
- **پادکست** — لینک‌های مستقیم MP3/M4A, فید RSS, SoundCloud و بیشتر

### مقاومت شبکه
- **بازتلاش بی‌نهایت با بکاف** — منتظر می‌ماند و در صورت خطا شبکه دوباره تلاش می‌کند
- **ادامه دانلود** — دقیقاً از جایی که متوقف شده ادامه می‌دهد
- **فرگمنت‌های چندنخی** — تا ۱۶ دانلود همزمان فرگمنت
- **تشخیص خطای هوشمند** — توضیح می‌دهد چه اتفاقی افتاده و چگونه رفعش کنید
- **پشتیبانی پروکسی** — پیکربندی HTTP/SOCKS5 پروکسی (v2ray, Clash, Hiddify, Nekoray)

### امکانات دانلود
- **برش ویدیو** — فقط بخشی از ویدیو را دانلود کنید (`--clip 00:01:30-00:05:00`)
- **SponsorBlock** — بخش‌های اسپانсор را به صورت خودکار رد کنید
- **زیرنویس** — دانلود، جستجو و جاسازی زیرنویس در ۵۰+ زبان
- **تصویر بندانگشتی** — دانلود و جاسازی تصویر بندانگشتی ویدیو
- **متادیتا** — جاسازی عنوان، هنرمند و سایر اطلاعات
- **استخراج صوت** — MP3, M4A, Opus, FLAC, WAV با کنترل کیفیت
- **فرمت‌های متعدد** — خروجی MP4, MKV, WebM, AVI

### حالت هوشمند
- **ذخیره تنظیمات** — کیفیت، فرمت و تنظیمات صوتی را یک بار تنظیم کنید
- **اعمال خودکار** — همه دانلودها از تنظیمات ذخیره شده استفاده می‌کنند

### صف و تاریخچه
- **صف دانلود** — چندین URL اضافه کنید، به صورت متوالی یا موازی پردازش کنید
- **تاریخچه دانلود** — پایگاه داده SQLite با جستجو، فیلتر و خروجی
- **اشتراک‌ها** — کانال‌ها را دنبال کنید و ویدیوهای جدید را خودکار دانلود کنید

### امکانات اضافی
- **گالری تصاویر** — دانلود از Pixiv, DeviantArt, ArtStation, Flickr, Imgur
- **تورنت/مگنت** — دانلود تورنت از طریق aria2c, transmission یا qBittorrent
- **حالت پرتابل** — از USB اجرا شود بدون دسترسی به پوشه‌های سیستم
- **۱۲ تم CLI** — Dracula, Catppuccin, Nord, Tokyo Night و بیشتر
- **رابط فارسی** — پشتیبانی کامل از زبان فارسی
- **اتوماسیون CLI** — ۴۰+ پرچم برای اسکریپت‌نویسی و اتوماسیون

---

## پیش‌نیازها

- Python 3.8+
- [ffmpeg](https://ffmpeg.org/) — برای ویدیوی HD (ادغام) و تبدیل MP3 ضروری است

### نصب ffmpeg (ویندوز)

```bash
winget install Gyan.FFmpeg
```

سپس ترمینال را ببندید و دوباره باز کنید.

---

## نصب

### گزینه ۱: pip (توصیه شده)

```bash
pip install smart-dl
```

### گزینه ۲: کلون و اجرا

```bash
git clone https://github.com/alisadeghiaghili/smart-dl.git
cd smart-dl
python smart_dl.py
```

وابستگی‌های پایتون (`yt-dlp`, `rich`, `requests`) در اولین اجرا به صورت خودکار نصب می‌شوند.

---

## استفاده

### حالت تعاملی

```bash
python smart_dl.py
```

### حالت CLI

```bash
# دانلود پایه
smart-dl "https://youtube.com/watch?v=abc123"

# کیفیت و فرمت
smart-dl URL -q best -o ~/Downloads
smart-dl URL --format mkv

# برش ویدیو
smart-dl URL --clip 00:01:30-00:05:00

# استخراج صوت
smart-dl URL --audio-only --audio-format flac --audio-quality 320

# SponsorBlock
smart-dl URL --sponsorblock

# زیرنویس
smart-dl URL --subtitles en,fa --embed-subs

# صف دانلود
smart-dl --queue add URL1 URL2 URL3
smart-dl --queue start

# تاریخچه دانلود
smart-dl --history list --sort date

# اشتراک‌ها
smart-dl --subscribe https://youtube.com/@channel
smart-dl --check-updates

# حالت هوشمند
smart-dl --smart-mode on

# گالری تصاویر
smart-dl https://www.pixiv.net/artworks/12345

# تورنت
smart-dl --torrent magnet:?xt=...

# تم
smart-dl --theme catppuccin

# پروکسی
smart-dl --proxy socks5://127.0.0.1:10808

# حالت پرتابل
smart-dl --portable
```

---

## پلتفرم‌های پشتیبانی شده

| پلتفرم | پشتیبانی |
|---------|----------|
| یوتیوب (ویدیو، پلی‌لیست، کانال، Shorts) | ✅ |
| آپارات (ویدیو، پلی‌لیست) | ✅ |
| TikTok | ✅ |
| Instagram | ✅ |
| Twitter / X | ✅ |
| Reddit | ✅ |
| Twitch | ✅ |
| Vimeo | ✅ |
| SoundCloud | ✅ |
| Bilibili | ✅ |
| پادکست RSS | ✅ |
| ۱۸۰۰+ سایت دیگر | ✅ |

---

## مقاومت شبکه

به طور خاص برای اتصالات ناپایدار ساخته شده:

- دانلودهای ناقص را به صورت خودکار ادامه می‌دهد
- بازتلاش با بکاف نمایی (۵ثانیه → ۷ثانیه → ۱۱ثانیه → ... تا ۵ دقیقه)
- محدودیت ۳۰ دقیقه‌ای بازتلاش (قابل تنظیم)
- خطاهای کشنده (ffmpeg نصب نیست، ویدیو خصوصی، کپی‌رایت) فوراً متوقف می‌شوند
- قطع اتصال به صورت ساکت مدیریت می‌شود؛ دانلوق وقتی شبکه برگشت ادامه می‌یابد

---

## سلب مسئولیت

SmartDL فقط برای **استفاده شخصی** در نظر گرفته شده. دانلود محتوای دارای حق چاپ بدون اجازه ممکن است شرایط استفاده YouTube و قوانین کشور شما را نقض کند. نویسندگان مسئولیتی در قبال سوءاستفاده از این ابزار ندارند.

---

## ☕ حمایت

SmartDL رایگان است و همیشه خواهد بود.  
حمایت‌ها هزینه انتشارهای سریع‌تر، تشخیص بهتر و نگهداری بلندمدت را تأمین می‌کنند.

[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png)](https://www.buymeacoffee.com/alisadeghil)

---

## مجوز

[MIT](LICENSE)
