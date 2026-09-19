#!/usr/bin/env python3
"""tex ファイルに登場する文字だけを残した TTF を作る。ratex は TTF 全体を読むと極端に遅くなる。

usage: subset_fonts.py doc.tex outdir font.ttf [font.ttf ...]
"""
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

tex, outdir, *fonts = sys.argv[1:]
chars = sorted({ord(c) for c in Path(tex).read_text() if ord(c) > 0x7F})
for f in fonts:
    o = subset.Options()
    o.layout_features, o.notdef_outline, o.glyph_names, o.hinting, o.name_IDs = [], True, False, False, ["*"]
    font = TTFont(f)
    ss = subset.Subsetter(o)
    ss.populate(unicodes=chars)
    ss.subset(font)
    font.save(Path(outdir) / Path(f).name)
print(f"{len(chars)} chars -> {outdir}")
