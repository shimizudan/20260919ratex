-- LuaTeX-ja なしで和文を行分割させる、ごく簡易な処理
-- 和文の文字と文字の間に、伸縮できる長さ 0 の glue を入れて改行可能にする
local GLYPH = node.id("glyph")
local GLUE  = node.id("glue")

local function is_cjk(c)
  return (c >= 0x3000 and c <= 0x30FF)   -- 句読点・かな
      or (c >= 0x4E00 and c <= 0x9FFF)   -- 漢字
      or (c >= 0xFF00 and c <= 0xFFEF)   -- 全角英数・記号
end

-- 行頭に来てはいけない文字（簡易禁則）
local no_break_before = {}
for _, c in utf8.codes("、。，．）」』！？ーぁぃぅぇぉっゃゅょ") do no_break_before[c] = true end

luatexbase.add_to_callback("pre_linebreak_filter", function(head)
  local n = head
  while n do
    local nx = n.next
    if n.id == GLYPH and nx and nx.id == GLYPH
       and (is_cjk(n.char) or is_cjk(nx.char))
       and not no_break_before[nx.char] then
      local g = node.new(GLUE)
      g.width, g.stretch, g.shrink = 0, tex.sp("0.5pt"), 0
      head = node.insert_after(head, n, g)
    end
    n = nx
  end
  return head
end, "ja_linebreak")
