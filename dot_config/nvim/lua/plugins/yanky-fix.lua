-- Silence "Nothing is copied" from wl-paste when the Wayland clipboard is empty.
-- Yanky calls wl-paste on FocusGained to sync the clipboard ring, and if nothing
-- has been copied yet the provider returns that error string as register content.
return {
  "gbprod/yanky.nvim",
  opts = function(_, opts)
    vim.api.nvim_create_autocmd("FocusGained", {
      group = vim.api.nvim_create_augroup("YankyClipboardGuard", { clear = true }),
      callback = function()
        -- Silently read the clipboard register; if wl-paste exits non-zero
        -- (empty clipboard), clear the register so yanky doesn't see the
        -- error message as content.
        local reg = vim.o.clipboard:find("unnamedplus") and "+" or "*"
        local content = vim.fn.getreg(reg)
        if content == "Nothing is copied\n" or content == "Nothing is copied" then
          vim.fn.setreg(reg, "")
        end
      end,
      -- Run before yanky's own FocusGained handler
      nested = false,
    })
    return opts
  end,
}
