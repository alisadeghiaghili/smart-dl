from pathlib import Path

yt = Path(r"C:\Users\alisa\Desktop\Projects\smart-dl\smart_dl\extractors\youtube.py")
raw = yt.read_bytes()
print("crlf", b"\r\n" in raw, "lf only", b"\n" in raw)
text = raw.decode("utf-8")
# normalize check
if "fmt, is_audio = shared_fmt, shared_is_audio" in text:
    text = text.replace(
        "fmt, is_audio = shared_fmt, shared_is_audio",
        "fmt = shared_fmt\n            is_audio = shared_is_audio",
    )
if "download_yt(vid_url, out_folder, fmt, is_audio)" in text:
    text = text.replace(
        "download_yt(vid_url, out_folder, fmt, is_audio)",
        "download_yt(vid_url, out_folder, str(fmt), bool(is_audio))",
    )

needle = "info(str(idx) + \". \" + vtitle[:55] + \""
idx = text.find(needle)
print("needle idx", idx)
if idx != -1:
    # find the line and following else/return
    # Replace the if/else block ending
    start = text.rfind("if still_skipped:", 0, idx)
    print("start", start)
    end = text.find("return True", idx)
    print("end", end, repr(text[idx:end+20]))
    # Build replacement carefully using exact slice
    # Find end of "return True\n" after else
    end2 = text.find("return True", idx)
    # get full block
    block = text[start:end2 + len("return True")]
    print("BLOCK START/END")
    print(repr(block[:200]))
    print("...")
    print(repr(block[-200:]))

# Use line-based rewrite
lines = text.splitlines(True)
out = []
i = 0
changed = False
while i < len(lines):
    line = lines[i]
    if line.strip() == "if still_skipped:" and i + 2 < len(lines) and "still failed after retry" in lines[i+2]:
        # capture until return True of else
        j = i
        while j < len(lines) and "return True" not in lines[j]:
            j += 1
        # lines[i:j] is if ... else success, lines[j] is return True
        # rewrite block
        out.append("    if still_skipped:\n")
        out.append("        console.print()\n")
        out.append('        warn(str(len(still_skipped)) + " video(s) still failed after retry.")\n')
        out.append("        for idx, vtitle, reason in still_skipped:\n")
        # keep the info line format from original
        info_line = None
        for k in range(i, j+1):
            if "info(str(idx)" in lines[k]:
                info_line = lines[k]
                break
        if info_line is None:
            info_line = '            info(str(idx) + ". " + vtitle[:55] + " \\u2014 " + reason[:50])\n'
        out.append(info_line)
        out.append("        return False\n")
        out.append('    success("All retried videos downloaded successfully.")\n')
        out.append("    return True\n")
        i = j + 1
        changed = True
        continue
    out.append(line)
    i += 1

new_text = "".join(out)
# also fix handle_playlist missing return - look for def handle_playlist and ensure last return
if "def handle_playlist" in new_text:
    # if function ends without return True/False after success paths - mypy said line 169
    pass

yt.write_text(new_text, encoding="utf-8")
print("changed", changed)

# force handle_playlist return: find function and if missing return at end, append
text = yt.read_text(encoding="utf-8")
import re
m = re.search(r"def handle_playlist\([\s\S]*?\n(?=def |\Z)", text)
if m:
    body = m.group(0)
    if body.rstrip().endswith("return False") or "return True" in body or "return False" in body:
        # ensure all paths return - add return False at end if last statement isn't return
        stripped = body.rstrip() + "\n"
        # if no return as last non-empty line
        last = [ln for ln in stripped.splitlines() if ln.strip()][-1]
        print("handle_playlist last line:", last)
        if not last.strip().startswith("return"):
            text = text.replace(body, stripped + "    return False\n")
            yt.write_text(text, encoding="utf-8")
            print("appended return False to handle_playlist")
