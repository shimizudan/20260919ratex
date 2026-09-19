#!/bin/sh
# usage: ./build.sh [doc.tex]   ->  build/<doc>_final.pdf
# ratex でコンパイル → フォントを Type0/CID に作り直してサブセット化
set -eu
cd "$(dirname "$0")"
doc="${1:-long.tex}"; name="${doc%.tex}"
RATEX="${RATEX:-$(cd ../.. && pwd)/src/target/release/ratex}"
mkdir -p build
cp "$doc" udmj.map udgj.map *.enc build/
python3 subset_fonts.py "$doc" build ipaexm.ttf ipaexg.ttf     # ratex を速くするため
( cd build && "$RATEX" "$doc" )
python3 fix_cjk.py "build/$name.pdf" "build/${name}_final.pdf" \
  build/ipaexm.ttf:IPAexMincho build/ipaexg.ttf:IPAexGothic
echo "=> demo/ja-font/build/${name}_final.pdf"
