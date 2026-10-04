#!/bin/zsh
# ratex -lualatex と TeX Live の lualatex で、同じ文書をビルドして結果を並べる
#   使い方: ./compare.sh        （ratex と lualatex が PATH にあること）
# 対象は、このフォルダの .tex と ../../ratex-v047/lualatex/ の .tex
setopt nullglob
here=${0:A:h}
v047=$here/../../ratex-v047/lualatex
work=$(mktemp -d)
cache=$work/ratex-cache
now() { perl -MTime::HiRes=time -e 'printf "%.1f", time' }

printf '%-24s | %-40s | %s\n' file "ratex $(ratex --version | awk '{print $2}') -lualatex" "$(lualatex --version | head -1 | sed 's/.*(\(TeX Live [0-9]*\)).*/\1/') lualatex"
for src in $v047/*.tex $here/*.tex; do
  f=${src:t:r}
  for side in r l; do
    mkdir -p $work/$side/$f
    cp $src $work/$side/$f/
    cp $v047/*.lua $work/$side/$f/ 2>/dev/null
  done
  # repro_scantextokens.tex は \show で止まるので、中身をログに書く形にして比べる
  sed -i '' 's/\\show\\x/\\typeout{SCAN=[\\meaning\\x]}/' $work/{r,l}/$f/$f.tex

  a=$(now); (cd $work/r/$f && ratex -lualatex --keep-logs --cache-directory $cache $f.tex > out.txt 2>&1 </dev/null); rc=$?; b=$(now)
  r="exit=$rc $(perl -e "printf '%.1f', $b-$a")s $(grep -m1 -oE '^error: .{0,24}' $work/r/$f/out.txt | sed 's/^error: //')"
  a=$(now); (cd $work/l/$f && lualatex -interaction=nonstopmode $f.tex > out.txt 2>&1 </dev/null); rc=$?; b=$(now)
  l="exit=$rc $(perl -e "printf '%.1f', $b-$a")s $(grep -m1 -oE '^! .{0,24}' $work/l/$f/out.txt)"
  printf '%-24s | %-40s | %s\n' $f "$r" "$l"
done
echo
echo "\\scantextokens{abc} の中身:"
echo "  ratex:    $(grep -h 'SCAN=' $work/r/repro_scantextokens/*.log)"
echo "  lualatex: $(grep -h 'SCAN=' $work/l/repro_scantextokens/*.log)"
rm -rf $work
