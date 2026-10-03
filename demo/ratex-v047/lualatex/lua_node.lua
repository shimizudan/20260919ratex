-- lua_node.tex から読み込む node コールバック
local GLYPH = node.id("glyph")
local L, u = string.byte("L"), string.byte("u")

glyph_count = 0

-- 段落中の文字 (glyph) を数え、「Lu」で始まる 3 文字を赤くする
luatexbase.add_to_callback("pre_linebreak_filter", function(head)
  for n in node.traverse_id(GLYPH, head) do
    glyph_count = glyph_count + 1
    if n.char == L and n.next and n.next.id == GLYPH and n.next.char == u then
      local on = node.new("whatsit", "pdf_literal")
      on.data = "1 0 0 rg"
      head = node.insert_before(head, n, on)
      local last = n.next.next or n.next
      local off = node.new("whatsit", "pdf_literal")
      off.data = "0 g"
      head = node.insert_after(head, last, off)
    end
  end
  return head
end, "lua_node_demo")
