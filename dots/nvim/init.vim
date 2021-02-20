if &compatible
  set nocompatible
endif
" Add the dein installation directory into runtimepath
set runtimepath+=~/.cache/dein/repos/github.com/Shougo/dein.vim

if dein#load_state('~/.cache/dein')
  call dein#begin('~/.cache/dein')

  call dein#add('~/.cache/dein/repos/github.com/Shougo/dein.vim')
  if !has('nvim')
    call dein#add('roxma/nvim-yarp')
    call dein#add('roxma/vim-hug-neovim-rpc')
    call dein#add('Shougo/neco-syntax')
    call dein#add('Shougo/neosnippet')
    call dein#add('Shougo/neosnippet-snippets') 
    call dein#add('Shougo/neomru.vim') 
    call dein#add('Shougo/neoyank.vim') 
    call dein#add('Shougo/denite.nvim')
    call dein#add('Shougo/unite-outline')
    call dein#add('Shougo/defx.nvim')
    call dein#add('ryanoasis/vim-devicons')
    call dein#add('kristijanhusak/defx-icons')
    call dein#add('Yggdroot/LeaderF')
    call dein#add('flazz/vim-colorschemes') 
    call dein#add('itchyny/lightline.vim')
    call dein#add('junegunn/goyo.vim')
    call dein#add('amix/vim-zenroom2')
    call dein#add('bronson/vim-trailing-whitespace')
    call dein#add('majutsushi/tagbar')
    call dein#add('tpope/vim-surround')
    call dein#add('davidhalter/jedi')
    call dein#add('klen/python-mode')
    call dein#add('lervag/vimtex')
    call dein#add('thinca/vim-quickrun')
    call dein#add('lilydjwg/fcitx.vim')
    call dein#add('jiangmiao/auto-pairs')
    call dein#add('tmhedberg/SimpylFold')
  endif

  call dein#end()
  call dein#save_state()
endif

if has('vim_starting') && dein#check_install()
  call dein#install()
endif

if filereadable(expand('~/.vimrc.local'))
  source ~/.vimrc.local
endif

filetype plugin indent on
syntax enable

colorscheme OceanicNext " northpole " adaryn " inkpot " 
highlight Normal ctermbg=none
highlight NonText ctermbg=none
highlight LineNr ctermbg=none
highlight Folded ctermbg=none
highlight EndOfBuffer ctermbg=none 
let g:lightline = {
        \ 'colorscheme': 'solarized',
        \ 'mode_map': {'c': 'NORMAL'},
        \ 'active': {
        \   'left': [ [ 'mode', 'paste' ], [ 'fugitive', 'filename' ] ]
        \ },
        \ 'component_function': {
        \   'modified': 'LightlineModified',
        \   'readonly': 'LightlineReadonly',
        \   'fugitive': 'LightlineFugitive',
        \   'filename': 'LightlineFilename',
        \   'fileformat': 'LightlineFileformat',
        \   'filetype': 'LightlineFiletype',
        \   'fileencoding': 'LightlineFileencoding',
        \   'mode': 'LightlineMode'
        \ }
        \ }

function! LightlineModified()
  return &ft =~ 'help\|vimfiler\|gundo' ? '' : &modified ? '+' : &modifiable ? '' : '-'
endfunction

function! LightlineReadonly()
  return &ft !~? 'help\|vimfiler\|gundo' && &readonly ? 'x' : ''
endfunction

function! LightlineFilename()
  return ('' != LightlineReadonly() ? LightlineReadonly() . ' ' : '') .
        \ (&ft == 'vimfiler' ? vimfiler#get_status_string() :
        \  &ft == 'unite' ? unite#get_status_string() :
        \  &ft == 'vimshell' ? vimshell#get_status_string() :
        \ '' != expand('%:p') ? expand('%:p') : '[No Name]') .
        \ ('' != LightlineModified() ? ' ' . LightlineModified() : '')
endfunction

function! LightlineFugitive()
  if &ft !~? 'vimfiler\|gundo' && exists('*fugitive#head')
    return fugitive#head()
  else
    return ''
  endif
endfunction

function! LightlineFileformat()
  return winwidth(0) > 70 ? &fileformat : ''
endfunction

function! LightlineFiletype()
  return winwidth(0) > 70 ? (&filetype !=# '' ? &filetype : 'no ft') : ''
endfunction

function! LightlineFileencoding()
  return winwidth(0) > 70 ? (&fenc !=# '' ? &fenc : &enc) : ''
endfunction

function! LightlineMode()
  return winwidth(0) > 60 ? lightline#mode() : ''
endfunction

let file_name = expand('%')
if has('vim_starting') &&  file_name == ''
  autocmd VimEnter * Defx -columns=indent:icons:filename:type | call clearmatches()
endif

set shell=/usr/bin/zsh
set number                                  " show line numbers
set ttyfast                                 " terminal acceleration
set rulerformat=%-14.(%l,%c%V%)\ %P
set ruler

set tabstop=4                               " 4 whitespaces for tabs visual presentation
set shiftwidth=4                            " shift lines by 4 spaces
set smarttab                                " set tabs for a shifttabs logic
set expandtab                               " expand tabs into spaces
set autoindent                              " indent when moving to the next line while writing code
set guicursor=
set autochdir

set cursorline                              " shows line under the cursor's line
set showmatch                               " shows matching part of bracket pairs (), [], {}

" set list
" set listchars=tab:»-,trail:-,extends:»,precedes:«,nbsp:%,eol:↲

" j, k による移動を折り返されたテキストでも自然に振る舞うように変更
nnoremap j gj
nnoremap k gk

" vを二回で行末まで選択
vnoremap v $h

" TABにて対応ペアにジャンプ
nnoremap <Tab> %
vnoremap <Tab> %

" Ctrl + hjkl でウィンドウ間を移動
nnoremap <C-h> <C-w>h
nnoremap <C-j> <C-w>j
nnoremap <C-k> <C-w>k
nnoremap <C-l> <C-w>l
nnoremap <C-Left> <C-w>h
nnoremap <C-Down> <C-w>j
nnoremap <C-Up> <C-w>k
nnoremap <C-Right> <C-w>l

set enc=utf-8                             " utf-8 by default
set encoding=utf-8
set t_Co=256 
set foldmethod=indent
set foldlevel=99

set nobackup                                " no backup files
set nowritebackup                           " only in case you don't want a backup file while editing
set noswapfile                              " no swap files

set backspace=indent,eol,start              " backspace removes all (indents, EOLs, start) What is start?

set scrolloff=20                            " let 10 lines before/after cursor during scroll

set clipboard=unnamed                       " use system clipboard

set exrc                                    " enable usage of additional .vimrc files from working directory
set secure                                  " prohibit .vimrc files to execute shell, create files, etc...

set wildmenu
set wildmode=full
set mouse=a
set title
set wrapscan
set guicursor=

inoremap jj <Esc>
nnoremap <S-Left>  <C-w><<CR>
nnoremap <S-Right> <C-w>><CR>
nnoremap <S-Up>    <C-w>-<CR>
nnoremap <S-Down>  <C-w>+<CR>
nnoremap <F4> :set relativenumber!<CR>

tab sball
set switchbuf=useopen
set laststatus=2
nnoremap <F9> :bprev<CR>
nnoremap <F10> :bnext<CR>
nnoremap <silent> <leader>q :SyntasticCheck # <CR> :bp <BAR> bd #<CR>

nnoremap <silent> <F11> :Goyo 170<CR>
nnoremap <silent> <F12> :Goyo!<CR>
 
" .doc .pdf .rtf file open settings
  " Read-only .doc through antiword
  autocmd BufReadPre *.doc silent set ro
  autocmd BufReadPost *.doc silent %!antiword "%"

  " Read-only odt/odp through odt2txt
  autocmd BufReadPre *.odt,*.odp silent set ro
  autocmd BufReadPost *.odt,*.odp silent %!odt2txt "%"

  " Read-only pdf through pdftotext
  autocmd BufReadPre *.pdf silent set ro
  autocmd BufReadPost *.pdf silent %!pdftotext -nopgbrk -layout -q -eol unix "%" - | fmt -w78

  " Read-only rtf through unrtf
  autocmd BufReadPre *.rtf silent set ro
  autocmd BufReadPost *.rtf silent %!unrtf --text

" tagbar settings
  let g:tagbar_autofocus=0
  let g:tagbar_width=42
  nnoremap <F8> :TagbarToggle<CR>
  " autocmd BufEnter *.py :call tagbar#autoopen(0)
  " autocmd BufWinLeave *.py :TagbarClose

" pymode settings
  " python executables for different plugins
  let g:pymode_python='python3'

  " rope
  let g:pymode_rope=0
  let g:pymode_rope_completion=0
  let g:pymode_rope_complete_on_dot=0
  let g:pymode_rope_auto_project=0
  let g:pymode_rope_enable_autoimport=0
  let g:pymode_rope_autoimport_generate=0
  let g:pymode_rope_guess_project=0

  " documentation
  let g:pymode_doc=0
  let g:pymode_doc_bind='K'

  " lints
  let g:pymode_lint=0

  " virtualenv
  let g:pymode_virtualenv=1

  " breakpoints
  let g:pymode_breakpoint=1
  let g:pymode_breakpoint_key='<leader>b'

  " syntax highlight
  let g:pymode_syntax=1
  let g:pymode_syntax_slow_nvsync=1
  let g:pymode_syntax_all=1
  let g:pymode_syntax_print_as_function=g:pymode_syntax_all
  let g:pymode_syntax_highlight_async_await=g:pymode_syntax_all
  let g:pymode_syntax_highlight_equal_operator=g:pymode_syntax_all
  let g:pymode_syntax_highlight_stars_operator=g:pymode_syntax_all
  let g:pymode_syntax_highlight_self=g:pymode_syntax_all
  let g:pymode_syntax_indent_errors=g:pymode_syntax_all
  let g:pymode_syntax_string_formatting=g:pymode_syntax_all
  let g:pymode_syntax_space_errors=g:pymode_syntax_all
  let g:pymode_syntax_string_format=g:pymode_syntax_all
  let g:pymode_syntax_string_templates=g:pymode_syntax_all
  let g:pymode_syntax_doctests=g:pymode_syntax_all
  let g:pymode_syntax_builtin_objs=g:pymode_syntax_all
  let g:pymode_syntax_builtin_types=g:pymode_syntax_all
  let g:pymode_syntax_highlight_exceptions=g:pymode_syntax_all
  let g:pymode_syntax_docstrings=g:pymode_syntax_all

  " highlight 'long' lines (>= 80 symbols) in python files
  augroup vimrc_autocmds
      autocmd!
      autocmd FileType python,rst,c,cpp highlight Excess ctermbg=DarkGrey guibg=Black
      autocmd FileType python,rst,c,cpp match Excess /\%81v.*/
      autocmd FileType python,rst,c,cpp set nowrap
      autocmd FileType python,rst,c,cpp set colorcolumn=80
  augroup END

  " code folding
  let g:pymode_folding=0

  " pep8 indents
  let g:pymode_indent=1

  " code running
  " let g:pymode_run=1
  " let g:pymode_run_bind='<F5>'

  let g:ale_sign_column_always = 0
  let g:ale_emit_conflict_warnings = 0                                                                      
  let g:pymode_rope_lookup_project = 0

  " imap <F5> <Esc>:w<CR>:!clear;python %<CR>

" Latex settings
  let g:quickrun_config = {
    \   'tex': {
    \       'command': 'latexmk',
    \       'exec': ['%c -gg -pdfdvi %s', 'mupdf %s:r.pdf']
    \   },
    \}
  filetype plugin on
  let g:tex_flavor = 'latexmk'
  let g:latex_latexmk_options = '-pdf'
  let g:vimtex_compiler_progname = 'nvr'
  let g:vimtex_view_method='mupdf'

" neosnippet setiings
  imap <C-k> <Plug>(neosnippet_expand_or_jump)
  smap <C-k> <Plug>(neosnippet_expand_or_jump)
  xmap <C-k> <Plug>(neosnippet_expand_target)
  if has('conceal')
    set conceallevel=0 concealcursor=niv
  endif

" map <F7> : !g++ % && ./a.out <CR>
" map <F6> : !python3 % <CR>

set splitright
set splitbelow

autocmd Filetype c,cpp nnoremap <buffer> <F5> :update<Bar>execute '!g++ % && ./a.out' <CR>
autocmd Filetype python nnoremap <buffer> <F5> :update<Bar>execute '!python3 %'<CR>

autocmd Filetype c,cpp nnoremap <silent> <C-b> :update<Bar>:let $CURR_PATH=expand('%:p:h')<CR>:let $CURR_FILE=expand('%:t')<CR>:let $CURR_PREFIX=expand('%:t:r')<CR>:belowright split<Bar>:te cd $CURR_PATH && g++ $CURR_FILE -o ./$CURR_PREFIX.o && ./$CURR_PREFIX.o<CR>

autocmd Filetype c,cpp nnoremap <silent> <C-b><C-b> :update<Bar>:let $CURR_PATH=expand('%:p:h')<CR>:let $CURR_FILE=expand('%:t')<CR>:let $CURR_PREFIX=expand('%:t:r')<CR>:belowright split<Bar>:te cd $CURR_PATH && g++ $CURR_FILE -o ./$CURR_PREFIX.o -lgsl -lgslcblas -lm && ./$CURR_PREFIX.o<CR>

autocmd Filetype python nnoremap <buffer> <C-b> :update<Bar>:let $CURR_PATH=expand('%:p:h')<CR>:let $CURR_FILE=expand('%:t')<CR>:belowright split<Bar>:te cd $CURR_PATH && python $CURR_FILE<CR>

autocmd Filetype pdf nnoremap <buffer> <C-b> <Esc>:!mupdf "%"<CR>

nnoremap <silent> <leader>p <Esc>:!mupdf "%"<CR><CR>
nnoremap <silent> <leader>] <Esc>:let $CURR_PATH=expand('%:p:h')<CR>:belowright split<Bar>:te<CR>i cd $CURR_PATH<CR>
nnoremap <C-s> <Esc>:w<CR>
nnoremap <C-w> <Esc>:q<CR>

let g:vim_run_command_map = {
  \'javascript': 'node',
  \'php': 'php',
  \'python': 'python',
  \}


" For en-keyboard layout
" nnoremap ; :
" nnoremap : ;

" denite settings
nnoremap <silent> <space>fr :<C-u>Denite file_mru<CR>
nnoremap <silent> <space>fb :<C-u>Denite buffer<CR>
nnoremap <silent> <space>fy :<C-u>Denite neoyank<CR>
nnoremap <silent> <space>ff :<C-u>Denite file_rec<CR>
nnoremap <silent> <space>fu :<C-u>Denite outline<CR>
nnoremap <silent> <space>fg :<C-u>DeniteBufferDir grep<CR>

" search word under cursor, the pattern is treated as regex, and enter normal mode directly
noremap <leader>f :<C-U><C-R>=printf("Leaderf! rg -e %s ", expand("<cword>"))<CR>
" search word under cursor, the pattern is treated as regex,
" append the result to previous search results.
noremap <leader>g :<C-U><C-R>=printf("Leaderf! rg --append -e %s ", expand("<cword>"))<CR>
" search word under cursor literally only in current buffer
noremap <leader>b :<C-U><C-R>=printf("Leaderf! rg -F --current-buffer -e %s ", expand("<cword>"))<CR>
" search visually selected text literally, don't quit LeaderF after accepting an entry
xnoremap gf :<C-U><C-R>=printf("Leaderf! rg -F --stayOpen -e %s ", leaderf#Rg#visual())<CR>
" recall last search. If the result window is closed, reopen it.
noremap go :<C-U>Leaderf! rg --stayOpen --recall<CR>

noremap <leader>bb :<C-u>OpenBookmark 
nnoremap <silent><Leader>v :<C-u>vs<CR>
nnoremap <silent><Leader>h :<C-u>sp<CR>
nnoremap <silent><Leader>w :<C-u>sp<CR>
nnoremap <silent><Leader>w :<C-u>:q<CR>

autocmd FileType defx call s:defx_my_settings()
    function! s:defx_my_settings() abort
     " Define mappings
      nnoremap <silent><buffer><expr> <Right>
     \ defx#async_action('open')
      nnoremap <silent><buffer><expr> <CR>
     \ defx#async_action('open', 'vsplit')
      nnoremap <silent><buffer><expr> cc
     \ defx#do_action('copy')
      nnoremap <silent><buffer><expr> mm
     \ defx#do_action('move')
      nnoremap <silent><buffer><expr> vv
     \ defx#do_action('paste')
      nnoremap <silent><buffer><expr> l
     \ defx#async_action('open')
      nnoremap <silent><buffer><expr> v
     \ defx#async_action('open', 'vsplit')
      nnoremap <silent><buffer><expr> p
     \ defx#async__action('open', 'pedit')
      nnoremap <silent><buffer><expr> mk
     \ defx#do_action('new_directory')
      nnoremap <silent><buffer><expr> cf
     \ defx#do_action('new_file')
      nnoremap <silent><buffer><expr> DD
     \ defx#do_action('remove')
     nnoremap <silent><buffer><expr> dd
     \ defx#do_action('remove_trash')
      nnoremap <silent><buffer><expr> rr
     \ defx#do_action('rename')
      nnoremap <silent><buffer><expr> xx
     \ defx#do_action('execute_system')
      nnoremap <silent><buffer><expr> yy
     \ defx#do_action('yank_path')
      nnoremap <silent><buffer><expr> .
     \ defx#do_action('toggle_ignored_files')
      nnoremap <silent><buffer><expr> <Left>
     \ defx#async_action('cd', ['..'])
      nnoremap <silent><buffer><expr> h
     \ defx#async_action('cd', ['..'])
      nnoremap <silent><buffer><expr> <leader><leader>
     \ defx#async_action('open')
      nnoremap <silent><buffer><expr> ~
     \ defx#async_action('cd')
      nnoremap <silent><buffer><expr> q
     \ defx#do_action('quit')
      nnoremap <silent><buffer><expr> <Space>
     \ defx#do_action('toggle_select') . 'j'
      nnoremap <silent><buffer><expr> *
     \ defx#do_action('toggle_select_all')
      nnoremap <silent><buffer><expr> j
     \ line('.') == line('$') ? 'gg' : 'j'
      nnoremap <silent><buffer><expr> k
     \ line('.') == 1 ? 'G' : 'k'
      nnoremap <silent><buffer><expr> <C-l>
     \ defx#do_action('redraw')
      nnoremap <silent><buffer><expr> <C-g>
     \ defx#do_action('print')
      nnoremap <silent><buffer><expr> cd
     \ defx#do_action('change_vim_cwd')
      nnoremap <silent><buffer><expr> dr
     \ defx#do_action('drop')
    endfunction
" nnoremap <silent> <leader><leader> :<C-u>Defx -columns=indent:icons:filename:type -listed -resume -buffer-name=tab`tabpagenr()`<CR>:call clearmatches()<CR>
nnoremap <silent> <leader><leader> :<C-u>Defx -columns=indent:icons:filename:type `expand('%:p:h')` -search=`expand('%:p')`<CR>:call clearmatches()<CR>

call defx#custom#option('_', {
      \ 'winwidth': 30,
      \ 'direction': 'botright',
      \ 'show_ignored_files': 0,
      \ 'buffer_name': '',
      \ 'toggle': 1,
      \ 'resume': 1
      \ })
call defx#custom#column('mark', {
        \ 'readonly_icon': '✗',
        \ 'selected_icon': '✓',
        \ })
call defx#custom#column('icon', {
        \ 'directory_icon': '▸',
        \ 'opened_icon': '▾',
        \ 'root_icon': ' ',
        \ })

" Defx Icons
  let g:defx_icons_enable_syntax_highlight = 0
  let g:defx_icons_column_length = 1
  let g:defx_icons_directory_icon = ''
  let g:defx_icons_mark_icon = '*'
  let g:defx_icons_parent_icon = ''
  let g:defx_icons_default_icon = ''
  let g:defx_icons_directory_symlink_icon = ''
  " Options below are applicable only when using "tree" feature
  let g:defx_icons_root_opened_tree_icon = ''
  let g:defx_icons_nested_opened_tree_icon = ''
  let g:defx_icons_nested_closed_tree_icon = ''

" Traillingwhite settings
nnoremap <silent><leader>tr :<C-u>:FixWhitespace<CR>
