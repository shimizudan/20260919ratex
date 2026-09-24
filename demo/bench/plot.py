#!/usr/bin/env python3
"""bench_result.json から比較グラフ (PNG) を作る。usage: plot.py out.png"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent
res = json.loads((HERE / "bench_result.json").read_text())

# 色はエンティティ (ratex / Typst / 通常の TeX) に固定
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e0"
group = lambda k: BLUE if k.startswith("ratex") else ORANGE if k == "Typst" else AQUA
label = {
    "ratex + 後処理 (IPAex全体)": "ratex v0.3.0 + 後処理\n(TTF 全体)",
    "ratex + 後処理 (TTFを事前サブセット)": "ratex v0.3.0 + 後処理\n(TTF をサブセット化)",
    "ratex v0.4.0 (CJKutf8)": "ratex v0.4.0\n(CJKutf8)",
    "ratex v0.4.0 (xeCJK)": "ratex v0.4.0\n(xeCJK)",
    "ratex v0.4.4 (CJKutf8)": "ratex v0.4.4\n(CJKutf8)",
    "ratex v0.4.4 (xeCJK)": "ratex v0.4.4\n(xeCJK)",
    "Typst": "Typst",
    "LuaLaTeX (luatexja)": "LuaLaTeX\n(luatexja)",
    "XeLaTeX (xeCJK)": "XeLaTeX\n(xeCJK)",
    "upLaTeX + dvipdfmx": "upLaTeX\n+ dvipdfmx",
}
names = sorted(res, key=lambda k: res[k]["clean"]["median"])

plt.rcParams["font.family"] = [f.name for f in font_manager.fontManager.ttflist if f.name == "Hiragino Sans"][:1] or ["sans-serif"]
fig, axes = plt.subplots(1, 2, figsize=(10, 4.6), sharey=True, facecolor="#fcfcfb")
for ax, (scn, title) in zip(axes, [("clean", "クリーンビルド"), ("edit", "1 文字編集後の再ビルド")]):
    ax.set_facecolor("#fcfcfb")
    ys = range(len(names))[::-1]
    vals = [res[k][scn]["median"] for k in names]
    ax.barh(list(ys), vals, height=0.55, color=[group(k) for k in names], zorder=3)
    for y, v in zip(ys, vals):
        ax.text(v + 0.25, y, f"{v:.2f} 秒", va="center", ha="left", fontsize=10, color=INK)
    ax.set_title(title, loc="left", fontsize=12, color=INK, pad=10)
    ax.set_xlim(0, 20 if scn == "clean" else 7.5)
    ax.xaxis.grid(True, color=GRID, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, length=0, labelsize=9)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.set_yticks(list(ys))
    ax.set_yticklabels([label[k] for k in names], fontsize=10, color=INK)
    ax.set_xlabel("秒（中央値・短いほど速い）", color=MUTED, fontsize=9)
fig.legend(handles=[Patch(color=BLUE, label="ratex"), Patch(color=ORANGE, label="Typst"), Patch(color=AQUA, label="通常の TeX")],
           loc="lower center", ncol=3, frameon=False, fontsize=10, labelcolor=INK, bbox_to_anchor=(0.5, -0.01))
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig(sys.argv[1], dpi=200, facecolor=fig.get_facecolor())
