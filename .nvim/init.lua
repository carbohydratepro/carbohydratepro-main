-- プロジェクト固有のNeovim設定
-- このファイルを読み込むには、exrcを有効にするか、
-- nvim --cmd "set exrc" で起動してください

-- LSP設定 (Pyright - strict mode)
local lspconfig_ok, lspconfig = pcall(require, 'lspconfig')
if lspconfig_ok then
  lspconfig.pyright.setup({
    settings = {
      python = {
        analysis = {
          typeCheckingMode = 'strict',
          diagnosticSeverityOverrides = {
            reportMissingTypeStubs = 'none',
          },
        },
      },
    },
  })

  -- Ruff LSP (Python linter/formatter)
  lspconfig.ruff.setup({
    init_options = {
      settings = {
        configurationPreference = 'filesystemFirst',
      },
    },
  })

  -- Biome LSP (JavaScript/CSS)
  lspconfig.biome.setup({})
end

-- none-ls / null-ls 設定 (djlint, biome, ruff)
local null_ls_ok, null_ls = pcall(require, 'null-ls')
if null_ls_ok then
  null_ls.setup({
    sources = {
      -- Python (Ruff)
      null_ls.builtins.formatting.ruff,
      null_ls.builtins.formatting.ruff_format,
      null_ls.builtins.diagnostics.ruff,

      -- Django HTML
      null_ls.builtins.formatting.djlint,
      null_ls.builtins.diagnostics.djlint,

      -- JavaScript/CSS (Biome)
      null_ls.builtins.formatting.biome,
      null_ls.builtins.diagnostics.biome,
    },
  })
end

-- conform.nvim 設定 (代替フォーマッター)
local conform_ok, conform = pcall(require, 'conform')
if conform_ok then
  conform.setup({
    formatters_by_ft = {
      python = { 'ruff_fix', 'ruff_format' },
      javascript = { 'biome' },
      css = { 'biome' },
      json = { 'biome' },
      html = { 'djlint' },
      htmldjango = { 'djlint' },
    },
    format_on_save = {
      timeout_ms = 500,
      lsp_fallback = true,
    },
  })
end

-- nvim-lint 設定 (代替リンター)
local lint_ok, lint = pcall(require, 'lint')
if lint_ok then
  lint.linters_by_ft = {
    python = { 'ruff' },
    javascript = { 'biome' },
    css = { 'biome' },
    html = { 'djlint' },
    htmldjango = { 'djlint' },
  }

  vim.api.nvim_create_autocmd({ 'BufWritePost', 'BufReadPost' }, {
    callback = function()
      lint.try_lint()
    end,
  })
end

-- 保存時に自動フォーマット
vim.api.nvim_create_autocmd('BufWritePre', {
  pattern = { '*.py', '*.js', '*.css', '*.json', '*.html' },
  callback = function()
    vim.lsp.buf.format({ async = false })
  end,
})
