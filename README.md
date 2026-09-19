# ratex で日本語 PDF を作る

Rust 製の TeX エンジン [ratex](https://github.com/leoliu0/ratex)（v0.3.0）で日本語を含む PDF を生成する検証と、
Typst・通常の TeX とのビルド時間の比較です（2026-09-19 時点、macOS）。

## 結論

- ratex は英語と数式なら、そのままで動く。
- **日本語は、そのままでは文字化けする。** 日本語フォントの字形（TTF など）がバンドルに入っておらず、PDF に埋め込まれない。
- 次の 3 つの対処で、pdf.js（VSCode）、macOS プレビュー、poppler で日本語が表示できた。
  1. IPAex フォントを 256 文字ずつのサブフォントに分けて、ratex に渡す（[gen_subfonts.py](demo/ja-font/gen_subfonts.py)）。
  2. ratex は TrueType を Type1 として書き出してしまうため、出力 PDF のフォントを Type0/CID に作り直し、使用文字だけにサブセット化する（[fix_cjk.py](demo/ja-font/fix_cjk.py)）。
  3. ratex は TTF 全体を読むと極端に遅くなるので、事前に使用文字だけの TTF にする（[subset_fonts.py](demo/ja-font/subset_fonts.py)）。

## ビルド時間の比較

同じ 3 ページの日本語文書（見出し・数式・表・箇条書き）を、同じ IPAex フォントでビルドした中央値です。

| 構成 | クリーンビルド | 1 文字編集後の再ビルド |
|---|---|---|
| Typst | 0.18 秒 | 0.18 秒 |
| upLaTeX + dvipdfmx | 1.6 秒 | 1.0 秒 |
| ratex + 後処理（TTF を事前サブセット） | 1.4 秒 | 0.8 秒 |
| XeLaTeX（xeCJK） | 2.3 秒 | 1.2 秒 |
| LuaLaTeX（luatexja） | 6.4 秒 | 2.2 秒 |
| ratex + 後処理（IPAex 全体の TTF） | 16.3 秒 | 6.0 秒 |

- 各 10 回（IPAex 全体の ratex のみ 3 回）。生データは [bench_result.json](demo/bench/bench_result.json)。
- Typst は英数字にも IPAex を使う。TeX 系は Computer Modern を使うため、組版の細部は同じではない。
- ratex は、フォントのサブセット化（前処理）を測定に含めていない。

## 構成

```
demo/
  hello.tex          英語 + 数式（ratex でそのまま動く）
  ja.tex             日本語の最小例（CJKutf8 のみ。文字化けする例）
  lang/              中国語・フランス語など他言語の試行
  fonttest/          Latin Modern の .pfb を置くと埋め込まれることの確認
  ja-font/           日本語対応（本体）
    setup.sh           IPAex の取得と、サブフォント用 enc / map の生成
    build.sh           ratex でビルド → PDF のフォントを作り直す
    gen_subfonts.py    TTF -> 256 文字ごとの enc / map
    subset_fonts.py    文書に使う文字だけの TTF を作る
    fix_cjk.py         PDF のフォントを Type0/CID + サブセットに作り直す
    fix_truetype.py    途中版（TrueType に直すだけ。pdf.js では漢字が出ない）
    long.tex           サンプルの長文（3 ページ）
    long_final.pdf     生成結果
  bench/             ビルド時間の比較（Typst / LuaLaTeX / XeLaTeX / upLaTeX）
```

## 再現手順

### 1. ratex をビルドする

Rust 1.89 以上が必要です。

```sh
git clone --depth 1 https://github.com/leoliu0/ratex.git src
(cd src && cargo build --release)      # 約 7 分
```

### 2. 日本語 PDF を作る

```sh
pip install -r requirements.txt
cd demo/ja-font
./setup.sh                             # IPAex の取得と enc / map の生成
./build.sh                             # -> build/long_final.pdf
```

自分の文書を使う場合は、`\usepackage{CJKutf8}` と `\pdfmapfile{+udmj.map}`（ゴシックは `+udgj.map`）を追加して、
`./build.sh mydoc.tex` を実行します（[long.tex](demo/ja-font/long.tex) を参照）。

### 3. ビルド時間を比べる

MacTeX、Typst、上の手順が必要です。

```sh
cd demo/bench
python3 bench.py 10
```

## 制限

- 検証は ratex v0.3.0、macOS のみ。
- 禁則処理や約物の詰めは `CJK` パッケージの範囲に限られる。
- 幅の情報は和田研フォント用の TFM を使うため、そこにない文字は出ないことがある。
- 太字の日本語は未確認。

## ライセンス・フォント

- IPAex フォントは [IPA フォントライセンス](https://moji.or.jp/ipafont/license/) です。このリポジトリには含めず、`setup.sh` で取得します。
- このリポジトリのスクリプトは MIT ライセンスです（[LICENSE](LICENSE)）。
- ratex は MIT または Apache-2.0 です。
