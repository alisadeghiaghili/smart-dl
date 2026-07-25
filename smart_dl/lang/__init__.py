"""Language translation system for SmartDL."""
import os
import json

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
    "needs_ffmpeg": "\u0646\u06cc\u0627\u0632 \u0628\u0647 ffmpeg",
    "ffmpeg_not_found": "ffmpeg \u06cc\u0627\u0641\u062a \u0646\u0634\u062f \u2014 \u0635\u0641\u062d\u0627\u062a HD \u0628\u0631\u0627\u06cc \u0627\u062f\u063a\u0627\u0645 \u0646\u06cc\u0627\u0632 \u062f\u0627\u0631\u0646\u062f.",

    # Playlist
    "playlist_title": "\u067e\u0644\u0627\u0633\u062a",
    "playlist_videos": "\u0648\u06cc\u062f\u0647\u0648\u0647\u0627",
    "playlist_empty": "\u067e\u0644\u0627\u0633\u062a \u062e\u0627\u0644\u06cc \u0627\u0633\u062a \u06cc\u0627 \u062f\u0631 \u062f\u0633\u062a\u0631\u0633 \u0627\u0633\u062a.",
    "download_mode": "\u062d\u0627\u0644\u062a \u062f\u0648\u0631\u0647",
    "same_quality": "\u06a9\u06cc\u0641\u06cc\u062a \u06cc\u06a9\u0627\u0646\u0647 \u0628\u0631\u0627\u06cc \u0647\u0645\u0647",
    "same_quality_desc": "\u06cc\u06a9 \u0628\u0627\u0631 \u0627\u0646\u062a\u062e\u0627\u0628 \u06a9\u0646\u06cc\u062f \u2014 \u0647\u0645\u0647 \u0631\u0627 \u062f\u0648\u0631\u0647 \u0628\u06af\u06cc\u0631\u06cc\u062f",
    "ask_per_video": "\u0628\u0631\u0627\u06cc \u0647\u0631 \u0648\u06cc\u062f\u06cc\u0648",
    "ask_per_video_desc": "\u06a9\u06cc\u0641\u06cc\u062a \u0631\u0627 \u0628\u0631\u0627\u06cc \u0647\u0631 \u0648\u06cc\u062f\u06cc\u0648 \u0627\u0646\u062a\u062e\u0627\u0628 \u06a9\u0646\u06cc\u062f",
    "cancel": "\u0644\u063a\u0648",
    "fetching_formats": "\u062f\u0631 \u062d\u0627\u0644 \u062f\u0631\u06cc\u0627\u0641\u062a\u0646 \u0644\u06cc\u0633\u062a \u06a9\u06cc\u0641\u06cc\u062a\u200c\u0647\u0627...",
    "playlist_complete": "\u062a\u0645\u0627\u0645 \u067e\u0644\u0627\u0633\u062a",
    "videos_downloaded": "\u0648\u06cc\u062f\u0647\u0648 \u062f\u0648\u0631\u0647 \u0634\u062f",

    # Download
    "resume_enabled": "\u0627\u062f\u0627\u0645\u0647 \u06af\u0631\u0641\u062a\u0647 \u0634\u062f\u0647",
    "download_complete": "\u062f\u0648\u0631\u0647 \u06a9\u0645\u0644 \u0634\u062f!",
    "stopped_by_user": "\u062a\u0648\u0633\u0637 \u06a9\u0627\u0631\u0628\u0631.",

    # Proxy
    "proxy_setup": "\u062a\u0646\u0638\u06cc\u0645\u0627\u062a \u067e\u0631\u0648\u06a9\u0633\u06cc",
    "proxy_set": "\u067e\u0631\u0648\u06a9\u0633\u06cc \u0633\u062a \u0634\u062f:",
    "proxy_cleared": "\u067e\u0631\u0648\u06a9\u0633\u06cc \u067e\u0627\u06a9 \u0634\u062f.",
    "proxy_unreachable": "\u067e\u0631\u0648\u06a9\u0633\u06cc \u0642\u0627\u0628\u0644 \u062f\u0633\u062a\u0631\u0633\u06cc \u0646\u06cc\u0633\u062a:",
    "proxy_none": "\u067e\u0631\u0648\u06a9\u0633\u06cc \u062a\u0646\u0638\u06cc\u0645 \u0646\u0634\u062f\u0647 \u0627\u0633\u062a.",

    # Settings
    "settings_title": "\u062a\u0646\u0638\u06cc\u0645\u0627\u062a \u062f\u0648\u0631\u0647",
    "max_retries": "\u062d\u062f\u0627\u06a9\u062b\u0631\u06cc\u0646 \u062a\u0644\u0627\u0634",
    "fragment_threads": "\u0631\u0634\u062a\u0647\u200c\u0647\u0627\u06cc \u0642\u0637\u0639\u0647",
    "settings_retries_set": "\u062d\u062f\u0627\u06a9\u062b\u0631\u06cc\u0646 \u062a\u0644\u0627\u0634 \u0628\u0647:",
    "settings_threads_set": "\u0631\u0634\u062a\u0647\u200c\u0647\u0627\u06cc \u0642\u0637\u0639\u0647 \u0628\u0647:",

    # Install
    "install_title": "\u0646\u0635\u0628 \u0627\u0648\u0644\u06cc\u062a\u200c\u0647\u0627",
    "install_ffmpeg": "\u0646\u0635\u0628 ffmpeg",
    "install_wt": "\u0646\u0635\u0628 Windows Terminal",
    "install_youtube": "\u0631\u0641\u0639 \u0627\u0634\u06a9\u0627\u0644 \u0628\u0648\u062a \u062f\u06cc\u062a\u06a9\u0634\u0646\u0646 YouTube",

    # Cookies
    "cookie_settings": "\u062a\u0646\u0638\u06cc\u0645\u0627\u062a \u06a9\u0648\u06a9\u06cc",
    "cookie_cleared": "\u06a9\u0648\u06a9\u06cc \u062f\u0631\u0627\u062e\u062a\u0631 \u0634\u062f.",

    # Network errors
    "connection_error": "\u062e\u0637\u0627 \u0627\u0631\u062a\u0628\u0627\u0637",
    "network_error": "\u062e\u0637\u0627\u06cc \u0634\u0628\u06a9\u0647",
    "network_error_hint": "\u0627\u062a\u0635\u0627\u0644 \u0627\u06cc\u0646\u062a\u0631\u0646\u062a \u06cc\u0627 \u067e\u0631\u0648\u06a9\u0633\u06cc \u0631\u0648 \u0628\u0631\u0631\u0633\u06cc \u06a9\u0646\u06cc\u062f (P \u0631\u0627 \u0628\u0632\u0646\u06cc\u062f).",
    "retrying_in": "\u062a\u0644\u0627\u0634 \u062f\u0648\u0631\u0647 \u062f\u0631",

    # Output folder
    "output_folder": "\u067e\u0648\u0634\u0647 \u062e\u0631\u0648\u062c",
    "output_set": "\u067e\u0648\u0634\u0647 \u062e\u0631\u0648\u062c:",

    # Errors
    "error": "\u062e\u0637\u0627",
    "unsupported_url": "\u0644\u0646\u06a9 \u067e\u0634\u062a\u06cc\u0628\u0627\u0646\u062f\u0647 \u0646\u06cc\u0633\u062a \u2014 yt-dlp \u0627\u0633\u062a\u062e\u0631\u062c\u06af\u0631 \u0628\u0631\u0627\u06cc \u0627\u06cc\u0646 \u0644\u0646\u06a9 \u0646\u062f\u0627\u0631\u062f:",
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
