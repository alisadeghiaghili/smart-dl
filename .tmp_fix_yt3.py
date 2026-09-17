from pathlib import Path

path = Path(r"C:\Users\alisa\Desktop\Projects\smart-dl\smart_dl\extractors\youtube.py")
text = path.read_text(encoding="utf-8")
old = """        else:
            fmt, is_audio = shared_fmt, shared_is_audio
        try:
            download_yt(vid_url, out_folder, fmt, is_audio)
        except Exception as e:
            still_skipped.append((idx, vtitle, str(e)[:80]))

    if still_skipped:
        console.print()
        warn(str(len(still_skipped)) + " video(s) still failed after retry.")
        for idx, vtitle, reason in still_skipped:
            info(str(idx) + ". " + vtitle[:55] + " \\u2014 " + reason[:50])
    else:
        success("All retried videos downloaded successfully.")
        return True
"""
# file may store em dash as real char
old2 = old.replace("\\u2014", "—")
new = """        else:
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
"""
new2 = new.replace("—", "—")
# also handle when info line uses unicode escape in source literally
if old in text:
    text = text.replace(old, new.replace("—", "\\u2014"))
    print("replaced with escaped form")
elif old2 in text:
    text = text.replace(old2, new2)
    print("replaced with unicode form")
else:
    # line based
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "fmt, is_audio = shared_fmt, shared_is_audio" in line:
            lines[i] = "            fmt = shared_fmt"
            lines.insert(i + 1, "            is_audio = shared_is_audio")
            print("split assignment at", i)
            break
    text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    if "download_yt(vid_url, out_folder, fmt, is_audio)" in text:
        text = text.replace(
            "download_yt(vid_url, out_folder, fmt, is_audio)",
            "download_yt(vid_url, out_folder, str(fmt), bool(is_audio))",
        )
        print("fixed download_yt call")
    # fix missing return
    marker = "success(\"All retried videos downloaded successfully.\")"
    if "return False" not in text[text.find("still failed after retry"):text.find(marker)+80]:
        text = text.replace(
            "            info(str(idx) + \". \" + vtitle[:55] + \" \\u2014 \" + reason[:50])\n    else:\n        success(\"All retried videos downloaded successfully.\")\n        return True",
            "            info(str(idx) + \". \" + vtitle[:55] + \" \\u2014 \" + reason[:50])\n        return False\n    success(\"All retried videos downloaded successfully.\")\n    return True",
        )
        print("fixed return path")

path.write_text(text, encoding="utf-8")
# verify
t2 = path.read_text(encoding="utf-8")
print("shared_fmt line ok", "fmt = shared_fmt" in t2)
print("return False after still", "return False" in t2[t2.find("still failed"):t2.find("All retried")+120])
print("def download alias", "download_single as download_yt" in t2)
print("lines", len(t2.splitlines()))
