from pathlib import Path
import re

root = Path(r"C:\Users\alisa\Desktop\Projects\smart-dl\smart_dl")
targets = [
    "extractors/torrent.py",
    "extractors/subtitles.py",
    "extractors/youtube.py",
    "extractors/gallery.py",
    "extractors/aparat.py",
    "extractors/general.py",
    "core/manager.py",
]
for rel in targets:
    path = root / rel
    text = path.read_text(encoding="utf-8")
    if re.search(r"\*\*kwargs: Any", text) and not re.search(r"from typing import[^\n]*\bAny\b", text):
        if "from typing import" in text:
            text = re.sub(
                r"from typing import ([^\n]+)",
                lambda m: m.group(0) if "Any" in m.group(1) else f"from typing import Any, {m.group(1)}",
                text,
                count=1,
            )
        elif "from __future__ import annotations\n" in text:
            text = text.replace(
                "from __future__ import annotations\n",
                "from __future__ import annotations\n\nfrom typing import Any\n",
                1,
            )
        else:
            lines = text.splitlines(True)
            insert_at = 0
            if lines and lines[0].startswith('"""'):
                # end of docstring
                if lines[0].count('"""') >= 2:
                    insert_at = 1
                else:
                    for i in range(1, len(lines)):
                        if '"""' in lines[i]:
                            insert_at = i + 1
                            break
            lines.insert(insert_at, "\nfrom typing import Any\n")
            text = "".join(lines)
        path.write_text(text, encoding="utf-8")
        print("Any import", rel)

# youtube return + assignment
yt = root / "extractors/youtube.py"
text = yt.read_text(encoding="utf-8")
if "fmt = shared_fmt" not in text:
    text = text.replace(
        "            fmt, is_audio = shared_fmt, shared_is_audio\n",
        "            fmt = shared_fmt\n            is_audio = shared_is_audio\n",
    )
text = text.replace(
    "            download_yt(vid_url, out_folder, fmt, is_audio)\n",
    "            download_yt(vid_url, out_folder, str(fmt), bool(is_audio))\n",
)
# missing return at end of function that logs still_failed
old_tail = """    if still_skipped:
        console.print()
        warn(str(len(still_skipped)) + " video(s) still failed after retry.")
        for idx, vtitle, reason in still_skipped:
            info(str(idx) + ". " + vtitle[:55] + " — " + reason[:50])
    else:
        success("All retried videos downloaded successfully.")
        return True
"""
new_tail = """    if still_skipped:
        console.print()
        warn(str(len(still_skipped)) + " video(s) still failed after retry.")
        for idx, vtitle, reason in still_skipped:
            info(str(idx) + ". " + vtitle[:55] + " — " + reason[:50])
        return False
    success("All retried videos downloaded successfully.")
    return True
"""
if old_tail in text:
    text = text.replace(old_tail, new_tail)
    print("youtube tail fixed")
else:
    # try unicode emdash form
    old_tail2 = old_tail.replace("—", "—")
    new_tail2 = new_tail.replace("—", "—")
    if old_tail2 in text:
        text = text.replace(old_tail2, new_tail2)
        print("youtube tail fixed (unicode)")
    else:
        print("youtube tail NOT found")
        # show nearby
        idx = text.find("still failed after retry")
        print(repr(text[idx-80:idx+200]))
yt.write_text(text, encoding="utf-8")

# proxy
px = root / "core/proxy.py"
pt = px.read_text(encoding="utf-8")
pt = pt.replace("    reg = _peek_registry_proxy()\n    return reg\n", "    reg = _peek_registry_proxy()\n    return str(reg or \"\")\n")
px.write_text(pt, encoding="utf-8")
print("proxy return cast")
