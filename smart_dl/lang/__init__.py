"""Language translation system for SmartDL."""
import os

_current_lang = None

def set_lang(lang_code: str):
    """Set the active language (e.g., 'en', 'fa')."""
    global _current_lang
    _current_lang = lang_code

def get_lang() -> str:
    """Get the active language code."""
    return _current_lang or _detect_lang()

def _detect_lang() -> str:
    """Auto-detect language from system locale."""
    # Check env vars
    for var in ["SMARTDL_LANG", "LANG", "LC_ALL", "LANGUAGE"]:
        val = os.environ.get(var, "")
        if val:
            if val.startswith("fa") or val.startswith("prs"):
                return "fa"
            return "en"
    # Check Windows UI language
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Control Panel\International")
        lang, _ = winreg.QueryValueEx(key, "LocaleName")
        if lang and lang.startswith("fa"):
            return "fa"
    except Exception:
        pass
    return "en"


# English strings
_EN = {
    # UI
    "title": "Smart YouTube & Podcast Downloader",
    "tagline": "bad connection? hold my retry loop.",
    "quit": "bye",
    "download_another": "Download another?",
    "yes": "y",
    "no": "n",

    # Main menu
    "url_prompt": "URL (q = quit \u00b7 p = proxy \u00b7 s = settings \u00b7 i = install \u00b7 c = cookies)",
    "invalid_url": "Not a valid URL. Start with http:// or https://",
    "cannot_handle": "Cannot handle this URL \u2014 yt-dlp could not extract any media.",

    # Quick guide
    "guide_title": "Quick Guide",
    "guide_youtube": "YouTube        Video or playlist URL \u2192 choose video/audio quality",
    "guide_aparat": "Aparat         Iranian video platform \u2192 videos + playlists",
    "guide_podcast": "Podcast        Direct MP3 link | RSS feed | SoundCloud | ...",
    "guide_stop": "Stop           Ctrl+C \u2014 partial file is saved and resumable",
    "guide_proxy": "P / p          Open proxy settings at any URL prompt",
    "guide_settings": "S / s          Open download settings (retries, fragment threads)",
    "guide_cookies": "C / c          Cookie settings (browser auth for bot detection)",
    "guide_install": "I / i          Install dependencies (ffmpeg, Node.js)",
    "how_many_lessons": "How many lessons? (0 = all)",
    "outline_only": "Course outline",
    "login_required": "Login / browser cookies required",
    "found_rss": "RSS feed found:",
    "episode_all": "All episodes",
    "castbox_channel": "Castbox channel",
    "downloaded_count": "Downloaded",
    "failed_count": "Failed",

    # Sections
    "analyzing_youtube": "Analyzing YouTube link",
    "analyzing_aparat": "Analyzing Aparat link",
    "analyzing_podcast": "Analyzing podcast link",
    "analyzing_video": "Analyzing video",
    "analyzing_playlist": "Analyzing playlist",
    "downloading": "Downloading",
    "quality_youtube": "Quality \u2014 video",
    "quality_podcast": "Quality \u2014 podcast",

    # Quality menu
    "select_quality": "Select quality #",
    "video_audio": "Video+Audio",
    "video_hd": "Video HD",
    "audio_only": "Audio Only",
    "best_quality": "Best Quality (auto)",
    "audio_mp3": "Audio MP3 192k",
    "needs_ffmpeg": "needs ffmpeg",
    "ffmpeg_not_found": "ffmpeg not found \u2014 Video HD rows need it for merging.",
    "ffmpeg_install_hint": "Type [bold]i[/bold] at URL prompt to install.",

    # Playlist
    "playlist_title": "Playlist",
    "playlist_videos": "Videos",
    "playlist_empty": "Playlist is empty or unavailable.",
    "download_mode": "Download Mode",
    "same_quality": "Same quality for all",
    "same_quality_desc": "Choose once \u2014 download all",
    "ask_per_video": "Ask per video",
    "ask_per_video_desc": "Choose quality for each video individually",
    "cancel": "Cancel",
    "fetching_formats": "Fetching format list from first video...",
    "could_not_fetch": "Could not fetch formats.",
    "skipping": "Skipping: could not fetch info.",
    "skipped_by_user": "Skipped by user",
    "playlist_complete": "Playlist Complete",
    "videos_downloaded": "videos downloaded",
    "skipped_videos": "Skipped Videos",
    "retry_skipped": "Retry skipped videos?",
    "retried_success": "All retried videos downloaded successfully.",
    "still_failed": "video(s) still failed after retry.",

    # Download
    "resume_enabled": "Resume enabled",
    "retries": "retries",
    "retry": "retry",
    "thread_fragments": "thread fragments",
    "download_complete": "Download complete!",
    "stopped_by_user": "Stopped by user.",

    # Proxy
    "proxy_setup": "Proxy Setup",
    "proxy_manual": "Enter proxy address manually",
    "proxy_manual_desc": "(http://host:port or socks5://host:port)",
    "proxy_localhost": "Use localhost port",
    "proxy_localhost_desc": "(v2rayN \u00b7 Clash \u00b7 Hiddify \u00b7 Nekoray)",
    "proxy_vpn": "I'm using a VPN",
    "proxy_vpn_desc": "(WireGuard \u00b7 OpenVPN \u00b7 AnyConnect)",
    "proxy_clear": "Clear proxy",
    "proxy_clear_desc": "(none)",
    "proxy_back": "Cancel / back",
    "proxy_set": "Proxy set:",
    "proxy_cleared": "Proxy cleared.",
    "proxy_unreachable": "Proxy unreachable:",
    "proxy_retry": "Clear proxy and retry without it?",
    "proxy_active": "Active proxy:",
    "proxy_none": "No proxy configured.",
    "proxy_press_p": "Press [bold cyan]P[/bold cyan] to set a proxy   or   [bold]Enter[/bold] to skip",
    "proxy_press_p_change": "Press [bold]P[/bold] to change / clear   or   Enter to continue",

    # Settings
    "settings_title": "Download Settings",
    "max_retries": "Max retries",
    "max_retries_infinite": "infinite",
    "fragment_threads": "Fragment threads",
    "settings_tip": "Tip: default values work best for most connections \u2014 change only if you know what you're doing.",
    "settings_retries_set": "Max retries set to:",
    "settings_threads_set": "Fragment threads set to:",

    # Install
    "install_title": "Install Dependencies",
    "install_ffmpeg": "Install ffmpeg",
    "install_wt": "Install Windows Terminal",
    "install_youtube": "Fix YouTube bot detection",
    "installed": "installed",
    "not_found": "not found",

    # Cookies
    "cookie_settings": "Cookie Settings",
    "cookie_active": "Active:",
    "cookie_reading_from": "reading cookies from",
    "cookie_clear_hint": "Type [bold]clear[/bold] to reset, or press Enter to keep it.",
    "cookie_cleared": "Cookie browser cleared.",
    "cookie_keeping": "Keeping:",
    "cookie_none": "No browser cookie source is set.",
    "cookie_none_hint": "This will be configured automatically the next time YouTube triggers a bot-detection or sign-in error.",
    "cookie_title": "Browser Cookie Source",

    # Bot detection
    "bot_detection_title": "Bot Detection",
    "bot_detection_msg": "YouTube is asking for a sign-in / bot check.",
    "bot_detection_fix": "SmartDL will fix this by reading cookies directly from your browser \u2014 no extension or export needed.",
    "bot_detection_hint": "Firefox and Edge work best on Windows. Chrome may not work due to Google's encryption.",
    "scanning_browsers": "Scanning installed browsers for a logged-in YouTube session...",
    "cookies_ok_node_missing": "cookies ok \u2014 Node.js missing",
    "node_required": "Node.js Required",
    "node_required_msg": "YouTube's bot check requires a JavaScript runtime to solve challenges.",
    "install_node": "Install Node.js now?",
    "no_browser_found": "No compatible browser found on this system.",
    "no_browser_hint": "Install Firefox or Edge, sign in to YouTube, then try downloading again.",
    "action_required": "Action Required",
    "action_required_msg": "SmartDL will open YouTube in your browser. Please sign in to your Google account, then come back here.",
    "which_browser": "Which browser will you use?",
    "press_enter_when_done": "Press Enter when done",
    "cookies_loaded": "Cookies loaded from",
    "cookies_saved": "saved for future downloads.",

    # Network errors
    "connection_error": "Connection Error",
    "connection_error_msg": "Connection failed \u2014 this usually means:",
    "connection_error_1": "No internet connection",
    "connection_error_2": "Host is blocked (common in Iran / restricted networks)",
    "connection_error_3": "Your proxy/VPN is off or misconfigured",
    "dns_failed": "DNS lookup failed \u2014 retrying...",
    "connection_reset": "Connection reset by server \u2014 retrying...",
    "network_error": "Network error",
    "network_error_hint": "Check your internet connection or proxy settings (press P).",
    "retrying_in": "Retrying in",
    "giving_up": "giving up. Try again later or check your connection.",

    # Output folder
    "output_folder": "Output Folder",
    "default_folder": "Default folder:",
    "output_set": "Output folder:",
    "folder_exists": "Folder exists \u2014",
    "folder_files": "file(s) inside",

    # Podcast
    "episode": "Episode",
    "no_episodes": "RSS feed found but no episodes.",
    "original": "Original (no conversion)",
    "original_desc": "Direct \u2014 fastest",
    "mp3_192": "MP3  192 kbps",
    "mp3_192_desc": "Good quality \u2014 requires ffmpeg",
    "mp3_128": "MP3  128 kbps",
    "mp3_128_desc": "Smaller file",
    "mp3_320": "MP3  320 kbps",
    "mp3_320_desc": "Highest MP3 quality",
    "m4a": "M4A (AAC) 128k",
    "m4a_desc": "Best for Apple",
    "ogg": "OGG  192 kbps",
    "ogg_desc": "Open format",
    "conversion_requires_ffmpeg": "Conversion options require ffmpeg",
    "select_episode": "Episode #",
    "converting_to": "Converting to",
    "downloaded": "Downloaded:",

    # Errors
    "error": "Error",
    "could_not_extract": "Could not extract video info.",
    "unsupported_url": "Unsupported URL \u2014 yt-dlp has no extractor for:",
    "proxy_error": "Proxy Error",
    "proxy_unreachable_hint": "Clear proxy and retry?",
}

# Persian/Farsi strings
_FA = {
    # UI
    "title": "\u0645\u0648\u0627\u0642\u0639 \u0627\u0637\u0644\u0627\u0639\u0627\u062a \u064a\u0648\u062a\u0648\u0628 \u0648 \u067e\u0648\u062f\u06a9\u0627\u0633\u062a",
    "tagline": "\u0627\u062a\u0635\u0627\u0644 \u0628\u0647 \u0646\u0638\u0631\u062a \u062f\u0627\u0631\u06cc\u061f \u062d\u0644\u0642\u0627\u0641\u062a \u0645\u0631\u0627 \u0628\u06af\u06cc\u0631.",
    "quit": "\u0628\u0627\u06cc",
    "download_another": "\u062c\u063a\u0631\u0627\u0634\u06cc \u062f\u06cc\u06af\u0631 \u062f\u0627\u0646\u0644\u0648\u062f \u062a\u0646\u0638\u06cc\u0645\u06cc\u062f\u061f",
    "yes": "\u0628\u0644\u0647",
    "no": "\u062e\u06cc\u0631",

    # Main menu
    "url_prompt": "\u0644\u0646\u06a9 (q = \u062e\u0631\u0648\u062c \u00b7 p = \u067e\u0631\u0648\u06a9\u0633\u06cc \u00b7 s = \u062a\u0646\u0638\u06cc\u0645\u0627\u062a \u00b7 i = \u0646\u0635\u0628 \u00b7 c = \u06a9\u0648\u06a9\u06cc)",
    "guide_title": "راهنمای سریع",
    "guide_youtube": "ویدیو یا پلی‌لیست → انتخاب کیفیت",
    "guide_aparat": "پلتفرم ایرانی → ویدیو و پلی‌لیست",
    "guide_podcast": "لینک مستقیم MP3 | فید RSS | SoundCloud | ...",
    "guide_stop": "Ctrl+C — فایل ناقص ذخیره و قابل ادامه است",
    "guide_proxy": "تنظیمات پروکسی در پرامپت URL",
    "guide_settings": "تنظیمات دانلود (تلاش مجدد، رشته‌های قطعه)",
    "guide_cookies": "تنظیمات کوکی (احراز هویت مرورگر)",
    "guide_install": "نصب وابستگی‌ها (ffmpeg, Node.js)",
    "how_many_lessons": "چند درس؟ (0 = همه)",
    "outline_only": "فهرست دوره",
    "login_required": "نیاز به لاگین / کوکی مرورگر",
    "found_rss": "فید RSS پیدا شد:",
    "episode_all": "همه اپیزودها",
    "castbox_channel": "کانال کست‌باکس",
    "downloaded_count": "دانلود شد",
    "failed_count": "ناموفق",
    "invalid_url": "\u0644\u0646\u06a9 \u0645\u0639\u062a\u0628\u0631 \u0646\u06cc\u0633\u062a. \u0628\u0627 \u0627\u0635\u0644 \u0627\u0632 http:// \u06cc\u0627 https:// \u0634\u0631\u0648\u0639 \u06a9\u0646\u06cc\u062f.",
    "cannot_handle": "\u0642\u0627\u0628\u0644 \u067e\u0631\u062f\u0627\u0632\u0634 \u0627\u0635\u0644 \u0644\u0646\u06a9 \u0646\u06cc\u0633\u062a \u2014 yt-dlp \u0646\u062a\u0648\u0627\u0646\u0633\u062a \u0645\u062f\u06cc\u0627 \u0631\u0627 \u0627\u0633\u062a\u062e\u0631\u062c \u06a9\u0646\u062f.",

    # Sections
    "analyzing_youtube": "\u062a\u062d\u0644\u06cc\u0644 \u0644\u0646\u06a9 \u0627\u0648\u062a\u06cc\u0648\u0628",
    "analyzing_aparat": "\u062a\u062d\u0644\u06cc\u0644 \u0644\u0646\u06a9 \u0627\u067e\u0627\u0631\u0627\u062a",
    "analyzing_podcast": "\u062a\u062d\u0644\u06cc\u0644 \u0644\u0646\u06a9 \u067e\u0648\u062f\u06a9\u0627\u0633\u062a",
    "analyzing_video": "\u062a\u062d\u0644\u06cc\u0644 \u0648\u06cc\u062f\u06cc\u0648",
    "analyzing_playlist": "\u062a\u062d\u0644\u06cc\u0644 \u067e\u0644\u0627\u0633\u062a",
    "downloading": "\u062f\u0631 \u062d\u0627\u0644 \u062f\u0648\u0631\u0647 \u0627\u0635\u0644\u0627\u0628",
    "quality_youtube": "\u06a9\u06cc\u0641\u06cc\u062a \u0648\u06cc\u062f\u06cc\u0648",
    "quality_podcast": "\u06a9\u06cc\u0641\u06cc\u062a \u067e\u0648\u062f\u06a9\u0627\u0633\u062a",

    # Quality menu
    "select_quality": "\u06a9\u06cc\u0641\u06cc\u062a \u0631\u0627 \u0627\u0646\u062a\u062e\u0627\u0628 \u06a9\u0646\u06cc\u062f #",
    "video_audio": "\u0648\u06cc\u062f\u06cc\u0648 + \u0635\u062f\u0627",
    "video_hd": "\u0648\u06cc\u062f\u06cc\u0648 HD",
    "audio_only": "\u0641\u0642\u0637 \u0635\u062f\u0627",
    "best_quality": "\u0628\u0647\u062a\u0631\u06cc\u0646 \u06a9\u06cc\u0641\u06cc\u062a (\u062e\u0648\u062f\u06a9\u0627\u0631)",
    "audio_mp3": "\u0635\u062f\u0627 MP3 192k",
    "needs_ffmpeg": "نیاز به ffmpeg",
    "ffmpeg_not_found": "ffmpeg یافت نشد — کیفیت‌های HD برای ادغام به آن نیاز دارند.",
    "ffmpeg_install_hint": "در پرامپت آدرس، حرف i را تایپ کنید تا نصب شود.",

    # Playlist
    "playlist_title": "پلی‌لیست",
    "playlist_videos": "ویدیوها",
    "playlist_empty": "پلی‌لیست خالی است یا در دسترس نیست.",
    "download_mode": "حالت دانلود",
    "same_quality": "کیفیت یکسان برای همه",
    "same_quality_desc": "یک بار انتخاب کنید — همه دانلود شوند",
    "ask_per_video": "پرسش برای هر ویدیو",
    "ask_per_video_desc": "انتخاب کیفیت به صورت جداگانه برای هر ویدیو",
    "cancel": "لغو",
    "fetching_formats": "در حال دریافت لیست کیفیت‌ها...",
    "could_not_fetch": "امکان دریافت لیست کیفیت‌ها وجود ندارد.",
    "skipping": "رد شدن: اطلاعات ویدیو دریافت نشد.",
    "skipped_by_user": "توسط کاربر رد شد",
    "playlist_complete": "پلی‌لیست تکمیل شد",
    "videos_downloaded": "ویدیو دانلود شد",
    "skipped_videos": "ویدیوهای رد شده",
    "retry_skipped": "تلاش مجدد برای ویدیوهای رد شده؟",
    "retried_success": "تمام ویدیوهای تکرار شده با موفقیت دانلود شدند.",
    "still_failed": "ویدیو همچنان پس از تلاش مجدد ناموفق ماند.",

    # Download
    "resume_enabled": "قابلیت ادامه (Resume) فعال است",
    "retries": "تلاش مجدد",
    "retry": "تلاش",
    "thread_fragments": "رشته‌های دانلود قطعات",
    "download_complete": "دانلود کامل شد!",
    "stopped_by_user": "توسط کاربر متوقف شد.",

    # Proxy
    "proxy_setup": "تنظیمات پروکسی",
    "proxy_manual": "وارد کردن دستی آدرس پروکسی",
    "proxy_manual_desc": "(http://host:port یا socks5://host:port)",
    "proxy_localhost": "استفاده از پورت لوکال‌هاست",
    "proxy_localhost_desc": "(v2rayN · Clash · Hiddify · Nekoray)",
    "proxy_vpn": "از VPN استفاده می‌کنم",
    "proxy_vpn_desc": "(WireGuard · OpenVPN · AnyConnect)",
    "proxy_clear": "حذف پروکسی",
    "proxy_clear_desc": "(بدون پروکسی)",
    "proxy_back": "لغو / بازگشت",
    "proxy_set": "پروکسی تنظیم شد:",
    "proxy_cleared": "پروکسی پاک شد.",
    "proxy_unreachable": "پروکسی در دسترس نیست:",
    "proxy_retry": "پروکسی پاک شود و بدون آن تلاش شود؟",
    "proxy_active": "پروکسی فعال:",
    "proxy_none": "هیچ پروکسی تنظیم نشده است.",
    "proxy_press_p": "کلید P را برای تنظیم پروکسی یا Enter را برای رد شدن فشار دهید",
    "proxy_press_p_change": "کلید P را برای تغییر/حذف یا Enter را برای ادامه فشار دهید",

    # Settings
    "settings_title": "تنظیمات دانلود",
    "max_retries": "حداکثر دفعات تلاش",
    "max_retries_infinite": "نامحدود",
    "fragment_threads": "رشته‌های قطعه",
    "settings_tip": "نکته: مقادیر پیش‌فرض برای اکثر اینترنت‌ها مناسب است — فقط در صورت نیاز تغییر دهید.",
    "settings_retries_set": "حداکثر دفعات تلاش تنظیم شد به:",
    "settings_threads_set": "رشته‌های دانلود قطعات تنظیم شد به:",

    # Install
    "install_title": "نصب پیش‌نیازها",
    "install_ffmpeg": "نصب ffmpeg",
    "install_wt": "نصب Windows Terminal",
    "install_youtube": "رفع مشکل بررسی ربات یوتیوب",
    "installed": "نصب شده",
    "not_found": "یافت نشد",

    # Cookies
    "cookie_settings": "تنظیمات کوکی",
    "cookie_active": "فعال:",
    "cookie_reading_from": "خواندن کوکی از مرورگر",
    "cookie_clear_hint": "برای بازنشانی clear را تایپ کنید، یا Enter را برای حفظ آن بزنید.",
    "cookie_cleared": "کوکی مرورگر پاک شد.",
    "cookie_keeping": "نگه‌داری:",
    "cookie_none": "هیچ مرورگری برای کوکی تنظیم نشده است.",
    "cookie_none_hint": "دفعه بعد که یوتیوب خطای ربات یا لاگین داد، به طور خودکار تنظیم می‌شود.",
    "cookie_title": "منبع کوکی مرورگر",

    # Bot detection
    "bot_detection_title": "تشخیص ربات",
    "bot_detection_msg": "یوتیوب نیاز به ورود به حساب کاربری / تایید امنیتی دارد.",
    "bot_detection_fix": "SmartDL با خواندن مستقیم کوکی‌ها از مرورگر شما مشکل را رفع می‌کند — نیازی به افزونه نیست.",
    "bot_detection_hint": "در ویندوز فایرفاکس و اج بهترین عملکرد را دارند. کروم ممکن است به دلیل رمزنگاری گوگل پاسخگو نباشد.",
    "scanning_browsers": "در حال اسکن مرورگرها برای یافتن نشست لاگین شده یوتیوب...",
    "cookies_ok_node_missing": "کوکی‌ها تایید شدند — Node.js یافت نشد",
    "node_required": "نیاز به Node.js",
    "node_required_msg": "بررسی ربات یوتیوب برای حل چالش‌ها به موتور جاوااسکریپت Node.js نیاز دارد.",
    "install_node": "آیا Node.js هم‌اکنون نصب شود؟",
    "no_browser_found": "هیچ مرورگر سازگاری در سیستم یافت نشد.",
    "no_browser_hint": "فایرفاکس یا اج را نصب کرده، در یوتیوب لاگین کنید و دوباره امتحان نمایید.",
    "action_required": "اقدام لازم است",
    "action_required_msg": "یوتیوب در مرورگر باز خواهد شد. لطفا وارد حساب گوگل خود شوید، سپس به اینجا بازگردید.",
    "which_browser": "از کدام مرورگر استفاده می‌کنید؟",
    "press_enter_when_done": "پس از اتمام، Enter را فشار دهید",
    "cookies_loaded": "کوکی‌ها بارگذاری شدند از",
    "cookies_saved": "برای دانلودهای بعدی ذخیره شد.",

    # Network errors
    "connection_error": "خطای ارتباط",
    "connection_error_msg": "ارتباط برقرار نشد — این خطا معمولاً ناشی از موارد زیر است:",
    "connection_error_1": "عدم اتصال به اینترنت",
    "connection_error_2": "سایت مورد نظر مسدود است (فیلترینگ)",
    "connection_error_3": "پروکسی یا VPN شما خاموش یا اشتباه تنظیم شده است",
    "dns_failed": "خطا در تحلیل DNS — در حال تلاش مجدد...",
    "connection_reset": "ارتباط از سمت سرور قطع شد — در حال تلاش مجدد...",
    "network_error": "خطای شبکه",
    "network_error_hint": "اتصال اینترنت یا تنظیمات پروکسی را بررسی کنید (کلید P).",
    "retrying_in": "تلاش مجدد در",
    "giving_up": "تلاش متوقف شد. لطفاً بعداً امتحان کرده یا اتصال خود را چک کنید.",

    # Output folder
    "output_folder": "پوشه خروجی",
    "output_set": "پوشه خروجی:",
    "default_folder": "پوشه پیش‌فرض:",
    "folder_exists": "پوشه موجود است —",
    "folder_files": "فایل داخل آن",

    # Podcast
    "episode": "اپیزود",
    "no_episodes": "فید RSS یافت شد اما هیچ اپیزودی ندارد.",
    "original": "اصلی (بدون تبدیل)",
    "original_desc": "مستقیم — سریع‌ترین",
    "mp3_192": "MP3  192 kbps",
    "mp3_192_desc": "کیفیت مناسب — نیازمند ffmpeg",
    "mp3_128": "MP3  128 kbps",
    "mp3_128_desc": "حجم کمتر",
    "mp3_320": "MP3  320 kbps",
    "mp3_320_desc": "بالاترین کیفیت MP3",
    "m4a": "M4A (AAC) 128k",
    "m4a_desc": "بهترین برای دستگاه‌های اپل",
    "ogg": "OGG  192 kbps",
    "ogg_desc": "فرمت متن‌باز",
    "conversion_requires_ffmpeg": "گزینه‌های تبدیل نیازمند ffmpeg هستند",
    "select_episode": "شماره اپیزود #",
    "converting_to": "در حال تبدیل به",
    "downloaded": "دانلود شد:",

    # Errors
    "error": "خطا",
    "could_not_extract": "امکان استخراج اطلاعات ویدیو وجود ندارد.",
    "unsupported_url": "لینک پشتیبانی نمی‌شود — yt-dlp اکسترکتوری برای این لینک ندارد:",
    "proxy_error": "خطای پروکسی",
    "proxy_unreachable_hint": "آیا پروکسی حذف شده و مجدداً تلاش شود؟",
}


_strings = {"en": _EN, "fa": _FA}


def t(key: str, **kwargs) -> str:
    """Translate a string key to the current language."""
    lang = get_lang()
    result = _strings.get(lang, _EN).get(key, _strings["en"].get(key, key))
    if kwargs:
        for k, v in kwargs.items():
            result = result.replace("{" + k + "}", str(v))
    return result
