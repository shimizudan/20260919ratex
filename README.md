# ratex で日本語 PDF を作る

Rust 製の TeX エンジン [ratex](https://github.com/leoliu0/ratex) で日本語を含む PDF を生成する検証と、
Typst・通常の TeX とのビルド時間の比較です（macOS）。
v0.3.0 での検証（2026-09-19）、issue [#4](https://github.com/leoliu0/ratex/issues/4) の対応後の v0.4.0 での再検証（2026-09-21）、v0.4.4 での再確認（2026-09-24）、v0.4.7 での LuaLaTeX と文書サンプルの検証（2026-10-03）、v0.5.0 の通常の LaTeX と LuaLaTeX の TeX Live 2026 との比較（2026-10-04）があります。

## v0.5.0 の現状（2026-10-04、TeX Live 2026 と比較）

通常の LaTeX（pdfLaTeX・XeLaTeX）は教材づくりに使える。LuaLaTeX は動くが、LuaTeX-ja・`luacode`・pgfplots が使えないので、日本語の文書にはまだ使えない。

### 通常の LaTeX（pdfLaTeX・XeLaTeX）

| 文書 | 結果 |
|---|---|
| xeCJK の教材（[wallis.tex](demo/ratex-v047/wallis/wallis.tex)。tcolorbox・TikZ・原ノ味） | 通る。初回約 2 秒、編集後約 0.9 秒 |
| B4 横 2 段組の考査問題（[20240922.tex](demo/ratex-v047/typst-port/20240922.tex)。BIZ UDP を `Path=`/`FontIndex=1` で指定） | 通る |
| bxjsarticle の `pdflatex` 版・`xelatex` 版（zr-tex8r さんのサンプル） | 通る（`xelatex` 版は `-xelatex` を付ける。v0.5.0 から） |
| [demo/ratex-v040/](demo/ratex-v040/) などの過去の文書 17 本（CJKutf8、xeCJK + 原ノ味・IPAex・BIZ UD・ヒラギノ） | すべて通る |

以前の制限は次のように変わった（画像でも確認）。

| 項目 | v0.4.4 まで | v0.4.7 | v0.5.0 |
|---|---|---|---|
| IPAex で `\textbf`・`\textit` | エラー | 通る（普通の書体で代わりに出る） | 同じ |
| 丸数字①（`\setmainfont` にグリフがない） | エラー | エラー | ビルドは通るが、①が消える |
| ヒラギノの `.ttc` の太字の面を `BoldFeatures={FontIndex=2}` で選ぶ | エラー | エラー | ビルドは通るが、太字にならない |
| Apple Color Emoji の絵文字 | 描画されない | 同じ | 同じ |

- v0.5.0 で `-xelatex` が本物の XeTeX モードになった。フォントにない文字は「Missing character」の警告を出して飛ばす。**TeX Live 2026 の xelatex も同じ動き**をすることを確かめた。ビルドが通っても文字が消えることがあるので、PDF は目で確かめる。
- 太字のない和文フォント（IPAex・BIZ UD 明朝）は、太字にしても太くならない。太字にはゴシックを `BoldFont=` で割り当てる。
- `-xelatex` などを付けないと、ratex はプリアンブルからエンジンを選ぶが、外れることがある（bxjsarticle の `xelatex` 版は pdfLaTeX が選ばれて止まる）。

### LuaLaTeX（`ratex -lualatex`）

ratex の中には、Rust で書き直した LuaTeX のエンジンがある。LuaTeX 1.24 として振る舞い（`status.luatex_version` = 124）、Lua は 5.3。フォントは同梱の luaotfload（fontloader 2023-12-28 版）で読む。

同じ文書を ratex v0.5.0 と TeX Live 2026 の lualatex でビルドした結果（[compare.sh](demo/ratex-v050/lualatex-compare/compare.sh) で再現できる）:

| 文書 | ratex v0.5.0 | TeX Live 2026 |
|---|---|---|
| `\directlua` と外部の `.lua`（[lua_basic.tex](demo/ratex-v047/lualatex/lua_basic.tex)） | 通る | 通る |
| node コールバック（[lua_node.tex](demo/ratex-v047/lualatex/lua_node.tex)） | 通る | 通る |
| fontspec + IPAex の日本語、Lua で和文の行分割（[lua_ja.tex](demo/ratex-v047/lualatex/lua_ja.tex)） | 通る | 通る |
| `\directlua` の中の空行（[repro_directlua_par.tex](demo/ratex-v047/lualatex/repro_directlua_par.tex)） | 通る（v0.5.0 で修正、#17） | 通る |
| babel のスペイン語（[babel_spanish.tex](demo/ratex-v050/lualatex-compare/babel_spanish.tex)、#17） | 通る（v0.5.0 で修正） | 通る |
| fontspec + 原ノ味ゴシック Medium（[harano_gothic.tex](demo/ratex-v050/lualatex-compare/harano_gothic.tex)） | 通る | 通る |
| **`luacode*` 環境**（[repro_luacode.tex](demo/ratex-v047/lualatex/repro_luacode.tex)） | 失敗（終わりを見つけられない） | 通る |
| **fontspec + 原ノ味明朝**（[repro_harano_lualatex.tex](demo/ratex-v047/lualatex/repro_harano_lualatex.tex)） | 失敗（luaotfload が落ちる） | 通る |
| **LuaTeX-ja**（[ltj_luatexja.tex](demo/ratex-v050/lualatex-compare/ltj_luatexja.tex)） | 失敗（`ltjsarticle.cls` が同梱されていない） | 通る |
| **pgfplots**（[pgfplots_min.tex](demo/ratex-v050/lualatex-compare/pgfplots_min.tex)、[#19](https://github.com/leoliu0/ratex/issues/19)） | 失敗（pgfplots の Lua ファイルの読み込みでエラー） | 通る |

- `luacode` が通らないのは、`\scantextokens` が末尾に空白（改行文字）を足すため。`\scantextokens{abc}` の中身は、ratex では `abc␣`、TeX Live 2026 では `abc` になる。
- **文書ごとの初回は 7〜9 秒かかる。** luaotfload のフォントデータベースを、TeX Live のようにマシンに 1 回ではなく、文書ごとに作るため（作者の説明による）。2 回目以降（1 行編集後の再ビルド）は 0.5〜1 秒で、TeX Live 2026（0.5〜1 秒）と同じくらい。
- 回避策: Lua のコードは別の `.lua` ファイルに書いて `\directlua{dofile(kpse.find_file("x.lua", "lua"))}` で読む。和文フォントは IPAex か原ノ味ゴシックにする。`\directlua` の中に `%` を書かない（TeX のコメントになる。`"\%"` は Lua の不正なエスケープで、TeX Live でも同じ）。

### 使い分け

| 用途 | おすすめ |
|---|---|
| 日本語の教材・プリント | ratex `-xelatex` + xeCJK（速く、TeX Live が要らない） |
| bxjsarticle の文書 | ratex（`pdflatex` 版はそのまま、`xelatex` 版は `-xelatex`） |
| LuaTeX-ja・`luacode`・pgfplots を使う文書 | TeX Live の lualatex |
| pLaTeX・upLaTeX の文書（emath など） | TeX Live（ratex は pTeX に対応していない） |
| Lua で計算や node の処理を試す | ratex `-lualatex` でもよい（Lua は別ファイルに書く） |

## 結論

- **v0.5.0（2026-10-04 確認）では、bxjsarticle の `xelatex` オプション版も通る。** v0.5.0 で `-xelatex` が本物の XeTeX モードになったため（v0.4.7 の `-xelatex` は互換モードで、「Option 'xelatex' used on wrong engine」で止まる）。zr-tex8r さんの XeLaTeX モード用のサンプル [ratex-ja-example-2.tex](demo/ratex-v050/ratex-ja-example-2.tex)（[gist](https://gist.github.com/zr-tex8r/f31d7c8f5a7370099ce81882aca88d43)。v0.4.4 のサンプルのクラスオプションを `xelatex` にした形）が、`ratex -xelatex` で 1 ページの PDF になった（[PDF](demo/ratex-v050/ratex-ja-example-2.pdf)）。和文は原ノ味明朝・ゴシック（`pdflatex` 版は和田研フォント）で、twemojis の絵文字も描画される。`-xelatex` を付けないと pdfLaTeX が選ばれ、bxjsarticle のエラーで止まる。
- **v0.4.7（2026-10-03 確認）では、xeCJK で実用的な教材が作れる。** ウォリス積分の問題と解答（A4 縦 1 ページ。tcolorbox の枠と TikZ のグラフつき、同梱の原ノ味フォント）の [wallis.tex](demo/ratex-v047/wallis/wallis.tex)（[PDF](demo/ratex-v047/wallis/wallis.pdf)）と、Typst で書いた B4 横 2 段組の考査問題を LaTeX に移した [20240922.tex](demo/ratex-v047/typst-port/20240922.tex)（元は [20240922.typ](demo/ratex-v047/typst-port/20240922.typ)。BIZ UDP 明朝・ゴシックを `Path=`/`FontIndex=1` で指定）が、どちらもエラー・警告なしで通った。v0.5.0（本物の XeTeX モードに切り替わった版）でも通る。
- **v0.4.7 では、`ratex -lualatex` で LuaLaTeX の文書がコンパイルできる。** `\directlua`、外部の `.lua` ファイル、node コールバック（`pre_linebreak_filter`）、fontspec（luaotfload）が動く（[demo/ratex-v047/lualatex/](demo/ratex-v047/lualatex/)）。Lua 5.3 で、`status.luatex_version` は 124（LuaTeX 1.24 として振る舞う）。ただし次の制限がある。
  - **`luacode` パッケージが通らない。** v0.4.7 では 2 つの不具合が重なっていた。`\directlua` の中の空行（`\par`）を Lua に渡してしまう不具合（本物の LuaTeX は捨てる。[repro_directlua_par.tex](demo/ratex-v047/lualatex/repro_directlua_par.tex)）は v0.5.0 で直った（issue [#17](https://github.com/leoliu0/ratex/issues/17) の対応）。`\scantextokens` が末尾に改行文字を足す不具合（[repro_scantextokens.tex](demo/ratex-v047/lualatex/repro_scantextokens.tex)）は v0.5.0 でも残っており、`luacode*` 環境は終了マークを見つけられずに失敗する（[repro_luacode.tex](demo/ratex-v047/lualatex/repro_luacode.tex)）。回避策は、Lua のコードを別ファイルに書いて `\directlua{dofile(kpse.find_file("x.lua", "lua"))}` で読むこと。
  - **LuaTeX-ja は同梱されていない**（`luatexja.sty`・`ltjsarticle.cls` が not found）。日本語は fontspec で同梱フォントを選べば出るが、和文の行分割は自分で用意する必要がある。[lua_ja.tex](demo/ratex-v047/lualatex/lua_ja.tex) では、Lua のコールバックで和文の文字間に伸縮する glue を入れ、簡単な禁則処理をした。
  - **同梱の原ノ味明朝を選ぶと luaotfload が落ちる**（`bad argument #1 to 'next'`。[repro_harano_lualatex.tex](demo/ratex-v047/lualatex/repro_harano_lualatex.tex)）。原ノ味ゴシック Medium と IPAex は通る。`-xelatex` では原ノ味明朝も通る。v0.5.0 でも同じ。
  - 上の不具合は、どれも TeX Live 2020・2026 の lualatex では起きない。
  - `-lualatex` のビルドは 1 本 7〜9 秒かかった（初回。2 回目以降は 0.5〜1 秒。上の「v0.5.0 の現状」を参照）。
- **v0.4.4（2026-09-24 確認）では、v0.4.0 の CJKutf8 の化けが直った。** [long_cjkutf8.tex](demo/ratex-v040/long_cjkutf8.tex)（3 ページ、目次・数式・表つき）も [repro_cjkutf8_enum.tex](demo/ratex-v040/repro_cjkutf8_enum.tex) も、英字・数字・数式が正しく出る（出力は [demo/ratex-v044/](demo/ratex-v044/)）。一方、下に書いた v0.4.0 のほかの制限（太字・斜体がないとエラー、同じ `.ttc` の別面を `BoldFont=` で選べない、丸数字が Missing glyph、絵文字フォントが描画されない）は、v0.4.4 でも同じだった。ビルドは v0.4.0 より遅くなった（下の表）。
- **v0.4.4 では、bxjsarticle（`pdflatex,ja=standard`）で日本語 PDF がそのまま作れる。** zr-tex8r さんのサンプル [ratex-ja-example.tex](demo/ratex-v044/ratex-ja-example.tex)（[gist](https://gist.github.com/zr-tex8r/ae14db01f5325ba47c7d6ad41fa58f02)）が、エラー・警告なしで 1 ページの PDF になった（[ratex-ja-example.pdf](demo/ratex-v044/ratex-ja-example.pdf)）。和文は同梱の和田研フォント（明朝・ゴシック）、`cases` と `\dfrac` の数式、`\text{}` 内の和文も正しく出る。**`twemojis` パッケージの絵文字（🙃☃💁）も描画される。** フォントではなく画像として貼るため、下の Apple Color Emoji の問題にはかからない。
- ratex は英語と数式なら、そのままで動く。
- **v0.4.0 では、fontspec + xeCJK で日本語 PDF が後処理なしで作れる。** CJK フォントが同梱され、`fontspec` / `xeCJK` が本物のフォントを選ぶようになった（issue #4 の対応）。`\setCJKmainfont{IPAexMincho}` などで指定したフォントが CID TrueType で埋め込まれる。システムフォントも、フォントファイルの用意も不要。3 ページの長文（数式・表・目次・参考文献つき）も約 0.7 秒で、化けなかった（[demo/ratex-v040/](demo/ratex-v040/)）。
- **v0.4.0 の CJKutf8 は、短い文書なら表示できるが、長文では英字・数字・数式が化ける（v0.4.0 のバグ。v0.4.4 で修正済み）。** 日本語の字形は同梱の和田研フォントで正しく出るが、同じフォント（CMR10 など）に、コードの割り当てが食い違う 2 つの版ができ、英字や数字が欠けたり重なったりする。`enumerate` の番号、ページ番号、目次、式番号などが引き金で、文書の書き方では避けられなかった。最小の再現例は [repro_cjkutf8_enum.tex](demo/ratex-v040/repro_cjkutf8_enum.tex)（6 行）。v0.4.0 の長文で使うなら xeCJK を使う。
- ただし v0.4.4 までの ratex はフォントを代替しない。**要求した太字・斜体がフォントになければエラーになる**（v0.4.6 以降は普通の書体で代わりに出る。上の「v0.5.0 の現状」を参照）。 IPAex には Bold がないため、見出しなどで太字を使う文書は IPAex では通らない（Harano Aji なら通る）。日本語への `\textit` もエラーになる。
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
| ratex v0.4.0（xeCJK、後処理なし） | 0.88 秒 | 0.32 秒 |
| ratex v0.4.0（CJKutf8、後処理なし。※英字・数字・数式が化ける） | 1.06 秒 | 0.38 秒 |
| **ratex v0.4.4（xeCJK、後処理なし）** | 1.40 秒 | 0.48 秒 |
| upLaTeX + dvipdfmx | 1.48 秒 | 0.98 秒 |
| ratex v0.4.4（CJKutf8、後処理なし） | 1.82 秒 | 0.61 秒 |
| XeLaTeX（xeCJK） | 2.27 秒 | 1.13 秒 |
| LuaLaTeX（luatexja） | 6.44 秒 | 2.20 秒 |
| ratex v0.3.0 + 後処理（TTF を事前サブセット） | 1.4 秒 | 0.8 秒 |
| ratex v0.3.0 + 後処理（IPAex 全体の TTF） | 16.3 秒 | 6.0 秒 |

- 各 10 回（v0.3.0 の IPAex 全体のみ 3 回）。生データは [bench_result.json](demo/bench/bench_result.json)。
- v0.4.4 と Typst、TeX 系は 2026-09-24 に同じ環境で測った。v0.4.0 の 2 行は 2026-09-21、v0.3.0 の 2 行は 2026-09-19 の測定値を、古いバイナリがないためそのまま載せている。Typst と TeX 系は 09-21 の測定とほぼ同じ値だったので、環境の差は小さい。
- フォントは同じではない。Typst と TeX 系は IPAex、ratex v0.4 系の xeCJK は Harano Aji（IPAex は Bold がなく、見出しで通らないため）、CJKutf8 は同梱の和田研フォント。
- Typst は英数字にも IPAex を使う。TeX 系は Computer Modern を使うため、組版の細部は同じではない。
- v0.3.0 の測定は、フォントのサブセット化（前処理）を含めていない。v0.4.0・v0.4.4 は前処理も後処理もない。
- ratex v0.4.0 は、TeX 系の中では最も速かった（クリーンで upLaTeX の約 1.4〜1.7 倍、LuaLaTeX の約 6〜7 倍）。Typst には及ばない。
- **v0.4.4 は v0.4.0 より約 1.5〜1.7 倍遅くなった**（xeCJK のクリーンで 0.88 → 1.40 秒、CJKutf8 で 1.06 → 1.82 秒）。xeCJK のクリーンビルドは upLaTeX とほぼ同じ（1.40 秒と 1.48 秒）。再ビルドはまだ upLaTeX の約 2 倍速い。原因は調べていない（v0.4.4 は LuaTeX エンジンなどが入り、バイナリも 445MB から 679MB に増えた）。

### 参考: ヒラギノ・BIZ UD との比較（簡易計測、v0.4.0）

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
  ratex-v044/        v0.4.4 での再確認
    ratex-ja-example.tex  bxjsarticle + twemojis のサンプル（zr-tex8r さんの gist）
    long_cjkutf8.pdf      ../ratex-v040/long_cjkutf8.tex を v0.4.4 でビルドしたもの（化けない）
    repro_cjkutf8_enum.pdf  ../ratex-v040/repro_cjkutf8_enum.tex を v0.4.4 でビルドしたもの（化けない）
  ratex-v047/        v0.4.7 での検証（v0.5.0 で再確認）
    wallis/            ウォリス積分の問題と解答（A4 縦、xeCJK・tcolorbox・TikZ。PDF は v0.5.0 でビルド）
    typst-port/        Typst の考査問題（20240922.typ）を LaTeX に移したもの（B4 横 2 段組、BIZ UDP）
    lualatex/          ratex -lualatex のサンプル
      lua_basic.tex/.lua   \directlua と外部 .lua ファイル（計算、表の生成）
      lua_node.tex/.lua    node コールバック（文字数を数える、文字を赤くする）、fontspec
      lua_ja.tex/.lua      fontspec + IPAex の日本語。Lua で和文の行分割と簡単な禁則
      repro_directlua_par.tex  \directlua の中の空行が Lua に渡る（v0.5.0 で修正済み）
      repro_scantextokens.tex  \scantextokens が末尾に改行文字を足す
      repro_luacode.tex        luacode* 環境が終わらない（上の不具合が原因）
      repro_harano_lualatex.tex  -lualatex で原ノ味明朝を選ぶと luaotfload が落ちる
  ratex-v050/        v0.5.0 での確認
    ratex-ja-example-2.tex  bxjsarticle の xelatex 版のサンプル（zr-tex8r さんの gist。ratex -xelatex でビルド）
    lualatex-compare/  ratex -lualatex と TeX Live の lualatex の比較
      compare.sh         両方でビルドして結果を並べるスクリプト（../../ratex-v047/lualatex/ の .tex も対象）
      ltj_luatexja.tex   LuaTeX-ja + luacode*（ratex には ltjsarticle.cls がない）
      pgfplots_min.tex   pgfplots（issue #19。ratex では失敗）
      babel_spanish.tex  babel のスペイン語（issue #17。v0.5.0 で修正）
      harano_gothic.tex  fontspec + 原ノ味ゴシック Medium（ratex でも通る）
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

Rust 1.89 以上が必要です。フォントを同梱するため、ソースが大きく、ビルドに時間がかかります（v0.4.0 は約 23 分・バイナリ約 445MB、v0.4.4 は約 29 分・約 679MB。Rust 1.98.1）。v0.4.4 の GitHub リリースには Linux 用のバイナリしかないので、macOS ではソースからビルドします。

```sh
git clone https://github.com/leoliu0/ratex.git src
(cd src && git checkout v0.4.4 && cargo build --release)   # v0.4.0 の検証を再現するなら v0.4.0
```

v0.4.5 からは、GitHub のリリースに macOS 用（Apple Silicon・Intel）のビルド済み版（`tex-suite-v0.4.x-macos-aarch64.tar.gz` など）があるので、ソースからビルドしなくてよい。展開した `bin/ratex` をそのまま使うか、PATH の通った場所にリンクする。

```sh
gh release download v0.4.7 -R leoliu0/ratex -p 'tex-suite-v0.4.7-macos-aarch64.tar.gz'
tar xzf tex-suite-v0.4.7-macos-aarch64.tar.gz
./tex-suite-macos-aarch64/bin/ratex --version
```

`ratex -C file.tex` は、キャッシュだけでなく、ratex が作った PDF も消す（コミット済みの PDF でも、手元で ratex がビルドしたものは消える）。キャッシュだけを消すなら `-c` を使う。

### 2. 日本語 PDF を作る（v0.4.0）

```sh
cd demo/ratex-v040
../../src/target/release/ratex xecjk.tex          # fontspec + xeCJK
../../src/target/release/ratex long_xecjk_harano.tex   # 長文（xeCJK）
```

### 2a. bxjsarticle のサンプル（v0.4.4）

```sh
cd demo/ratex-v044
../../src/target/release/ratex ratex-ja-example.tex
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

### 2c. v0.4.7 のサンプル

```sh
cd demo/ratex-v047/wallis     && ratex -xelatex wallis.tex
cd ../typst-port              && ratex -xelatex 20240922.tex   # BIZ UD フォント（/Library/Fonts）が必要
cd ../lualatex                && ratex -lualatex lua_basic.tex # lua_node.tex, lua_ja.tex も同じ
```

### 2d. bxjsarticle の xelatex 版（v0.5.0）

`-xelatex` を付けないと、ratex は pdfLaTeX を選び、bxjsarticle が「Option 'xelatex' used on wrong engine」で止まる。

```sh
cd demo/ratex-v050
ratex -xelatex ratex-ja-example-2.tex
```

### 2e. ratex -lualatex と TeX Live の lualatex を比べる（v0.5.0）

TeX Live（2026 で確認）と ratex が PATH にあること。

```sh
demo/ratex-v050/lualatex-compare/compare.sh
```

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

- 検証は macOS のみ。v0.4.0 の表示確認は Poppler と macOS プレビュー、v0.4.4 は Poppler のみ。pdf.js は未確認。
- v0.4.4 の再確認は、demo/ratex-v040/ の全ファイルの再ビルド（丸数字の再現例以外は成功）、CJKutf8 の 2 例と絵文字の描画確認、IPAex の `\textbf` / `\textit` と `.ttc` の `BoldFeatures={FontIndex=2}` の試行に限る。ヒラギノ・BIZ UD の出力の見た目は v0.4.4 では確認していない。
- ratex の LuaTeX モードは、上の「v0.5.0 の現状」の表の 11 本で試しただけ。OpenType MATH は試していない。比較の相手は TeX Live 2026（MacTeX-2026）の lualatex。
- v0.4.7・v0.5.0 の表示確認は Poppler のみ。v0.5.0 で見た目まで確かめたのは、wallis、ratex-ja-example-2、丸数字・絵文字・IPAex の太字・ヒラギノの太字の例。ほかの過去の文書はビルドが通ることだけ確かめた。
- v0.4.0 では、CJKutf8 の長文で英字・数字・数式が化ける（上の結論を参照。v0.4.4 で修正済み）。表示の確認は、テキスト抽出だけでなく、描画した画像でも行うこと（抽出は正しく見える）。
- 丸数字・ローマ数字・丸英字は xeCJK の CJK 判定に含まれず `\setmainfont` 側に回るため、そちらにグリフがないと Missing glyph になる（上の結論を参照）。v0.5.0 ではエラーにならず、文字が消える。絵文字はビルドはエラーにならないが、`sbix` 非対応のため PDF には描画されない（同）。ビルドが成功しても表示されない例があるため、ここでも描画した画像での確認が要る。
- v0.4.4 までは、要求した太字・斜体がフォントになければエラーになった（IPAex・BIZ UD 明朝は Bold なし。日本語の `\textit` も不可）。v0.4.6 以降はエラーにならず、普通の書体で代わりに出る。`BoldFont=` は、ファイル名を渡さない形では効かなかった。
- `\setCJKmainfont` に `Path=`/`Extension=`/`FontIndex=` で外部フォントを直接指すとき、システムフォントは fontconfig のようなフォント DB を検索しないため、名前だけでは見つからない。`BoldFont=` に渡す名前も同じ `Path`/`Extension`/`FontIndex` を引き継ぐため、Regular と Bold が同じ `.ttc` の別面にあるフォント（ヒラギノ明朝など）では選べない。単体ファイルに面を抜き出す必要がある（[demo/ratex-v040/hirafonts/](demo/ratex-v040/hirafonts/)）。
- CJKutf8 の禁則処理や約物の詰めは `CJK` パッケージの範囲に限られる。
- v0.3.0 では、幅の情報が和田研フォント用の TFM のため、そこにない文字は出ないことがあった。

## ライセンス・フォント

- IPAex フォントは [IPA フォントライセンス](https://moji.or.jp/ipafont/license/) です。このリポジトリには含めず、`setup.sh` で取得します。
- ヒラギノは Apple 独自のライセンスのフォントです。このリポジトリには含めません。`demo/ratex-v040/hirafonts/` は `.gitignore` で除外しており、上の「2b」の `fontTools` コマンドで手元の macOS から都度抜き出します。BIZ UD はモリサワの [BIZ UDフォント](https://on-d.morisawa.co.jp/biz/) で無償配布されていますが、こちらもリポジトリには含めず、システムにインストールされたものを参照します。
- このリポジトリのスクリプトは MIT ライセンスです（[LICENSE](LICENSE)）。
- ratex は MIT または Apache-2.0 です。
- [demo/ratex-v044/ratex-ja-example.tex](demo/ratex-v044/ratex-ja-example.tex) は zr-tex8r さんの [gist](https://gist.github.com/zr-tex8r/ae14db01f5325ba47c7d6ad41fa58f02) のものです。[demo/ratex-v050/ratex-ja-example-2.tex](demo/ratex-v050/ratex-ja-example-2.tex) も zr-tex8r さんの [gist](https://gist.github.com/zr-tex8r/f31d7c8f5a7370099ce81882aca88d43) のものです。どちらも PDF に入る絵文字は [Twemoji](https://github.com/twitter/twemoji)（CC-BY 4.0）です。
