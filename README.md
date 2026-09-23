# ratex で日本語 PDF を作る

Rust 製の TeX エンジン [ratex](https://github.com/leoliu0/ratex) で日本語を含む PDF を生成する検証と、
Typst・通常の TeX とのビルド時間の比較です（macOS）。
v0.3.0 での検証（2026-09-19）と、issue [#4](https://github.com/leoliu0/ratex/issues/4) の対応後の v0.4.0 での再検証（2026-09-21）があります。

## 結論

- ratex は英語と数式なら、そのままで動く。
- **v0.4.0 では、fontspec + xeCJK で日本語 PDF が後処理なしで作れる。** CJK フォントが同梱され、`fontspec` / `xeCJK` が本物のフォントを選ぶようになった（issue #4 の対応）。`\setCJKmainfont{IPAexMincho}` などで指定したフォントが CID TrueType で埋め込まれる。システムフォントも、フォントファイルの用意も不要。3 ページの長文（数式・表・目次・参考文献つき）も約 0.7 秒で、化けなかった（[demo/ratex-v040/](demo/ratex-v040/)）。
- **CJKutf8 は、短い文書なら表示できるが、長文では英字・数字・数式が化ける（v0.4.0 のバグ）。** 日本語の字形は同梱の和田研フォントで正しく出るが、同じフォント（CMR10 など）に、コードの割り当てが食い違う 2 つの版ができ、英字や数字が欠けたり重なったりする。`enumerate` の番号、ページ番号、目次、式番号などが引き金で、文書の書き方では避けられなかった。最小の再現例は [repro_cjkutf8_enum.tex](demo/ratex-v040/repro_cjkutf8_enum.tex)（6 行）。長文で使うなら xeCJK を使う。
- ただし ratex はフォントを代替しない。**要求した太字・斜体がフォントになければエラーになる。** IPAex には Bold がないため、見出しなどで太字を使う文書は IPAex では通らない（Harano Aji なら通る）。日本語への `\textit` もエラーになる。
- **macOS 同梱のヒラギノや、別途インストールした BIZ UD ゴシック/明朝も、実ファイルを直接指定すれば使える。** ratex は fontconfig のようなシステムフォント DB を持たないため、`\setCJKmainfont{ヒラギノ明朝 ProN}` のように名前だけ書いても見つからない。`Path=` / `Extension=` / `FontIndex=` オプションで実際のファイルを指す必要がある（[xecjk_hiragino.tex](demo/ratex-v040/xecjk_hiragino.tex)、[long_xecjk_hiragino.tex](demo/ratex-v040/long_xecjk_hiragino.tex)、[xecjk_bizud.tex](demo/ratex-v040/xecjk_bizud.tex)、[long_xecjk_bizud.tex](demo/ratex-v040/long_xecjk_bizud.tex)）。ヒラギノの標準フォント（ProN）は SIP 保護領域にあり `ls` では見えないため、`fc-list`（Homebrew の fontconfig）でパスを調べた。
- **丸数字（①②③）・ローマ数字（Ⅰ Ⅱ Ⅲ）・丸英字（Ⓐ Ⓑ Ⓒ）は、xeCJK では `\setCJKmainfont` に回らず `\setmainfont` 側で解決される。** ratex の CJK 判定（`is_cjk()`）は Enclosed CJK Letters and Months（㈠㈡㈢ など、U+3200-32FF）は対象に含むが、Enclosed Alphanumerics（①など、U+2460-24FF）と Number Forms（Ⅰなど、U+2150-218F）は対象外にしている。そのためこれらの文字は `\setCJKmainfont` ではなく地の `\setmainfont`（既定では Latin Modern Roman）に回され、そちらにグリフがなければ Missing glyph でビルドが止まる。HaranoAjiMincho・IPAexMincho はどちらもこれらのグリフを持たないため、xeCJK の既定設定では丸数字は使えない（[repro_enclosed_alnum.tex](demo/ratex-v040/repro_enclosed_alnum.tex)）。回避策は、`\setmainfont` にもこれらのグリフを持つフォント（ヒラギノなど）を指定すること。ヒラギノ明朝 ProN 自体にはグリフがあるため、`\setmainfont` と `\setCJKmainfont` の両方に指定すれば和文中に混在させても表示できる（[enclosed_alnum_hiragino.tex](demo/ratex-v040/enclosed_alnum_hiragino.tex)）。
- **絵文字（😀🎉など）は、ビルドはエラーなく成功するが、PDF には何も描画されない。** Apple Color Emoji をフォント指定すると Missing glyph エラーは出ない（コードポイント→グリフ ID の対応は取れている）が、出力 PDF は Poppler・macOS Quick Look のどちらで見ても空白になる（[repro_emoji_blank.tex](demo/ratex-v040/repro_emoji_blank.tex)）。Apple Color Emoji の実体は色ビットマップを持つ `sbix` テーブルにあり、通常の輪郭を持つはずの `glyf` テーブル側は面積ゼロの退化した2点だけのダミー輪郭しか持たない（fontTools で確認）。ratex は `sbix` を読まず `glyf` のダミー輪郭をそのまま埋め込むため、エラーにはならないが見た目には何も残らない。なお色のない記号（☆★○●✓☺♪♥など）は、フォントに実体のある輪郭グリフとして入っていれば通常の文字と同様に表示できる。
- **`BoldFont=` は、1 つの `.ttc` に複数ウェイトが同居していると選べない。** `BoldFont=` に渡した名前も、元の `Path`/`Extension`/`FontIndex` をそのまま引き継ぐため、Regular と Bold が別ファイルのフォント（BIZ UD ゴシックの `BIZ-UDGothicR.ttc` / `BIZ-UDGothicB.ttc` など）なら問題なく効くが、同じファイルの別面に Bold が入っているフォント（ヒラギノ明朝 ProN.ttc は面 0 が Regular、面 2 が Bold）では面を切り替えられない。回避策として、`fontTools` で該当面を単体ファイルに抜き出した（[demo/ratex-v040/hirafonts/](demo/ratex-v040/hirafonts/)）。BIZ UD 明朝のように Bold 自体が存在しないフォントでは、IPAex と同じく和文を `\textbf` に含めるとエラーになる。
- **v0.3.0 では、日本語はそのままでは文字化けした。** 字形が PDF に埋め込まれず、ratex は TrueType を Type1 として書き出していた。次の 3 つの回避策で表示できた（v0.4.0 では不要。[demo/ja-font/](demo/ja-font/) に残してある）。
  1. IPAex フォントを 256 文字ずつのサブフォントに分けて、ratex に渡す（[gen_subfonts.py](demo/ja-font/gen_subfonts.py)）。
  2. 出力 PDF のフォントを Type0/CID に作り直し、使用文字だけにサブセット化する（[fix_cjk.py](demo/ja-font/fix_cjk.py)）。
  3. TTF 全体を読むと極端に遅くなるので、事前に使用文字だけの TTF にする（[subset_fonts.py](demo/ja-font/subset_fonts.py)）。

## ビルド時間の比較

同じ 3 ページの日本語文書（見出し・数式・表・箇条書き）をビルドした中央値です。

| 構成 | クリーンビルド | 1 文字編集後の再ビルド |
|---|---|---|
| Typst | 0.18 秒 | 0.18 秒 |
| **ratex v0.4.0（xeCJK、後処理なし）** | 0.88 秒 | 0.32 秒 |
| ratex v0.4.0（CJKutf8、後処理なし。※英字・数字・数式が化ける） | 1.06 秒 | 0.38 秒 |
| upLaTeX + dvipdfmx | 1.5 秒 | 1.0 秒 |
| XeLaTeX（xeCJK） | 2.3 秒 | 1.2 秒 |
| LuaLaTeX（luatexja） | 6.4 秒 | 2.2 秒 |
| ratex v0.3.0 + 後処理（TTF を事前サブセット） | 1.4 秒 | 0.8 秒 |
| ratex v0.3.0 + 後処理（IPAex 全体の TTF） | 16.3 秒 | 6.0 秒 |

- 各 10 回（v0.3.0 の IPAex 全体のみ 3 回）。生データは [bench_result.json](demo/bench/bench_result.json)。
- v0.4.0 と Typst、TeX 系は 2026-09-21 に同じ環境で測り直した。v0.3.0 の 2 行は、古いバイナリがないため 2026-09-19 の測定値をそのまま載せている。
- フォントは同じではない。Typst と TeX 系は IPAex、ratex v0.4.0 の xeCJK は Harano Aji（IPAex は Bold がなく、見出しで通らないため）、CJKutf8 は同梱の和田研フォント。
- Typst は英数字にも IPAex を使う。TeX 系は Computer Modern を使うため、組版の細部は同じではない。
- v0.3.0 の測定は、フォントのサブセット化（前処理）を含めていない。v0.4.0 は前処理も後処理もない。
- ratex v0.4.0 は、TeX 系の中では最も速い（クリーンで upLaTeX の約 1.4〜1.7 倍、LuaLaTeX の約 6〜7 倍）。Typst には及ばない。

### 参考: ヒラギノ・BIZ UD との比較（簡易計測）

同じ環境・同じ 3 ページの文書で、Harano Aji に加えてヒラギノ（ProN）・BIZ UD でもビルド時間を測った（2026-09-22、各 5 回の中央値）。上の表とは計測条件が異なる簡易チェックなので、別枠で載せる。

| フォント | クリーンビルド | 1 文字編集後の再ビルド |
|---|---|---|
| Harano Aji | 0.99 秒 | 0.35 秒 |
| ヒラギノ（ProN） | 1.10 秒 | 0.44 秒 |
| BIZ UD | 0.86 秒 | 0.36 秒 |

- クリーンビルドは `ratex -c` でキャッシュを消してから計測。再ビルドは末尾にコメント行を 1 行足して内容を変えてから計測。
- 差はおおむねフォントファイルの読み込み時間。ヒラギノの明朝は、fontTools で抜き出した単体 OTF（Regular・Bold 合わせて約 19MB）を読むぶん、他より遅い。

## 構成

```
demo/
  hello.tex          英語 + 数式（ratex でそのまま動く）
  ja.tex             日本語の最小例（CJKutf8 のみ。v0.3.0 では文字化けする例）
  lang/              中国語・フランス語など他言語の試行
  fonttest/          Latin Modern の .pfb を置くと埋め込まれることの確認
  ratex-v040/        v0.4.0 での再検証（後処理なし）
    cjkutf8.tex        日本語の最小例（CJKutf8。短文なら表示できる）
    xecjk.tex          fontspec + xeCJK（IPAexMincho / IPAexGothic）
    xecjk_hiragino.tex   fontspec + xeCJK（システムのヒラギノ ProN。Path/Extension/FontIndex 指定）
    xecjk_bizud.tex      fontspec + xeCJK（システムの BIZ UD ゴシック/明朝）
    long_cjkutf8.tex   長文（3 ページ、CJKutf8。英字・数字・数式が化ける）
    long_xecjk_harano.tex  長文（3 ページ、xeCJK + Harano Aji。化けない）
    long_xecjk_hiragino.tex  長文（3 ページ、ヒラギノ。Bold 面を fontTools で単体ファイルに抜いて使用）
    long_xecjk_bizud.tex     長文（3 ページ、BIZ UD。明朝に Bold がないため見出し表の和文を \textbf の外に出した）
    hirafonts/           ヒラギノ明朝 ProN.ttc の面 0（Regular）・面 2（Bold）を fontTools で単体 OTF に抜いたもの
    repro_cjkutf8_enum.tex  CJKutf8 の化けの最小再現例（6 行）
    repro_enclosed_alnum.tex  丸数字・ローマ数字が xeCJK の CJK 判定に含まれず Missing glyph になる再現例
    enclosed_alnum_hiragino.tex  上の回避策（\setmainfont にもヒラギノを指定）
    repro_emoji_blank.tex  絵文字がエラーなくビルドされるが PDF には描画されない再現例
  ja-font/           v0.3.0 用の回避策（後処理あり）
    setup.sh           IPAex の取得と、サブフォント用 enc / map の生成
    build.sh           ratex でビルド → PDF のフォントを作り直す
    gen_subfonts.py    TTF -> 256 文字ごとの enc / map
    subset_fonts.py    文書に使う文字だけの TTF を作る
    fix_cjk.py         PDF のフォントを Type0/CID + サブセットに作り直す
    fix_truetype.py    途中版（TrueType に直すだけ。pdf.js では漢字が出ない）
    long.tex           サンプルの長文（3 ページ）
    long_final.pdf     生成結果
  bench/             ビルド時間の比較（Typst / LuaLaTeX / XeLaTeX / upLaTeX）と、グラフ作成（plot.py）
```

## 再現手順

### 1. ratex をビルドする

Rust 1.89 以上が必要です。v0.4.0 はフォントを同梱するため、ソースが大きく、ビルドに約 23 分（バイナリ約 445MB）かかりました。

```sh
git clone https://github.com/leoliu0/ratex.git src
(cd src && git checkout v0.4.0 && cargo build --release)
```

### 2. 日本語 PDF を作る（v0.4.0）

```sh
cd demo/ratex-v040
../../src/target/release/ratex xecjk.tex          # fontspec + xeCJK
../../src/target/release/ratex long_xecjk_harano.tex   # 長文（xeCJK）
```

### 2b. システムフォント（ヒラギノ / BIZ UD）で日本語 PDF を作る（v0.4.0）

ratex は fontconfig のようなシステムフォント DB を持たないので、`\setCJKmainfont` に `Path=` / `Extension=` / `FontIndex=` を渡して実ファイルを直接指す（詳しくは上の「結論」参照）。BIZ UD ゴシック（`/Library/Fonts/BIZ-UDGothicR.ttc` など）が入っていれば、そのまま動く。

```sh
cd demo/ratex-v040
../../src/target/release/ratex xecjk_bizud.tex
../../src/target/release/ratex long_xecjk_bizud.tex
```

ヒラギノは、実ファイルが SIP 保護領域にあり `fc-list`（Homebrew の fontconfig）でパスを調べる必要があるのに加え、明朝の Bold が Regular と同じ `.ttc` の別面に入っているため、`fontTools` で面を単体ファイルに抜き出した（[demo/ratex-v040/hirafonts/](demo/ratex-v040/hirafonts/)、リポジトリに同梱済み）。抜き出しをやり直す場合は次のようにする。

```sh
pip install -r requirements.txt
python3 -c "
from fontTools.ttLib import TTCollection
src = TTCollection('/System/Library/Fonts/ヒラギノ明朝 ProN.ttc')
src.fonts[0].save('demo/ratex-v040/hirafonts/HiraMinProN-Regular.otf')  # 面 0 = W3 (Regular)
src.fonts[2].save('demo/ratex-v040/hirafonts/HiraMinProN-Bold.otf')     # 面 2 = W6 (Bold 相当)
"
cd demo/ratex-v040
../../src/target/release/ratex xecjk_hiragino.tex
../../src/target/release/ratex long_xecjk_hiragino.tex
```

### 2'. 日本語 PDF を作る（v0.3.0 用の回避策）

v0.3.0 のバイナリ（`git checkout v0.3.0`）が必要です。

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

## 参考: 別実装の rtex（yingkitw）

名前が似ている [yingkitw/rtex](https://github.com/yingkitw/rtex)（v0.1.11、pdfrs エンジン）も試した。
TeX エンジンではなく、LaTeX のサブセットを解釈して PDF / HTML / DOCX / EPUB に変換するツールで、
Rust 1.90 で約 2 分でビルドできた（`cargo build --release`）。ファイルは [demo/rtex-yingkitw/](demo/rtex-yingkitw/)。

- **日本語は後処理なしで表示できる。** CJKutf8 もフォント指定も不要で、macOS では [ja_min.tex](demo/rtex-yingkitw/ja_min.tex) がそのまま読める PDF になった（CID TrueType を埋め込み）。
- ビルドは同じ 3 ページの文書で 約 0.02 秒（10 回の中央値。クリーン・1 文字編集後とも）。Typst（0.18 秒）より約 9 倍速い。ただし TeX の組版はしていないので、単純比較はできない。
- **組版の品質は TeX に遠く及ばない。** [rt.pdf](demo/rtex-yingkitw/rt.pdf) では次の問題があった。
  - 用紙が Letter 固定（`geometry` が効かない）。
  - 行内数式 `$...$` が独立したブロックになり、文が途中で切れる。連立方程式（行列）も縦に崩れる。
  - `\textbf` などが表のセル内で展開されない。`\bibliography` が壊れる。
  - 禁則処理・約物の詰めなし。和文の行末で不自然に改行される。
- 用途は、簡単なメモや CI での変換。日本語の論文・教材には向かない。
- 検証は macOS のみ。日本語のグリフをどこから取っているかは未確認（PDF の中身は 1 つの TrueType）。

## 制限

- 検証は macOS のみ。v0.4.0 の表示確認は Poppler と macOS プレビュー。pdf.js は未確認。
- LuaTeX / luatexja と OpenType MATH は未対応（issue #4 より）。
- CJKutf8 の長文で英字・数字・数式が化ける（上の結論を参照）。表示の確認は、テキスト抽出だけでなく、描画した画像でも行うこと（抽出は正しく見える）。
- 丸数字・ローマ数字・丸英字は xeCJK の CJK 判定に含まれず `\setmainfont` 側に回るため、そちらにグリフがないと Missing glyph になる（上の結論を参照）。絵文字はビルドはエラーにならないが、`sbix` 非対応のため PDF には描画されない（同）。ビルドが成功しても表示されない例があるため、ここでも描画した画像での確認が要る。
- 要求した太字・斜体がフォントになければエラーになる（IPAex・BIZ UD 明朝は Bold なし。日本語の `\textit` も不可）。`BoldFont=` は、ファイル名を渡さない形では効かなかった。
- `\setCJKmainfont` に `Path=`/`Extension=`/`FontIndex=` で外部フォントを直接指すとき、システムフォントは fontconfig のようなフォント DB を検索しないため、名前だけでは見つからない。`BoldFont=` に渡す名前も同じ `Path`/`Extension`/`FontIndex` を引き継ぐため、Regular と Bold が同じ `.ttc` の別面にあるフォント（ヒラギノ明朝など）では選べない。単体ファイルに面を抜き出す必要がある（[demo/ratex-v040/hirafonts/](demo/ratex-v040/hirafonts/)）。
- CJKutf8 の禁則処理や約物の詰めは `CJK` パッケージの範囲に限られる。
- v0.3.0 では、幅の情報が和田研フォント用の TFM のため、そこにない文字は出ないことがあった。

## ライセンス・フォント

- IPAex フォントは [IPA フォントライセンス](https://moji.or.jp/ipafont/license/) です。このリポジトリには含めず、`setup.sh` で取得します。
- ヒラギノは Apple 独自のライセンスのフォントです。このリポジトリには含めません。`demo/ratex-v040/hirafonts/` は `.gitignore` で除外しており、上の「2b」の `fontTools` コマンドで手元の macOS から都度抜き出します。BIZ UD はモリサワの [BIZ UDフォント](https://on-d.morisawa.co.jp/biz/) で無償配布されていますが、こちらもリポジトリには含めず、システムにインストールされたものを参照します。
- このリポジトリのスクリプトは MIT ライセンスです（[LICENSE](LICENSE)）。
- ratex は MIT または Apache-2.0 です。
