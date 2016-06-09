set wildignore+=bin,lib,local,include,vendor,*pyc
let g:easytags_file = '.vimtags'
let g:ctrlp_extensions = ['tag']
let g:easytags_dynamic_files = 1
let g:easytags_suppress_report = 1
let g:easytags_opts = ['--sort=no', '--languages=Python', '-h py', '-o .vimtags', '--python-kinds=-i', '--exclude=*/build/*', '--recurse', 'src' ]
