#set page(paper: "a4", margin: 25mm, numbering: "1")
#set text(font: "IPAexMincho", lang: "ja", size: 11pt)
#set par(justify: true, first-line-indent: (amount: 1em, all: false), leading: 0.8em)
#set heading(numbering: "1.1")
#show heading: set text(font: "IPAexGothic")
#show heading.where(level: 1): set block(above: 1.6em, below: 1em)
#set math.equation(numbering: "(1)")
#set list(marker: [•])
#set enum(numbering: "1.")

#align(center)[
  #text(size: 17pt, font: "IPAexGothic")[Rust製TeX「ratex」で日本語PDFを作る]
  #v(0.6em)
  #text(size: 12pt, font: "IPAexGothic")[清水 団]
  #v(0.4em)
  2026年9月19日
]

#align(center)[
  #block(width: 85%)[
    #text(font: "IPAexGothic", weight: "bold")[概要] \
    #set align(left)
    Rust で書かれた TeX エンジン ratex を使い、日本語を含む PDF を生成できるか検証した。
    標準の状態では日本語の字形データが PDF に埋め込まれず、文字化けする。
    本稿では、IPAex フォントをサブフォントに分割して渡し、生成後の PDF を後処理することで、
    主要なビューアで日本語が正しく表示されることを示す。
  ]
]

#outline(title: text(font: "IPAexGothic")[目次], indent: auto)

= はじめに
TeX は数式を美しく組版できるため、論文や教材の作成で広く使われている。
一方で、日本語の文書を作るには、pTeX や LuaTeX-ja など専用のエンジンや大きな配布物（TeX Live）が必要になる。
ratex は、これらを単一のバイナリにまとめた新しい TeX エンジンであり、コンパイルが極めて高速だと報告されている。

本稿の目的は次の三つである。
- ratex で日本語を含む文書をコンパイルできるかを確かめる。
- 表示されない場合の原因を特定する。
- 実用的な回避策を示し、その限界を整理する。

= 検証の方法
== 環境
検証は macOS 上で行った。ratex はソースからビルドし、フォントには IPAex 明朝と IPAex ゴシックを用いた。
文書は `CJKutf8` パッケージで組み、生成した PDF を四種類のビューアで確認した。

== フォントの渡し方
pdfTeX 系のエンジンは 8 ビットのフォントしか扱えないため、六千を超える漢字を含む日本語フォントは、
二百五十六文字ずつのサブフォントに分割して扱う。分割後のフォントは、次の対応で PDF に埋め込まれる。

#figure(
  table(
    columns: 3,
    align: left,
    stroke: none,
    table.hline(),
    [*Unicode の範囲*], [内容], [サブフォント],
    table.hline(),
    [U+3000--30FF], [約物・かな], [udmj30],
    [U+4E00--9FFF], [漢字], [udmj4e--9f],
    [U+FF00--FFEF], [全角形], [udmjff],
    table.hline(),
  ),
  caption: [サブフォントの分割（明朝体）],
  supplement: [表],
)

= 結果
== ビューアごとの表示
何も対策しない場合、フォントは PDF に埋め込まれず、どのビューアでも文字化けする。
フォントを渡しただけの PDF は poppler では表示できたが、macOS のプレビューでは表示できなかった。
これは ratex が TrueType フォントを Type1 として書き出しているためである。

さらに pdf.js では、ひらがなとカタカナは表示されるものの、漢字だけが表示されなかった。
そこで、フォントを Type0 の CIDFontType2 に作り直す後処理を加えたところ、すべてのビューアで正しく表示された。

== ファイルサイズ
IPAex 明朝はおよそ六メガバイトあり、全体を埋め込むと一行の文章でも PDF が大きくなる。
使用した文字だけを取り出すサブセット化を行うことで、サイズは十数キロバイトまで縮んだ。

= 数式との共存
日本語の文章の中でも、数式は ratex 本来の品質で組まれる。たとえば、正規分布の確率密度関数は
$ f(x) = 1 / sqrt(2 pi sigma^2) exp(-(x - mu)^2 / (2 sigma^2)) $ <normal>
と書ける。ここで $mu$ は平均、$sigma^2$ は分散である。また、ガウス積分
$ integral_(-infinity)^infinity e^(-x^2) dif x = sqrt(pi) $
は、式 (1) の正規化に使われる。行列を用いた例として、次の連立方程式を考える。
$ mat(2, 1; 1, 3) vec(x, y) = vec(5, 10). $

= 考察
今回の方法には、次のような限界がある。
+ 生成のたびに、PDF の後処理が必要になる。
+ 禁則処理や約物の詰めは、`CJK` パッケージの範囲に限られる。
+ 和田研フォント用の文字幅表を使うため、そこにない文字は表示できない場合がある。

ratex 自身が TrueType を正しく埋め込み、日本語の組版パッケージに対応すれば、
これらの手間は不要になるはずである。今後の開発に期待したい。

= おわりに
ratex は英語と数式の文書では高速で高品質だが、日本語には現時点で追加の作業が必要である。
それでも、字形データを自分で用意することで、日本語を含む PDF を生成できることを確認した。

#heading(numbering: none, outlined: false)[参考文献]
[1] leoliu0, _ratex: a pure-Rust TeX engine_, GitHub. \
[2] 一般財団法人 文字情報技術促進協議会, _IPAex フォント_.
