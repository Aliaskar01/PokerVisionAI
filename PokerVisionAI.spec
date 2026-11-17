# Folder distribution: copy the entire dist/PokerVisionAI directory.
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files,collect_dynamic_libs
root = Path(SPECPATH)
a = Analysis([str(root/'main.py')],pathex=[str(root)],
             datas=[(str(root/'assets'),'assets'),(str(root/'models'),'models')]+collect_data_files('rapidocr_onnxruntime'),
             binaries=collect_dynamic_libs('onnxruntime'),
             hiddenimports=['mss.windows','treys'],
             excludes=['torch','torchvision','easyocr','PySide6.QtWebEngineCore','PySide6.QtWebEngineWidgets','PySide6.QtPdf'],
             noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz,a.scripts,[],exclude_binaries=True,name='PokerVisionAI',debug=False,
          bootloader_ignore_signals=False,strip=False,upx=False,console=False)
coll = COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='PokerVisionAI')
