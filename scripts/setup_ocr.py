"""Explicit one-time optional model download; application never downloads models."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from config import DATA

if __name__ == '__main__':
    import easyocr
    target = DATA/'models'
    target.mkdir(parents=True,exist_ok=True)
    easyocr.Reader(['en','ru'],gpu=False,model_storage_directory=str(target),download_enabled=True)
    print(f'OCR models installed in {target}. Set use_easyocr to true in Detection layout.')
