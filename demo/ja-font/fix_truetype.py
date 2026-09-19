#!/usr/bin/env python3
"""ratex が Type1/FontFile として書き出した TrueType フォントを、正しい TrueType 記述に直す。"""
import sys
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, NumberObject

src, dst = sys.argv[1], sys.argv[2]
TARGET = "/" + (sys.argv[3] if len(sys.argv) > 3 else "IPAexMincho")
w = PdfWriter(clone_from=PdfReader(src))
n = 0
for obj in w._objects:
    o = obj.get_object() if hasattr(obj, "get_object") else obj
    if not hasattr(o, "get"):
        continue
    if o.get("/Type") == "/FontDescriptor" and "/FontFile" in o and o.get("/FontName") == TARGET:
        o[NameObject("/FontFile2")] = o.pop("/FontFile")
        o[NameObject("/Flags")] = NumberObject(32)  # nonsymbolic: /Differences の uniXXXX 名を使わせる
        n += 1
    elif o.get("/Type") == "/Font" and o.get("/Subtype") == "/Type1" and "/FontDescriptor" in o:
        d = o["/FontDescriptor"].get_object()
        if d.get("/FontName") == TARGET:
            o[NameObject("/Subtype")] = NameObject("/TrueType")
w.write(dst)
print("descriptors fixed:", n)
