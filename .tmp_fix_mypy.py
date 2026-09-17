from pathlib import Path

root = Path(r"C:\Users\alisa\Desktop\Projects\smart-dl\smart_dl")
old = """try:
    from smart_dl.lang import t
except ImportError:
    def t(key, **kw):
        return key
"""
new = """try:
    from smart_dl.lang import t
except ImportError:

    def t(key: str, **kwargs: object) -> str:
        return key
"""
old2 = """try:
    from smart_dl.lang import t
except ImportError:
    def t(key: str, **kw) -> str:
        return key
"""
changed = []
for path in root.rglob("*.py"):
    text = path.read_text(encoding="utf-8")
    orig = text
    if old in text:
        text = text.replace(old, new)
    if old2 in text:
        text = text.replace(old2, new)
    if text != orig:
        path.write_text(text, encoding="utf-8")
        changed.append(str(path.relative_to(root)))
print("updated", len(changed))
for c in changed:
    print(c)
