# Neovim プロジェクト設定

このディレクトリにはプロジェクト固有の Neovim 設定が含まれています。

## 必要なプラグイン

- [nvim-lspconfig](https://github.com/neovim/nvim-lspconfig) - LSP設定
- [none-ls.nvim](https://github.com/nvimtools/none-ls.nvim) または [null-ls.nvim](https://github.com/jose-elias-alvarez/null-ls.nvim) - リンター/フォーマッター統合
- [conform.nvim](https://github.com/stevearc/conform.nvim) - フォーマッター (代替)
- [nvim-lint](https://github.com/mfussenegger/nvim-lint) - リンター (代替)

## 必要な外部ツール

```bash
# Python
pip install pyright ruff

# Django HTML
pip install djlint

# JavaScript/CSS
npm install -g @biomejs/biome
```

## 設定の読み込み方法

### 方法1: exrc を有効にする

`~/.config/nvim/init.lua` に追加:

```lua
vim.o.exrc = true
vim.o.secure = true
```

### 方法2: 手動で読み込む

```lua
-- ~/.config/nvim/init.lua
vim.api.nvim_create_autocmd('DirChanged', {
  callback = function()
    local nvim_config = vim.fn.getcwd() .. '/.nvim/init.lua'
    if vim.fn.filereadable(nvim_config) == 1 then
      dofile(nvim_config)
    end
  end,
})
```

### 方法3: 起動時に指定

```bash
nvim --cmd "luafile .nvim/init.lua"
```
