#!/usr/bin/env python3
"""IPAex 明朝 (TTF) から CJK パッケージの udmjXX サブフォント用 enc / map を生成する。"""
import sys
from fontTools.ttLib import TTFont

ttf, prefix, psname = sys.argv[1], sys.argv[2], sys.argv[3]  # ipaexm.ttf udmj IPAexMincho
cmap = TTFont(ttf).getBestCmap()
pages = sorted({cp >> 8 for cp in cmap if cp >= 0x80})
with open(f"{prefix}.map", "w") as m:
    for p in pages:
        name = f"{prefix}{p:02x}"
        names = [f"/uni{p << 8 | i:04X}" if (p << 8 | i) in cmap else "/.notdef" for i in range(256)]
        with open(f"{name}.enc", "w") as e:
            e.write(f"/{name}Enc [\n" + "\n".join(names) + "\n] def\n")
        m.write(f"{name} {psname} <{name}.enc <{ttf}\n")
print(f"{len(pages)} subfonts")
