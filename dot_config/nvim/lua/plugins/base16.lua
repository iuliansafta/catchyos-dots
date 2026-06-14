return {
  "RRethy/base16-nvim",
  config = function()
    require("matugen").setup()

    -- Transparent background so the terminal/wallpaper shows through
    local groups = {
      -- Core
      "Normal", "NormalNC", "NormalFloat", "NormalSB",
      "SignColumn", "SignColumnSB", "FoldColumn",
      "EndOfBuffer", "MsgArea",
      "FloatBorder", "FloatTitle",
      "WinBar", "WinBarNC",
      "VertSplit", "WinSeparator",
      "StatusLine", "StatusLineNC",
      "LineNr", "CursorLine", "CursorLineNr", "CursorColumn",
      "ColorColumn", "Folded", "Conceal",
      "TabLine", "TabLineFill", "TabLineSel",
      "Pmenu", "PmenuMatch",
      "TreesitterContext",
      -- NeoTree
      "NeoTreeNormal", "NeoTreeNormalNC", "NeoTreeEndOfBuffer",
      "NeoTreeWinSeparator", "NeoTreeFloatNormal", "NeoTreeFloatBorder",
      "NeoTreeStatusLine", "NeoTreeStatusLineNC",
      "NeoTreeIndentMarker", "NeoTreeExpander",
      "NeoTreeCursorLine", "NeoTreeTitleBar",
      -- Telescope
      "TelescopeNormal", "TelescopeBorder", "TelescopeResultsTitle",
      -- Trouble / WhichKey
      "TroubleNormal", "WhichKeyNormal",
      -- Diff
      "DiffviewNormal", "DiffviewSignColumn",
    }
    for _, g in ipairs(groups) do
      vim.api.nvim_set_hl(0, g, vim.tbl_extend("force",
        vim.api.nvim_get_hl(0, { name = g }),
        { bg = "NONE", ctermbg = "NONE" }
      ))
    end
  end,
}
