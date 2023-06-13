# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

import sys ; sys.setrecursionlimit(sys.getrecursionlimit() * 5)

a = Analysis(
    ['c:\\Projects\\alphageist\\main.py'],
    pathex=['C:\\Projects\\alphageist'],
    binaries=[],
    datas=[
        ('C:\\Projects\\alphageist\\venv\\Lib\\site-packages\\langchain\\chains\\llm_summarization_checker\\prompts\\are_all_true_prompt.txt', 'langchain/chains/llm_summarization_checker/prompts/'), 
        ('C:\\Projects\\alphageist\\venv\\Lib\\site-packages\\langchain\\chains\\llm_summarization_checker\\prompts\\check_facts.txt', 'langchain/chains/llm_summarization_checker/prompts/'), 
        ('C:\\Projects\\alphageist\\venv\\Lib\\site-packages\\langchain\\chains\\llm_summarization_checker\\prompts\\create_facts.txt', 'langchain/chains/llm_summarization_checker/prompts/'), 
        ('C:\\Projects\\alphageist\\venv\\Lib\\site-packages\\langchain\\chains\\llm_summarization_checker\\prompts\\revise_summary.txt', 'langchain/chains/llm_summarization_checker/prompts/'),
        ('C:\\Projects\\alphageist\\alphageist\\ui\\assets\\*', 'alphageist/ui/assets')
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

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Visendi Search',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='exe_assets/Visendi.ico',
    version='0.0.1',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Visendi Search',
)

