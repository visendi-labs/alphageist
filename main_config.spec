# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

import sys ; sys.setrecursionlimit(sys.getrecursionlimit() * 5)

a = Analysis(
    ['/Users/jonathansmac/Python_projects/Alphageist/main.py'],
    pathex=['/Users/jonathansmac/Python_projects/Alphageist'],
    binaries=[],
    datas=[
        ('/Users/jonathansmac/.pyenv/versions/3.11.3/lib/python3.11/site-packages/langchain/chains/llm_summarization_checker/prompts/are_all_true_prompt.txt', 'langchain/chains/llm_summarization_checker/prompts/'), 
        ('/Users/jonathansmac/.pyenv/versions/3.11.3/lib/python3.11/site-packages/langchain/chains/llm_summarization_checker/prompts/check_facts.txt', 'langchain/chains/llm_summarization_checker/prompts/'), 
        ('/Users/jonathansmac/.pyenv/versions/3.11.3/lib/python3.11/site-packages/langchain/chains/llm_summarization_checker/prompts/create_facts.txt', 'langchain/chains/llm_summarization_checker/prompts/'), 
        ('/Users/jonathansmac/.pyenv/versions/3.11.3/lib/python3.11/site-packages/langchain/chains/llm_summarization_checker/prompts/revise_summary.txt', 'langchain/chains/llm_summarization_checker/prompts/'),
        ('/Users/jonathansmac/Python_projects/Alphageist/alphageist/ui/assets/*', 'alphageist/ui/assets')
    ],
    hiddenimports=['tiktoken_ext.openai_public', 'tiktoken_ext'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch','torchvision', 'detectron2'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='Visendi',
          debug=True,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          onefile=True
)