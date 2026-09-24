#!/usr/bin/env python3
"""同じ日本語文書 (3ページ) を ratex / Typst / 通常の TeX でビルドし、所要時間を比較する。

シナリオ
  clean : 補助ファイルやキャッシュを消した状態からのビルド
  edit  : ビルド済みの状態で本文を 1 文字 (日付の数字) 書き換えて再ビルド
"""
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
RATEX = ROOT / "src/target/release/ratex"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 10
WORK = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/ratex-bench")

DATE_TOKEN = "9月19日"


def run(cmd, cwd, check=True):
    r = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if check and r.returncode != 0:
        print(r.stdout[-2000:])
        raise SystemExit(f"failed: {cmd}")
    return r


def timed(cmd, cwd):
    t = time.perf_counter()
    run(cmd, cwd)
    return time.perf_counter() - t


def edit(path, i):
    """日付の日を 10..19 で巡回させて、内容を実際に変える"""
    s = path.read_text()
    import re
    s = re.sub(r"9月\d+日", f"9月{10 + i % 10}日", s)
    path.write_text(s)


class Tool:
    name = ""
    files = []           # 作業ディレクトリへコピーするもの
    source = ""          # 編集対象
    def prepare(self, d): ...
    def clean(self, d): ...
    def build(self, d): ...


class Typst(Tool):
    name = "Typst"
    source = "long.typ"
    def clean(self, d): pass  # Typst は永続キャッシュを持たない (フォント検索のみ)
    def build(self, d):
        return timed(["typst", "compile", "--font-path", ".", "long.typ", "out.pdf"], d)


class Ratex(Tool):
    """ratex 本体 + フォント後処理。sub=True なら、使う文字だけの TTF を渡す"""
    source = "long.tex"

    def __init__(self, name, sub, n=None):
        self.name, self.sub, self.n = name, sub, n
        self.body = []           # ratex 本体だけの時間
        self.fix = []            # 後処理の時間

    def prepare(self, d):
        if not self.sub:
            return
        from fontTools import subset
        from fontTools.ttLib import TTFont
        chars = sorted({ord(c) for c in (d / "long.tex").read_text() if ord(c) > 0x7F})
        for f in ("ipaexm.ttf", "ipaexg.ttf"):
            o = subset.Options()
            o.layout_features, o.notdef_outline, o.glyph_names, o.hinting, o.name_IDs = [], True, False, False, ["*"]
            font = TTFont(d / f)
            ss = subset.Subsetter(o)
            ss.populate(unicodes=chars)
            ss.subset(font)
            font.save(d / f)

    def clean(self, d):
        # 文書ごとのキャッシュ (jobs) だけを消す。全体は消さない
        shutil.rmtree(Path.home() / "Library/Caches/tex-rs/texmk/jobs", ignore_errors=True)
        (d / "long.pdf").unlink(missing_ok=True)

    def build(self, d):
        b = timed([str(RATEX), "long.tex"], d)
        f = timed([sys.executable, "fix_cjk.py", "long.pdf", "long_final.pdf",
                   "ipaexm.ttf:IPAexMincho", "ipaexg.ttf:IPAexGothic"], d)
        self.body.append(b); self.fix.append(f)
        return b + f


class RatexNative(Tool):
    """ratex v0.4 系。後処理なしで、そのままビルドする"""

    def __init__(self, name, source):
        self.name, self.source = name, source

    def clean(self, d):
        shutil.rmtree(Path.home() / "Library/Caches/tex-rs/texmk/jobs", ignore_errors=True)
        (d / Path(self.source).with_suffix(".pdf")).unlink(missing_ok=True)

    def build(self, d):
        return timed([str(RATEX), self.source], d)


class Latexmk(Tool):
    def __init__(self, name, source, args):
        self.name, self.source, self.args = name, source, args
    def clean(self, d):
        run(["latexmk", "-C", self.source], d, check=False)
        for p in d.glob("*.aux"):
            p.unlink()
    def build(self, d):
        return timed(["latexmk", *self.args, "-interaction=nonstopmode", "-halt-on-error", self.source], d)


def stats(xs):
    return {"median": statistics.median(xs), "min": min(xs), "max": max(xs), "n": len(xs)}


def main():
    ver = run([str(RATEX), "--version"], HERE).stdout.split()[1]  # "ratex 0.4.4 (Rust TeX engine)"
    ratex_files = ["../ja-font/long.tex", "../ja-font/fix_cjk.py", "../ja-font/ipaexm.ttf", "../ja-font/ipaexg.ttf",
                 "../ja-font/udmj.map", "../ja-font/udgj.map"] + [str(p) for p in (ROOT / "demo/ja-font").glob("ud*.enc")]
    tools = [
        (RatexNative(f"ratex v{ver} (CJKutf8)", "long_cjkutf8.tex"), ["../ratex-v040/long_cjkutf8.tex"]),
        (RatexNative(f"ratex v{ver} (xeCJK)", "long_xecjk_harano.tex"), ["../ratex-v040/long_xecjk_harano.tex"]),
        (Typst(), ["long.typ", "../ja-font/ipaexm.ttf", "../ja-font/ipaexg.ttf"]),
        (Latexmk("LuaLaTeX (luatexja)", "lua.tex", ["-lualatex"]), ["lua.tex", "body.tex"]),
        (Latexmk("XeLaTeX (xeCJK)", "xe.tex", ["-xelatex"]), ["xe.tex", "body.tex"]),
        (Latexmk("upLaTeX + dvipdfmx", "up.tex", ["-pdfdvi", "-latex=uplatex", "-e", "$dvipdf=q/dvipdfmx %O -o %D %S/"]), ["up.tex", "body.tex"]),
    ]
    shutil.rmtree(WORK, ignore_errors=True)
    # 別バージョンの ratex の測定値 (v0.3.0 の後処理つきなど) は、古いバイナリがないので既存の JSON から引き継ぐ
    old = HERE / "bench_result.json"
    keep = lambda k: k.startswith("ratex + 後処理") or (k.startswith("ratex v") and not k.startswith(f"ratex v{ver} "))
    results = {k: v for k, v in json.loads(old.read_text()).items() if keep(k)} if old.exists() else {}
    for tool, files in tools:
        d = WORK / tool.name.replace(" ", "_").replace("/", "_")
        d.mkdir(parents=True, exist_ok=True)
        for f in files:
            src = (HERE / f).resolve()
            shutil.copy(src, d / src.name)
        tool.prepare(d)
        n = getattr(tool, "n", None) or N
        edit_target = d / tool.source

        tool.clean(d); tool.build(d)  # ウォームアップ
        if isinstance(tool, Ratex):
            tool.body.clear(); tool.fix.clear()
        clean, edit_t = [], []
        for i in range(n):
            tool.clean(d)
            clean.append(tool.build(d))
        nb = len(tool.body) if isinstance(tool, Ratex) else 0
        for i in range(n):
            edit(edit_target, i)
            edit_t.append(tool.build(d))
        r = results[tool.name] = {"clean": stats(clean), "edit": stats(edit_t)}
        if isinstance(tool, Ratex):
            r["clean"]["body_median"] = statistics.median(tool.body[:nb])
            r["edit"]["body_median"] = statistics.median(tool.body[nb:])
        print(f"{tool.name:34s} clean {r['clean']['median']*1000:8.0f} ms   edit {r['edit']['median']*1000:8.0f} ms   (n={n})", flush=True)

    (HERE / "bench_result.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))


main()
