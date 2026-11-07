"""Join od.py (Part A, Brandon) and arm.py (Part B, Alex) into robotics.ipynb.

Usage: python robotics/build_notebook.py
Cells are split by '# %%' / '# %% [markdown]'; markdown lines start with '# '. Missing parts are skipped.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
PARTS = ["intro.py", "od.py", "arm.py"]
cells = []


def parse(lines):
    out, kind, buf = [], None, []

    def flush():
        if kind is None:
            return
        body = list(buf)
        while body and not body[-1].strip():
            body.pop()
        while body and not body[0].strip():
            body.pop(0)
        if kind == "markdown":
            body = [l[2:] if l.startswith("# ") else l.lstrip("#") for l in body]
            out.append({"cell_type": "markdown", "metadata": {}, "source": "\n".join(body)})
        else:
            out.append({"cell_type": "code", "metadata": {}, "execution_count": None,
                        "outputs": [], "source": "\n".join(body)})

    for line in lines:
        if line.startswith("# %%"):
            flush()
            kind, buf = ("markdown" if "[markdown]" in line else "code"), []
        else:
            buf.append(line)
    flush()
    return out


for part in PARTS:
    p = HERE / part
    if p.exists():
        cells += parse(p.read_text().splitlines())
    else:
        print(f"skipping missing {part}")

nb = {"cells": cells, "metadata": {
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
    "language_info": {"name": "python"}, "colab": {"provenance": []}},
    "nbformat": 4, "nbformat_minor": 5}
(HERE / "robotics.ipynb").write_text(json.dumps(nb, indent=1))
print(f"wrote {len(cells)} cells")
