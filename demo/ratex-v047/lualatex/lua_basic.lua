-- lua_basic.tex から読み込む関数
function fib(n)
  local a, b = 0, 1
  for _ = 1, n do a, b = b, a + b end
  return a
end

function fib_table(n)
  tex.sprint("\\begin{tabular}{rr}\\hline $n$ & $F_n$ \\\\ \\hline")
  for i = 1, n do
    tex.sprint(string.format("%d & %d \\\\", i, fib(i)))
  end
  tex.sprint("\\hline\\end{tabular}")
end

function sum_squares(n)
  local s = 0
  for k = 1, n do s = s + k * k end
  return s
end

-- TeX 側で "\%" と書くと Lua の不正なエスケープになる（本物の LuaTeX でも同じ）。
-- そこで "%" は Lua 側で付ける：fmt(".10f", x) → string.format("%.10f", x)
function fmt(f, x)
  tex.print(string.format("%" .. f, x))
end
