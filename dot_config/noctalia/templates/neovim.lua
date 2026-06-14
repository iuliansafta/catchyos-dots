local M = {}

function M.setup()
  require("base16-colorscheme").setup({
    -- Background tones
    base00 = "{{colors.surface.default.hex | darken 2}}", -- Default Background
    base01 = "{{colors.surface_container.default.hex}}", -- Lighter Background (status bars)
    base02 = "{{colors.surface_container_high.default.hex}}", -- Selection Background
    base03 = "{{colors.outline.default.hex}}", -- Comments, Invisibles
    -- Foreground tones
    base04 = "{{colors.on_surface_variant.default.hex}}", -- Dark Foreground (status bars)
    base05 = "{{colors.on_surface.default.hex}}", -- Default Foreground
    base06 = "{{colors.on_surface.default.hex}}", -- Light Foreground
    base07 = "{{colors.on_background.default.hex}}", -- Lightest Foreground
    -- Accent colors
    base08 = "{{colors.error.default.hex}}", -- Variables, XML Tags, Errors
    base09 = "{{colors.primary_container.default.hex | invert | darken 5}}", -- Integers, Constants
    base0A = "{{colors.secondary.default.hex}}", -- Classes, Search Background
    base0B = "{{colors.secondary_container.default.hex | invert | darken 5}}", -- Strings, Diff Inserted
    base0C = "{{colors.tertiary_container.default.hex | invert | darken 5}}", -- Regex, Escape Chars
    base0D = "{{colors.tertiary.default.hex}}", -- Functions, Methods
    base0E = "{{colors.primary.default.hex}}", -- Keywords, Storage
    base0F = "{{colors.error_container.default.hex}}", -- Deprecated, Embedded Tags
  })
end

-- Apply transparent backgrounds
local function make_transparent()
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
end

-- Register a signal handler for SIGUSR1 (theme updates)
local signal = vim.uv.new_signal()
signal:start(
  "sigusr1",
  vim.schedule_wrap(function()
    package.loaded["matugen"] = nil
    require("matugen").setup()
    make_transparent()
  end)
)

return M
