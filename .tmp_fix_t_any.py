from pathlib import Path

root = Path(r"C:\Users\alisa\Desktop\Projects\smart-dl\smart_dl")
old = """    def t(key: str, **kwargs: object) -> str:
        return key
"""
new = """    def t(key: str, **kwargs: Any) -> str:
        return key
"""
# ensure Any is imported when we rewrite
for path in root.rglob("*.py"):
    text = path.read_text(encoding="utf-8")
    if old not in text:
        continue
    text = text.replace(old, new)
    if "from typing import Any" not in text and "from typing import" in text:
        # extend existing typing import
        import re
        text = re.sub(
            r"from typing import ([^\n]+)",
            lambda m: f"from typing import {m.group(1)}" if "Any" in m.group(1) else f"from typing import Any, {m.group(1)}",
            text,
            count=1,
        )
    elif "from typing import Any" not in text:
        # insert after future import or module docstring
        if "from __future__ import annotations\n" in text:
            text = text.replace(
                "from __future__ import annotations\n",
                "from __future__ import annotations\n\nfrom typing import Any\n",
                1,
            )
        else:
            # after first docstring end rough
            text = text.replace("from smart_dl.lang import t", "from smart_dl.lang import t", 1)
    path.write_text(text, encoding="utf-8")
    print("fixed", path.relative_to(root))

# special: always ensure lang fallback files import Any when fallback present
for path in root.rglob("*.py"):
    text = path.read_text(encoding="utf-8")
    if "def t(key: str, **kwargs: Any)" not in text:
        continue
    if "from typing import" not in text:
        if "from __future__ import annotations\n" in text:
            text = text.replace(
                "from __future__ import annotations\n",
                "from __future__ import annotations\n\nfrom typing import Any\n",
                1,
            )
            path.write_text(text, encoding="utf-8")
            print("import Any", path.relative_to(root))
    else:
        # ensure Any in typing import
        import re
        m = re.search(r"from typing import ([^\n]+)", text)
        if m and "Any" not in m.group(1):
            text = text.replace(m.group(0), f"from typing import Any, {m.group(1)}", 1)
            path.write_text(text, encoding="utf-8")
            print("typing Any", path.relative_to(root))
