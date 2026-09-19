#!/bin/sh
# IPAex フォントを取得し、ratex に渡すサブフォント用の enc / map を生成する。
set -eu
cd "$(dirname "$0")"
if [ ! -f ipaexm.ttf ]; then
  curl -fL -o ipaex.zip https://moji.or.jp/wp-content/ipafont/IPAexfont/IPAexfont00401.zip
  unzip -q -o ipaex.zip -d ipaex
  cp ipaex/IPAexfont00401/ipaexm.ttf ipaex/IPAexfont00401/ipaexg.ttf .
  rm -rf ipaex ipaex.zip
fi
python3 gen_subfonts.py ipaexm.ttf udmj IPAexMincho
python3 gen_subfonts.py ipaexg.ttf udgj IPAexGothic
