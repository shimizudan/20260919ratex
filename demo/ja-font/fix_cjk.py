#!/usr/bin/env python3
"""ratex が出力した「TrueType を Type1 として書いた」日本語フォントを、
Type0 / CIDFontType2 (Identity-H) に作り直し、使用文字だけにサブセット化する。

usage: fix_cjk.py in.pdf out.pdf font.ttf:BaseFontName [font.ttf:BaseFontName ...]
"""
import io
import sys

import fitz  # PyMuPDF: 不要オブジェクトの掃除に使う
from fontTools import subset
from fontTools.ttLib import TTFont
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (ArrayObject, ByteStringObject, ContentStream, DecodedStreamObject,
                           DictionaryObject, NameObject, NumberObject, TextStringObject)

src, dst = sys.argv[1:3]
specs = [a.rsplit(":", 1) for a in sys.argv[3:]]  # [(ttf_path, BaseFont), ...]

w = PdfWriter(clone_from=PdfReader(src))


def code_to_unicode(font):
    """/Differences [ 229 /uni65E5 ... ] -> {229: 0x65E5}"""
    m, code = {}, 0
    for item in font.get("/Encoding", {}).get_object().get("/Differences", []):
        item = item.get_object() if hasattr(item, "get_object") else item
        if isinstance(item, (int, NumberObject)):
            code = int(item)
        else:
            if str(item).startswith("/uni"):
                m[code] = int(str(item)[4:], 16)
            code += 1
    return m


def raw(s):
    return bytes(s) if isinstance(s, ByteStringObject) else s.get_original_bytes()


class Target:
    """1 つの実フォント (例: IPAexMincho) に対応する変換情報"""

    def __init__(self, ttf_path, base):
        self.ttf_path, self.base = ttf_path, "/" + base
        self.fonts = {}      # サブフォントの object id -> {code: unicode}
        self.used = set()
        self.gid_of = {}
        self.type0ref = None


targets = [Target(*sp) for sp in specs]
by_objid = {}
for page in w.pages:
    for ref in page["/Resources"].get("/Font", {}).values():
        f = ref.get_object()
        for t in targets:
            if f.get("/Subtype") in ("/Type1", "/TrueType") and f.get("/BaseFont") == t.base:
                t.fonts[ref.idnum] = code_to_unicode(f)
                by_objid[ref.idnum] = t


# 1. 使用文字を集める (フォントリソース名 -> サブフォントの対応表)
for page in w.pages:
    fonts = page["/Resources"]["/Font"]
    cs = ContentStream(page.get_contents(), w)
    cur_map, cur_t = None, None
    for operands, op in cs.operations:
        if op == b"Tf":
            ref = fonts.get(operands[0])
            cur_t = by_objid.get(getattr(ref, "idnum", None))
            cur_map = cur_t.fonts[ref.idnum] if cur_t else None
        elif cur_t is not None and op in (b"Tj", b"TJ"):
            strs = [operands[0]] if op == b"Tj" else [x for x in operands[0] if isinstance(x, (ByteStringObject, TextStringObject))]
            for s in strs:
                cur_t.used.update(cur_map[c] for c in raw(s) if c in cur_map)

# 2. フォントごとにサブセット化して Type0 フォントを作る
for t in targets:
    opts = subset.Options()
    opts.layout_features, opts.notdef_outline, opts.glyph_names, opts.name_IDs, opts.hinting = [], True, False, [], False
    font = TTFont(t.ttf_path)
    ss = subset.Subsetter(opts)
    ss.populate(unicodes=sorted(t.used))
    ss.subset(font)
    buf = io.BytesIO()
    font.save(buf)
    data = buf.getvalue()
    font = TTFont(io.BytesIO(data))
    order = font.getGlyphOrder()
    t.gid_of = {u: order.index(g) for u, g in font.getBestCmap().items()}
    hmtx, head, hhea = font["hmtx"], font["head"], font["hhea"]
    k = 1000 / head.unitsPerEm

    ff = DecodedStreamObject()
    ff.set_data(data)
    ff[NameObject("/Length1")] = NumberObject(len(data))
    desc = w._add_object(DictionaryObject({
        NameObject("/Type"): NameObject("/FontDescriptor"),
        NameObject("/FontName"): NameObject(t.base),
        NameObject("/Flags"): NumberObject(4),
        NameObject("/FontBBox"): ArrayObject(NumberObject(int(v * k)) for v in (head.xMin, head.yMin, head.xMax, head.yMax)),
        NameObject("/ItalicAngle"): NumberObject(0),
        NameObject("/Ascent"): NumberObject(int(hhea.ascent * k)),
        NameObject("/Descent"): NumberObject(int(hhea.descent * k)),
        NameObject("/CapHeight"): NumberObject(int(hhea.ascent * k)),
        NameObject("/StemV"): NumberObject(80),
        NameObject("/FontFile2"): w._add_object(ff),
    }))
    warr = ArrayObject()
    for u, gid in sorted(t.gid_of.items(), key=lambda kv: kv[1]):
        warr += [NumberObject(gid), ArrayObject([NumberObject(round(hmtx[order[gid]][0] * k))])]
    cid = w._add_object(DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/CIDFontType2"),
        NameObject("/BaseFont"): NameObject(t.base),
        NameObject("/CIDSystemInfo"): DictionaryObject({
            NameObject("/Registry"): TextStringObject("Adobe"),
            NameObject("/Ordering"): TextStringObject("Identity"),
            NameObject("/Supplement"): NumberObject(0)}),
        NameObject("/FontDescriptor"): desc,
        NameObject("/CIDToGIDMap"): NameObject("/Identity"),
        NameObject("/DW"): NumberObject(1000),
        NameObject("/W"): warr,
    }))
    bf = "\n".join(f"<{gid:04X}> <{u:04X}>" for u, gid in sorted(t.gid_of.items(), key=lambda kv: kv[1]))
    tu = DecodedStreamObject()
    tu.set_data((
        "/CIDInit /ProcSet findresource begin 12 dict begin begincmap\n"
        "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n"
        "/CMapName /Adobe-Identity-UCS def /CMapType 2 def\n"
        "1 begincodespacerange <0000> <FFFF> endcodespacerange\n"
        f"{len(t.gid_of)} beginbfchar\n{bf}\nendbfchar\n"
        "endcmap CMapName currentdict /CMap defineresource pop end end\n").encode())
    t.type0ref = w._add_object(DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type0"),
        NameObject("/BaseFont"): NameObject(t.base),
        NameObject("/Encoding"): NameObject("/Identity-H"),
        NameObject("/DescendantFonts"): ArrayObject([cid]),
        NameObject("/ToUnicode"): w._add_object(tu),
    }))
    print(f"{t.base}: {len(t.used)} chars, subset {len(data)} bytes")

# 3. 文字列を 2 バイトのグリフ番号へ書き換え、フォントリソースを差し替える
for page in w.pages:
    fonts = page["/Resources"]["/Font"]
    cs = ContentStream(page.get_contents(), w)
    cur_map, cur_t = None, None
    for operands, op in cs.operations:
        if op == b"Tf":
            ref = fonts.get(operands[0])
            cur_t = by_objid.get(getattr(ref, "idnum", None))
            cur_map = cur_t.fonts[ref.idnum] if cur_t else None
            continue
        if cur_t is None or op not in (b"Tj", b"TJ"):
            continue
        conv = lambda s: ByteStringObject(b"".join(cur_t.gid_of[cur_map[c]].to_bytes(2, "big") for c in raw(s)))
        if op == b"Tj":
            operands[0] = conv(operands[0])
        else:
            arr = operands[0]
            for i, x in enumerate(arr):
                if isinstance(x, (ByteStringObject, TextStringObject)):
                    arr[i] = conv(x)
    page.replace_contents(cs)
    for rname, ref in list(fonts.items()):
        t = by_objid.get(getattr(ref, "idnum", None))
        if t:
            fonts[rname] = t.type0ref

# 4. 書き出し後、元の巨大な TTF など未参照オブジェクトを掃除する
tmp = io.BytesIO()
w.write(tmp)
doc = fitz.open(stream=tmp.getvalue(), filetype="pdf")
doc.save(dst, garbage=4, deflate=True, clean=True)
print("saved", dst)
