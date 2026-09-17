from pathlib import Path

path = Path(r"C:\Users\alisa\Desktop\Projects\smart-dl\smart_dl\extractors\youtube.py")
text = path.read_text(encoding="utf-8")
old = '''        if mode == "2":
            vid_info = get_yt_formats(vid_url)
            if not vid_info:
                still_skipped.append((idx, vtitle, "Could not fetch info"))
                continue
            fmt, is_audio = yt_quality_menu(vid_info)
            if fmt is None:
                still_skipped.append((idx, vtitle, "Skipped by user"))
                continue
        else:
            fmt, is_audio = shared_fmt, shared_is_audio
        try:
            download_yt(vid_url, out_folder, fmt, is_audio)
        except Exception as e:
            still_skipped.append((idx, vtitle, str(e)[:80]))

    if still_skipped:
        console.print()
        warn(str(len(still_skipped)) + " video(s) still failed after retry.")
        for idx, vtitle, reason in still_skipped:
            info(str(idx) + ". " + vtitle[:55] + " — " + reason[:50])
    else:
        success("All retried videos downloaded successfully.")
        return True
'''
new = '''        if mode == "2":
            vid_info = get_yt_formats(vid_url)
            if not vid_info:
                still_skipped.append((idx, vtitle, "Could not fetch info"))
                continue
            fmt, is_audio = yt_quality_menu(vid_info)
            if fmt is None:
                still_skipped.append((idx, vtitle, "Skipped by user"))
                continue
        else:
            fmt = shared_fmt
            is_audio = shared_is_audio
        try:
            download_yt(vid_url, out_folder, str(fmt), bool(is_audio))
        except Exception as e:
            still_skipped.append((idx, vtitle, str(e)[:80]))

    if still_skipped:
        console.print()
        warn(str(len(still_skipped)) + " video(s) still failed after retry.")
        for idx, vtitle, reason in still_skipped:
            info(str(idx) + ". " + vtitle[:55] + " — " + reason[:50])
        return False
    success("All retried videos downloaded successfully.")
    return True
'''
if old not in text:
    raise SystemExit("pattern not found")
path.write_text(text.replace(old, new), encoding="utf-8")
print("youtube.py updated")
