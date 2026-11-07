"""Turn digital_twin.py (cells split by '# %%' / '# %% [markdown]') into digital_twin.ipynb.

Usage: python digital-twin/build_notebook.py
Markdown cells: every line starts with '# ' (or is '#'), which is stripped.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
src = (HERE / "digital_twin.py").read_text().splitlines()

cells, kind, buf = [], None, []


def flush():
    if kind is None:
        return
    lines = list(buf)
    while lines and not lines[-1].strip():
        lines.pop()
    while lines and not lines[0].strip():
        lines.pop(0)
    if kind == "markdown":
        lines = [l[2:] if l.startswith("# ") else l.lstrip("#") for l in lines]
        cells.append({"cell_type": "markdown", "metadata": {}, "source": "\n".join(lines)})
    else:
        cells.append({"cell_type": "code", "metadata": {}, "execution_count": None,
                      "outputs": [], "source": "\n".join(lines)})


for line in src:
    if line.startswith("# %%"):
        flush()
        kind, buf = ("markdown" if "[markdown]" in line else "code"), []
    else:
        buf.append(line)
flush()

nb = {"cells": cells, "metadata": {
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
    "language_info": {"name": "python"}, "colab": {"provenance": []}},
    "nbformat": 4, "nbformat_minor": 5}
(HERE / "digital_twin.ipynb").write_text(json.dumps(nb, indent=1))
print(f"wrote {len(cells)} cells")
